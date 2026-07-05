# ruff: noqa
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

import os
import google.auth
from dotenv import load_dotenv
from google.adk.agents import Agent
from google.adk.apps import App
from google.adk.models import Gemini
from google.genai import types
from google.adk.agents.callback_context import CallbackContext

# Load env variables from .env
load_dotenv()

# Check for API key (AI Studio mode) vs Vertex AI mode
api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")

if api_key:
    # Use AI Studio
    os.environ["GOOGLE_GENAI_USE_VERTEXAI"] = "False"
    os.environ["GOOGLE_API_KEY"] = api_key
else:
    # Use Vertex AI (Agent Runtime / Reasoning Engine)
    os.environ["GOOGLE_GENAI_USE_VERTEXAI"] = "True"
    project_id = os.environ.get("GOOGLE_CLOUD_PROJECT")
    if not project_id:
        try:
            _, project_id = google.auth.default()
            os.environ["GOOGLE_CLOUD_PROJECT"] = project_id
        except Exception:
            project_id = "dilip-rajkumar-personal"
            os.environ["GOOGLE_CLOUD_PROJECT"] = project_id
    os.environ["GOOGLE_CLOUD_LOCATION"] = "global"

# Import our custom field service copilot tools
from app.tools import (
    get_dashboard_state,
    unassign_job_self,
    request_reassignment,
    approve_reassignment_request,
    reject_reassignment_request,
)

# Callback to initialize state variables before agent runs
async def before_agent(callback_context: CallbackContext) -> None:
    if "user:role" not in callback_context.state:
        callback_context.state["user:role"] = "Technician"
    if "user:technician_id" not in callback_context.state:
        callback_context.state["user:technician_id"] = "tech_1"

# System instruction for the Copilot with dynamic state interpolations
INSTRUCTION = """
You are the Field Service Management Copilot, a production-style assistant managing technician schedules, job reassignments, and dispatch approvals.

Current context:
- User Role: {user:role}
- Current Technician ID: {user:technician_id}

Role-based Rules & Actions:
1. If User Role is "Technician":
   - You can unassign a job from yourself via `unassign_job_self` tool. This requires a valid reason (e.g. "traffic delay", "site inaccessible", "not certified").
   - You can request job reassignment to another technician via `request_reassignment` tool. This creates a PENDING approval request. You MUST NOT reassign the job directly.
   - If the technician wants to unassign, verify they own the job.
   - If the technician wants to move/transfer/reassign a job, call `request_reassignment`.
   - You CANNOT approve or reject requests.

2. If User Role is "Dispatch Manager":
   - You can approve a pending request via `approve_reassignment_request`.
   - You can reject a pending request via `reject_reassignment_request`.
   - You CANNOT unassign jobs or create technician reassignment requests.

General guidelines:
- If you don't know the current state or need to review jobs/technicians/requests, call the `get_dashboard_state` tool.
- When an action is successful, return a brief, professional response highlighting key IDs (e.g., job ID, request ID) and confirming the update.
- If an action is blocked due to unauthorized permissions or validation issues, explain why clearly.
"""

root_agent = Agent(
    name="field_service_copilot",
    model=Gemini(
        model="gemini-3.1-flash-lite",  # Latest Gemini Flash Lite model
        retry_options=types.HttpRetryOptions(attempts=3),
    ),
    instruction=INSTRUCTION,
    tools=[
        get_dashboard_state,
        unassign_job_self,
        request_reassignment,
        approve_reassignment_request,
        reject_reassignment_request,
    ],
    before_agent_callback=before_agent,
)

app = App(
    root_agent=root_agent,
    name="app",
)
