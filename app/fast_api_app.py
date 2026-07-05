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
from fastapi import FastAPI
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
async def chat_endpoint(req: ChatRequest) -> dict:
    """Passes user messages to the ADK Copilot runner, injecting user role and tech ID in context."""
    runner = app.state.runner
    session_service = runner.session_service

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
