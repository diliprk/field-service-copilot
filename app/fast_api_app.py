# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import contextlib
import os
from collections.abc import AsyncIterator

from a2a.server.tasks import InMemoryTaskStore
from dotenv import load_dotenv
from fastapi import FastAPI, Header
from fastapi.staticfiles import StaticFiles
from google.adk.cli.fast_api import get_fast_api_app
from google.adk.runners import Runner
from google.genai import types
from pydantic import BaseModel

from app.app_utils import services
from app.app_utils.a2a import attach_a2a_routes
from app.app_utils.reasoning_engine_adapter import (
    attach_reasoning_engine_routes,
)
from app.app_utils.telemetry import (
    setup_agent_engine_telemetry,
    setup_telemetry,
)
from app.app_utils.typing import Feedback
from app.db import get_kpis, load_db, reset_db
from app.tools import approve_reassignment_request, reject_reassignment_request

load_dotenv()
setup_telemetry()
# Must run before get_fast_api_app to set the tracer provider resource.
setup_agent_engine_telemetry()

import logging
local_logger = logging.getLogger("fast_api_app")

# Robust logger fallback
try:
    from google.cloud import logging as google_cloud_logging

    logging_client = google_cloud_logging.Client()
    logger = logging_client.logger(__name__)
except Exception:
    import logging

    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)

allow_origins = (
    os.getenv("ALLOW_ORIGINS", "").split(",") if os.getenv("ALLOW_ORIGINS") else None
)

AGENT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


@contextlib.asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    # Runner for the A2A path, sharing the same session/artifact services as the
    # adk_api and reasoning_engine paths (see services.py). Imported here so the
    # agent is built after env/telemetry setup.
    from app.agent import app as adk_app
    from app.agent import root_agent

    runner = Runner(
        app=adk_app,
        session_service=services.get_session_service(),
        artifact_service=services.get_artifact_service(),
        auto_create_session=True,
    )
    # Shared by the A2A path and the reasoning_engine adapter routes.
    app.state.runner = runner
    app.state.agent_app_name = adk_app.name
    await attach_a2a_routes(
        app,
        agent=root_agent,
        runner=runner,
        task_store=InMemoryTaskStore(),
        rpc_path=f"/a2a/{adk_app.name}",
    )
    # Mount static files folder to serve the visual control tower dashboard (index.html)
    # This must be mounted after dynamic routes are attached so that it acts as a fallback handler.
    static_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")
    if os.path.exists(static_dir):
        app.mount("/", StaticFiles(directory=static_dir, html=True), name="static")
    yield


app: FastAPI = get_fast_api_app(
    agents_dir=AGENT_DIR,
    web=False,
    artifact_service_uri=services.ARTIFACT_SERVICE_URI,
    allow_origins=allow_origins,
    session_service_uri=services.SESSION_SERVICE_URI,
    otel_to_cloud=False,
    lifespan=lifespan,
)
app.title = "field-service-copilot"
app.description = "API for interacting with the Agent field-service-copilot"


# Proxy routes so the Vertex AI Console Playground (reasoning_engine SDK) can
# talk to this agent alongside the native adk_api routes.
attach_reasoning_engine_routes(app)


# Pydantic Schemas for Custom Endpoints
class ChatRequest(BaseModel):
    message: str
    role: str
    technician_id: str
    session_id: str
    user_id: str


class DirectApprovalRequest(BaseModel):
    request_id: str
    manager_comments: str = ""


# Custom API Endpoints
@app.get("/api/state")
def get_state_endpoint() -> dict:
    """Returns the current state database of jobs, techs, approvals, and dynamic KPIs."""
    data = load_db()
    kpis = get_kpis(data)
    return {
        "kpis": kpis,
        "territories": data["territories"],
        "technicians": data["technicians"],
        "jobs": data["jobs"],
        "approval_requests": data["approval_requests"],
        "activity_log": data["activity_log"][-20:],  # Return last 20 activities
    }


@app.post("/api/reset")
def reset_endpoint() -> dict:
    """Resets the state database to default synthetic demo data."""
    data = reset_db()
    kpis = get_kpis(data)
    return {
        "kpis": kpis,
        "territories": data["territories"],
        "technicians": data["technicians"],
        "jobs": data["jobs"],
        "approval_requests": data["approval_requests"],
        "activity_log": data["activity_log"][-20:],
    }


@app.post("/api/approve_direct")
def approve_direct_endpoint(req: DirectApprovalRequest) -> dict:
    """REST API to directly approve a reassignment request from the Dispatch UI."""
    # Enforces Dispatch Manager role by default for direct button actions
    return approve_reassignment_request(
        request_id=req.request_id, manager_comments=req.manager_comments
    )


@app.post("/api/reject_direct")
def reject_direct_endpoint(req: DirectApprovalRequest) -> dict:
    """REST API to directly reject a reassignment request from the Dispatch UI."""
    return reject_reassignment_request(
        request_id=req.request_id, manager_comments=req.manager_comments
    )


