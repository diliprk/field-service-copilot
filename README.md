# Field Service Management Copilot

A production-style operational dashboard and agentic copilot powered by the **Google ADK (Agent Development Kit)** and **FastAPI**, designed to support natural-language job reassignments, unassignments, and exception handling.

---

## 🛠️ Project Architecture

```
field-service-copilot/
├── app/
│   ├── data/
│   │   └── db.json            # Seed database (SF coordinates, jobs, techs)
│   ├── static/                # Visual Control Tower assets
│   │   ├── index.html         # Live dashboard layout
│   │   ├── style.css          # Theme styles (Dark/Light glassmorphism)
│   │   └── app.js             # Leaflet maps & chat controller
│   ├── agent.py               # Google ADK Agent (gemini-3.1-flash-lite)
│   ├── db.py                  # State database engine & KPI calculator
│   ├── tools.py               # Custom role-aware ADK tools
│   └── fast_api_app.py        # Unified FastAPI backend & static server
├── architecture_note.md       # Full design note
├── pyproject.toml             # Python dependencies
└── README.md                  # This file
```

---

## 🚀 Quick Start

### 1. Prerequisites
- **Python 3.11+**
- **uv** package manager installed (`curl -LsSf https://astral.sh/uv/install.sh | sh`)
- **Google AI Studio API Key** in a `.env` file:
  ```env
  GEMINI_API_KEY=AIzaSy...
  ```

### 2. Install Dependencies
Run the installation command in the project root:
```bash
uv sync
```

### 3. Start the Server
Run the FastAPI web application:
```bash
uv run python -m app.fast_api_app
```
*(The server will start running at **`http://localhost:8000`**)*

---

## 🗺️ Visual Control Tower Features

*   **Interactive Map (Leaflet.js)**: Displays real San Francisco coordinates for service jobs and technician centers with custom marker styles (glowing status rings and pulsing badges).
*   **Theme Switcher**: Toggle between **Dark Mode** and **Light Mode** instantly in the header. The Leaflet map tiles will swap from CartoDB Dark Matter to Positron Positron.
*   **Role-Based Simulators**: Select either **Field Technician** or **Dispatch Manager** to test permissions.
*   **Real-Time Audit Trail**: View execution logs in the bottom-right feed as jobs change status or reassignments get requested/approved.

---

## 💬 Interactive Prompt Scenarios

Toggle the simulating role in the top header and type the following prompts in the chat box:

### 1. Technician Mode (Simulating Alice Vance / Bob Miller)
*   **Self-Unassignment**:
    *   *“I can't complete Job job_1 because the site is inaccessible.”*
    *   *(Alice Vance owns job_1, so it unassigns immediately and updates the map pin to Amber/Unassigned).*
*   **Reassignment Request**:
    *   *“Move Job job_1 to Bob Miller (tech_2) because I don't have the right tools.”*
    *   *(Creates a **Pending Approval** request in the manager's queue).*
*   **Ownership Check**:
    *   *“I can't do Job job_3 because I'm stuck in traffic.”*
    *   *(The agent will block the request because job_3 belongs to Charlie Davis, not Alice).*

### 2. Dispatch Manager Mode (Dave Miller)
*   **Approve Request**:
    *   *“Approve reassignment request req_1 with comments: Approved for dispatch.”*
    *   *(Swaps job assignment to the target technician, moves job back to Assigned, and logs the action).*
*   **Reject Request**:
    *   *“Reject request req_1 because Bob is already overbooked.”*
*   **Operations Status**:
    *   *“Show the status of Alice Vance and her current jobs.”*
