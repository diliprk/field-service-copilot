# Video Demo Transcript: Field Service Management Copilot

**Target Length**: ~3 Minutes  
**Demonstrator**: Product Owner / Developer  
**Roles Shown**: Field Technician & Dispatch Manager  

---

## 📋 Prompt Reference Sheet (By Environment)

### 🖥️ Custom Frontend UI (localhost:8000)
*   **Technician Mode (Alice Vance context):**
    *   `"I can't complete Job job_1 because the site is inaccessible."` (Triggers `unassign_job_self` tool; map pin turns amber)
*   **Technician Mode (Evan Wright context):**
    *   `"Please reassign Job job_5 to Alice Vance."` (Triggers `request_reassignment` tool; adds req to manager queue)
*   **Dispatch Manager Mode:**
    *   Direct interactive click on the green **Approve** button for `req_1` in the manager approvals panel.

### 🛠️ ADK Playground (localhost:8080 or CLI)
*   **Role & Tools Verification (Under the Hood):**
    *   `"Show the status of Alice Vance and her current jobs."` (Runs `get_dashboard_state` tool to retrieve current SF database state)
    *   `"I can't complete Job job_3 because the site is inaccessible."` (Checks security validation — blocked because Alice doesn't own charlie's job)
    *   `"Approve reassignment request req_1 with comments: Approved for dispatch."` (Runs `approve_reassignment_request` tool in manager context)

---

## 🎬 Section 1: Intro & Theme Toggle (0:00 - 0:40)

**[0:00 - 0:20 Screen: Split-screen view. One side focuses on the custom Frontend UI rendered in Light Theme, showing the Leaflet map centered on San Francisco. Tech list and Job list visible.]**

*   **Action**: Point to the clean Light Mode design, the map header **AEROCORE FIELD SERVICE COPILOT**, and the KPI cards. Click the theme toggle icon in the header to switch to Dark Mode, showing the glassmorphic layout shifting and the Leaflet map tiles swapping to CartoDB Dark Matter, then click it again to return to Light Mode.
*   **Speech**: 
    > *"Hello everyone! Today I’m showcasing my Field Service Management Copilot built using the Google ADK and FastAPI. In field operations, technician schedules change instantly. I’ve built an operations control tower centered in San Francisco that matches live technician workloads with an interactive, intelligent agent. Clicking this theme toggle switches my glassmorphic layout and map tiles instantly between light and dark modes."*

**[0:20 - 0:40 Screen: Switch focus to the ADK Playground web interface running on localhost:8080 showing the workflow graph and the custom tools.]**

*   **Action**: Show the interactive graph, highlight the custom tools (`unassign_job_self`, `request_reassignment`, `approve_reassignment_request`), and point to the prompts made in the playground.
*   **Speech**: 
    > *"Before diving into the live dashboard, here is the under-the-hood view in the ADK Playground. This graph defines my agent's structure, showing how it routes conversations to custom tools like unassignment, reassignment requests, and manager approvals. Now, let’s go back to the custom dashboard for the detailed demo."*

---

## 🏗️ Section 2: Technician Mode & Self-Unassignment (0:40 - 1:25)

**[Screen: Simulated Tech 'Alice Vance' is selected on the custom UI dashboard. Active tab is Technicians. A split-screen or overlay shows a terminal running the FastAPI backend logs.]**

*   **Action**: Select the chat input and click the suggested chip: *"I can't complete Job job_1 because the site is inaccessible."* Highlight the terminal window as it streams the ADK agent's reasoning process and the execution of the `unassign_job_self` tool call.
*   **Speech**: 
    > *"Let’s start in Technician Mode, simulating Alice Vance. Alice is currently assigned to Job 1. She encounters a site issue and tells the Copilot about it. When she submits this, notice the terminal on the right: the ADK agent dynamically parses the request, prints its model reasoning steps, calls my custom `unassign_job_self` tool, and returns the response. Instantly, the map pin for Job 1 turns amber on the dashboard, showing a real-time unassignment."*

---

## 🔁 Section 3: Reassignment Requests (1:25 - 2:10)

**[Screen: Switch simulated technician dropdown in the left sidebar from 'Alice Vance' to 'Evan Wright'. Chat box is clear. Terminal overlay is active.]**

*   **Action**: Select **Evan Wright** as the simulated technician. Click the suggested chip or type: *"Please reassign Job job_5 to Alice Vance."* Point to the terminal logs showing the ADK agent evaluating the technician's role permissions, verifying that Evan owns `job_5`, and executing the `request_reassignment` tool call.
*   **Speech**: 
    > *"Now, let's switch our simulated technician to Evan Wright, who is assigned to Job 5. Evan wants to transfer Job 5 to Alice Vance. As a technician, he doesn't have permissions to make direct modifications to other routes. So, in the terminal, you can see the ADK agent verifying Evan's ownership of Job 5. It confirms he owns the job, and instead of applying the assignment directly, it calls my `request_reassignment` tool. This registers a pending request `req_1` and drops it into the Dispatch Manager approvals queue in the dashboard. The job remains assigned to Evan until a manager approves."*

---

## 👮 Section 4: Manager Approvals (2:10 - 2:40)

**[Screen: Header role selector. Click 'Dispatch Manager'.]**

*   **Action**: Click 'Dispatch Manager'. Note the change in context. Click the green **Approve** button on the pending approval card for `req_1` in the sidebar. In the modal, type *"Approved for Bob"* and click **Approve Request**.
*   **Speech**: 
    > *"Now I toggle the simulating role to Dispatch Manager. The right panel immediately loads the pending approval cards. Clicking 'Approve' triggers my direct modal review. I’ll add a comment, click 'Approve Request', and the backend updates the state database. On the map, the route line shifts from Evan to Alice, and the timeline log records the audit detail."*

---

## 🎯 Section 5: Outro (2:40 - 2:55)

**[Screen: Zoom back out to the full dashboard grid.]**

*   **Action**: Show the KPI numbers.
*   **Speech**: 
    > *"By wrapping role-aware ADK tools around a structured local state engine and an interactive Leaflet map, I’ve created an operational copilot that is secure, visually interactive, and incredibly easy to use. Thanks for watching!"*