@app.post("/api/chat")
async def chat_endpoint(
    req: ChatRequest,
    x_gemini_api_key: str | None = Header(default=None)
) -> dict:
    """Passes user messages to the ADK Copilot runner, injecting user role and tech ID in context."""
    runner = app.state.runner
    session_service = runner.session_service

    custom_key_used = False
    old_use_vertexai = os.environ.get("GOOGLE_GENAI_USE_VERTEXAI")
    old_use_enterprise = os.environ.get("GOOGLE_GENAI_USE_ENTERPRISE")
    old_google_api_key = os.environ.get("GOOGLE_API_KEY")
    old_gemini_api_key = os.environ.get("GEMINI_API_KEY")
    original_models = {}

    if x_gemini_api_key:
        os.environ["GOOGLE_GENAI_USE_VERTEXAI"] = "False"
        os.environ["GOOGLE_GENAI_USE_ENTERPRISE"] = "False"
        os.environ["GOOGLE_API_KEY"] = x_gemini_api_key
        os.environ["GEMINI_API_KEY"] = x_gemini_api_key
        custom_key_used = True
        
        # Recursively clear cached clients and adjust model names on the agent hierarchy
        def prepare_agents_for_custom_key(agent):
            if hasattr(agent, "model") and agent.model:
                for prop in ["api_client", "_api_backend", "_live_api_client"]:
                    if prop in agent.model.__dict__:
                        del agent.model.__dict__[prop]
                model_name = agent.model.model
                if model_name and model_name.startswith("projects/") and "models/" in model_name:
                    base_model = model_name.split("models/")[-1]
                    original_models[id(agent)] = model_name
                    agent.model.model = base_model
            if hasattr(agent, "sub_agents") and agent.sub_agents:
                for sub_agent in agent.sub_agents:
                    prepare_agents_for_custom_key(sub_agent)

        prepare_agents_for_custom_key(runner.app.root_agent)

    try:
        # Ensure session is initialized
        session = await session_service.get_session(
            app_name=runner.app_name, user_id=req.user_id, session_id=req.session_id
        )
        if session is None:
            session = await session_service.create_session(
                app_name=runner.app_name, user_id=req.user_id, session_id=req.session_id
            )
        response_text = ""
        async for event in runner.run_async(
            user_id=req.user_id,
            session_id=req.session_id,
            new_message=types.Content(
                role="user", parts=[types.Part.from_text(text=req.message)]
            ),
            state_delta={
                "user:role": req.role,
                "user:technician_id": req.technician_id,
            },
        ):
            if event.content and event.content.parts:
                for part in event.content.parts:
                    if part.text:
                        response_text += part.text

        return {"response": response_text}

    except Exception as e:
        err_msg = str(e)
        local_logger.error(f"Error executing agent runner: {err_msg}", exc_info=True)
        
        # Check if the exception looks like an API Key error
        is_api_key_error = False
        if "api key" in err_msg.lower() or "api_key" in err_msg.lower() or "unauthorized" in err_msg.lower() or "invalid_argument" in err_msg.lower() or "apikey" in err_msg.lower() or "not found" in err_msg.lower() or "404" in err_msg.lower():
            is_api_key_error = True
        
        if is_api_key_error:
            return {
                "error": "API_KEY_INVALID",
                "message": "The Gemini API Key is invalid or not working. Please input a valid API Key."
            }
        
        return {
            "error": "CHAT_ERROR",
            "message": f"Error running agent: {err_msg}"
        }

    finally:
        # Restore original environment variables if overridden
        if custom_key_used:
            if old_use_vertexai is not None:
                os.environ["GOOGLE_GENAI_USE_VERTEXAI"] = old_use_vertexai
            else:
                os.environ.pop("GOOGLE_GENAI_USE_VERTEXAI", None)
                
            if old_use_enterprise is not None:
                os.environ["GOOGLE_GENAI_USE_ENTERPRISE"] = old_use_enterprise
            else:
                os.environ.pop("GOOGLE_GENAI_USE_ENTERPRISE", None)
                
            if old_google_api_key is not None:
                os.environ["GOOGLE_API_KEY"] = old_google_api_key
            else:
                os.environ.pop("GOOGLE_API_KEY", None)
                
            if old_gemini_api_key is not None:
                os.environ["GEMINI_API_KEY"] = old_gemini_api_key
            else:
                os.environ.pop("GEMINI_API_KEY", None)
                
            # Restore model names and clear cached clients again so they're restored to default on next call
            def restore_agents(agent):
                if hasattr(agent, "model") and agent.model:
                    if id(agent) in original_models:
                        agent.model.model = original_models[id(agent)]
                    for prop in ["api_client", "_api_backend", "_live_api_client"]:
                        if prop in agent.model.__dict__:
                            del agent.model.__dict__[prop]
                if hasattr(agent, "sub_agents") and agent.sub_agents:
                    for sub_agent in agent.sub_agents:
                        restore_agents(sub_agent)

            restore_agents(runner.app.root_agent)


@app.post("/feedback")
def collect_feedback(feedback: Feedback) -> dict[str, str]:
    """Collect and log feedback."""
    try:
        logger.log_struct(feedback.model_dump(), severity="INFO")
    except Exception:
        pass
    return {"status": "success"}





# Main execution
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
