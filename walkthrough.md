# Field Service Management Copilot Walkthrough

We have successfully built and verified the **Field Service Management Copilot** project under `/Users/dilip.rajkumar/Documents/Github/field-service-copilot`. The codebase is structured, fully functional, dynamic, and styled as a premium operations control tower.

---

## 1. What Was Built

The project has a modular layout with clear separation of concerns:

- **State Database (`app/db.py`)**: Manages the local JSON-based store (`app/data/db.json`), automatically seeds 10 technicians and 20 jobs centered in San Francisco, and dynamically computes KPI cards (Pending Approvals, Delayed Jobs, Active Field Techs).
- **ADK Tool Implementations (`app/tools.py`)**: Implements `get_dashboard_state`, `unassign_job_self` (direct execute), `request_reassignment` (pending approval gate), `approve_reassignment_request`, and `reject_reassignment_request` with strict role-based permission assertions.
- **Agent Definitions (`app/agent.py`)**: Declares the ADK agent using `gemini-3.1-flash-lite`, bound tools, custom system instructions, and a `before_agent_callback` to seed default role values in session state.
- **REST Backend & Web Server (`app/fast_api_app.py`)**: Implements custom endpoints (`/api/state`, `/api/chat`, `/api/approve_direct`, `/api/reject_direct`) and mounts the static web folder to serve the dashboard.
- **Visual Fronted Control Room (`app/static/`)**:
  - `index.html`: Header, metrics ribbons, list sidebars, canvas vector map, and chat client layout.
  - `style.css`: A custom slate-dark theme with glassmorphic cards, color-coded badges, glowing elements, and responsive layout grids.
  - `app.js`: Connects lists to the REST API, draws San Francisco territories and job pins on canvas, and drives chat submissions and direct approval review queues.

---

## 2. Verification Testing & Validation Results

We performed automated quality checks and agentic smoke tests directly on the codebase:

### Code Quality & Lints
- **Command**: `agents-cli lint`
- **Result**: Checked code quality, formatted files, and ran type checking with Ty. All checks passed successfully.

### Smoke Test: Dashboard Metrics Query
- **Command**: `agents-cli run "Show dashboard summary metrics"`
- **Result**: The agent initialized successfully and resolved database parameters dynamically:
  ```
  *   **Total Jobs:** 20
  *   **Assigned Jobs:** 8
  *   **Unassigned Jobs:** 12
  *   **In Progress Jobs:** 0
  *   **Completed Jobs:** 0
  *   **Delayed Jobs:** 1
  *   **Active Technicians:** 8
  *   **Pending Approvals:** 0
  ```

### Smoke Test: Technician Self-Unassignment (Direct Flow)
- **Command**: `agents-cli run "I can't complete Job job_1 because the site is inaccessible."`
- **Result**: The agent parsed the intent, extracted parameters, ran the tool, updated the database, and logged the event:
  ```
  [tool_call: unassign_job_self({"job_id": "job_1", "reason": "site inaccessible"})]
  [tool_response: unassign_job_self -> {"status": "success", "message": "Successfully unassigned Job 'job_1' from your schedule.", "job_id": "job_1", "reason": "site inaccessible"}]
  I have successfully unassigned you from job_1 because the site is inaccessible. Your schedule has been updated.
  ```

### Smoke Test: Role-Based Ownership Validation (Security check)
- **Command**: `agents-cli run "Move Job job_3 from me to Technician tech_4 because I'm delayed."` (called under default `tech_1` context)
- **Result**: The agent checked job ownership and blocked the unassigned transfer:
  ```
  According to our records, job_3 is currently assigned to tech_3 (Charlie Davis), not yourself (tech_1). Additionally, as a technician, you are only able to request reassignments for jobs currently assigned to you.
  ```

---

## 3. How to Run and Preview the Visual Control Tower

Follow these simple steps to run and view the visual dashboard locally:

1. **Verify your environment**:
   Ensure you have a `.env` file containing your API Key (already added to `.gitignore`):
   ```env
   GEMINI_API_KEY=your-api-key-here
   ```

2. **Navigate to the project and run**:
   ```bash
   cd /Users/dilip.rajkumar/Documents/Github/field-service-copilot
   uv run python -m app.fast_api_app
   ```

3. **Open in browser**:
   Navigate to **[http://localhost:8000](http://localhost:8000)** to view the live dashboard.

4. **Interactive Demo Scenarios**:
   - Toggle **Role Switcher** between *Technician* and *Dispatch Manager*.
   - Use the **Suggested Prompts** to test self-unassignment and reassignment requests.
   - Watch the **San Francisco Canvas Map** update in real-time as jobs change states or reassignments get approved!
