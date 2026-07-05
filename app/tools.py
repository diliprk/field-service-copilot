from datetime import datetime

from google.adk.tools import ToolContext

from app.db import get_kpis, load_db, log_activity, save_db


def get_dashboard_state(tool_context: ToolContext) -> dict:
    """Gets the current status of the field service operations dashboard, including
    technicians, jobs, pending approvals, dynamic KPIs, and the activity log.

    Returns:
        dict: The full state of the dashboard database and summary metrics.
    """
    data = load_db()
    kpis = get_kpis(data)
    return {
        "status": "success",
        "kpis": kpis,
        "territories": data["territories"],
        "technicians": data["technicians"],
        "jobs": data["jobs"],
        "approval_requests": data["approval_requests"],
        "activity_log": data["activity_log"][-20:],  # Return last 20 activities
    }


def unassign_job_self(job_id: str, reason: str, tool_context: ToolContext) -> dict:
    """Removes a job assignment directly from the calling technician's schedule.
    This action is executed immediately and does not require manager approval,
    but a valid justification/reason must be provided.

    Args:
        job_id: The ID of the job to unassign (e.g., 'job_1').
        reason: The reason for the unassignment (e.g., 'site inaccessible', 'delayed').

    Returns:
        dict: Status message and description of the action taken.
    """
    user_role = tool_context.state.get("user:role", "Technician")
    user_tech_id = tool_context.state.get("user:technician_id", "tech_1")

    if user_role != "Technician":
        return {
            "status": "error",
            "message": f"Permission denied. Role '{user_role}' cannot perform technician self-unassignment.",
        }

    if not reason or len(reason.strip()) < 5:
        return {
            "status": "error",
            "message": "A valid explanation/reason is required to unassign a job.",
        }

    data = load_db()

    # Find job
    job = next((j for j in data["jobs"] if j["id"] == job_id), None)
    if not job:
        return {"status": "error", "message": f"Job '{job_id}' not found."}

    # Validate assignment
    if job["assigned_technician_id"] != user_tech_id:
        return {
            "status": "error",
            "message": f"Unauthorized. You cannot unassign job '{job_id}' because it is assigned to technician '{job['assigned_technician_id']}', not you ({user_tech_id}).",
        }

    # Perform unassignment
    job["assigned_technician_id"] = None
    job["status"] = "Unassigned"

    # Update technician schedule
    tech = next((t for t in data["technicians"] if t["id"] == user_tech_id), None)
    if tech and job_id in tech["assigned_job_ids"]:
        tech["assigned_job_ids"].remove(job_id)

    save_db(data)

    tech_name = tech["name"] if tech else user_tech_id
    log_activity(
        user=tech_name,
        action="Self-Unassignment",
        details=f"Unassigned job {job_id} from {tech_name}. Reason: {reason}",
    )

    return {
        "status": "success",
        "message": f"Successfully unassigned Job '{job_id}' from your schedule.",
        "job_id": job_id,
        "reason": reason,
    }


def request_reassignment(
    job_id: str, target_tech_id: str, reason: str, tool_context: ToolContext
) -> dict:
    """Proposes transferring a job assignment to another technician.
    This creates a pending approval request that must be reviewed by the Dispatch Manager.
    It does not execute the change directly.

    Args:
        job_id: The ID of the job to reassign (e.g., 'job_1').
        target_tech_id: The ID of the technician to assign the job to (e.g., 'tech_2').
        reason: The reason for the reassignment (e.g., 'running late', 'missing required equipment').

    Returns:
        dict: Details of the created approval request.
    """
    user_role = tool_context.state.get("user:role", "Technician")
    user_tech_id = tool_context.state.get("user:technician_id", "tech_1")

    if user_role != "Technician":
        return {
            "status": "error",
            "message": f"Permission denied. Role '{user_role}' cannot request reassignments.",
        }

    if not reason or len(reason.strip()) < 5:
        return {
            "status": "error",
            "message": "A valid reason is required to request job reassignment.",
        }

    data = load_db()

    # Find job
    job = next((j for j in data["jobs"] if j["id"] == job_id), None)
    if not job:
        return {"status": "error", "message": f"Job '{job_id}' not found."}

    # Validate assignment ownership
    if job["assigned_technician_id"] != user_tech_id:
        return {
            "status": "error",
            "message": f"Unauthorized. You cannot reassign job '{job_id}' because it is assigned to technician '{job['assigned_technician_id']}', not you ({user_tech_id}).",
        }

    # Validate target tech exists
    target_tech = next(
        (t for t in data["technicians"] if t["id"] == target_tech_id), None
    )
    if not target_tech:
        return {
            "status": "error",
            "message": f"Target technician '{target_tech_id}' not found.",
        }

    if target_tech["role"] == "Dispatch Manager":
        return {
            "status": "error",
            "message": "Cannot reassign a job to a Dispatch Manager.",
        }

    # Create approval request
    req_id = f"req_{len(data['approval_requests']) + 1}"
    new_request = {
        "request_id": req_id,
        "requester_id": user_tech_id,
        "source_technician_id": user_tech_id,
        "target_technician_id": target_tech_id,
        "job_id": job_id,
        "reason": reason,
        "status": "Pending",
        "manager_comments": "",
        "timestamp": datetime.now().isoformat(),
    }

    data["approval_requests"].append(new_request)
    save_db(data)

    tech = next((t for t in data["technicians"] if t["id"] == user_tech_id), None)
    tech_name = tech["name"] if tech else user_tech_id
    target_name = target_tech["name"]

    log_activity(
        user=tech_name,
        action="Reassignment Requested",
        details=f"Requested transfer of job {job_id} from {tech_name} to {target_name}. Reason: {reason}",
    )

    return {
        "status": "success",
        "message": f"Reassignment request '{req_id}' for Job '{job_id}' created successfully and is pending Dispatch Manager approval.",
        "request_id": req_id,
        "job_id": job_id,
        "source_technician": tech_name,
        "target_technician": target_name,
        "request_status": "Pending",
    }


def approve_reassignment_request(
    request_id: str, manager_comments: str = "", tool_context: ToolContext | None = None
) -> dict:
    """Approves a pending job reassignment request and updates the technician schedules.
    Only available to the Dispatch Manager.

    Args:
        request_id: The ID of the pending approval request (e.g., 'req_1').
        manager_comments: Optional notes/comments from the manager.

    Returns:
        dict: Status message indicating success or error.
    """
    # If called from REST directly, tool_context might be None, or we read from state
    user_role = "Dispatch Manager"
    if tool_context:
        user_role = tool_context.state.get("user:role", "Technician")

    if user_role != "Dispatch Manager":
        return {
            "status": "error",
            "message": "Permission denied. Only a Dispatch Manager can approve reassignment requests.",
        }

    data = load_db()

    # Find request
    req = next(
        (r for r in data["approval_requests"] if r["request_id"] == request_id), None
    )
    if not req:
        return {
            "status": "error",
            "message": f"Reassignment request '{request_id}' not found.",
        }

    if req["status"] != "Pending":
        return {
            "status": "error",
            "message": f"Request '{request_id}' is already {req['status']}.",
        }

    job_id = req["job_id"]
    source_id = req["source_technician_id"]
    target_id = req["target_technician_id"]

    # Validate job and target tech
    job = next((j for j in data["jobs"] if j["id"] == job_id), None)
    target_tech = next((t for t in data["technicians"] if t["id"] == target_id), None)
    source_tech = next((t for t in data["technicians"] if t["id"] == source_id), None)

    if not job:
        return {
            "status": "error",
            "message": f"Job '{job_id}' associated with this request was not found.",
        }
    if not target_tech:
        return {
            "status": "error",
            "message": f"Target technician '{target_id}' was not found.",
        }

    # Execute reassignment
    job["assigned_technician_id"] = target_id
    job["status"] = "Assigned"

    # Update schedules
    if source_tech and job_id in source_tech["assigned_job_ids"]:
        source_tech["assigned_job_ids"].remove(job_id)
    if target_tech and job_id not in target_tech["assigned_job_ids"]:
        target_tech["assigned_job_ids"].append(job_id)

    # Approve request
    req["status"] = "Approved"
    req["manager_comments"] = manager_comments or "Approved by Dispatch Manager."

    save_db(data)

    source_name = source_tech["name"] if source_tech else source_id
    target_name = target_tech["name"] if target_tech else target_id

    log_activity(
        user="Dispatch Manager",
        action="Request Approved",
        details=f"Approved reassignment of Job {job_id} from {source_name} to {target_name}. Comments: {req['manager_comments']}",
    )

    return {
        "status": "success",
        "message": f"Successfully approved request '{request_id}'. Job '{job_id}' has been reassigned to {target_name}.",
        "request_id": request_id,
        "job_id": job_id,
        "target_technician": target_name,
        "request_status": "Approved",
    }


def reject_reassignment_request(
    request_id: str, manager_comments: str = "", tool_context: ToolContext | None = None
) -> dict:
    """Rejects a pending job reassignment request.
    Only available to the Dispatch Manager.

    Args:
        request_id: The ID of the pending approval request (e.g., 'req_1').
        manager_comments: Optional notes/comments explaining why the request was rejected.

    Returns:
        dict: Status message indicating success or error.
    """
    user_role = "Dispatch Manager"
    if tool_context:
        user_role = tool_context.state.get("user:role", "Technician")

    if user_role != "Dispatch Manager":
        return {
            "status": "error",
            "message": "Permission denied. Only a Dispatch Manager can reject reassignment requests.",
        }

    data = load_db()

    # Find request
    req = next(
        (r for r in data["approval_requests"] if r["request_id"] == request_id), None
    )
    if not req:
        return {
            "status": "error",
            "message": f"Reassignment request '{request_id}' not found.",
        }

    if req["status"] != "Pending":
        return {
            "status": "error",
            "message": f"Request '{request_id}' is already {req['status']}.",
        }

    job_id = req["job_id"]
    source_id = req["source_technician_id"]
    target_id = req["target_technician_id"]

    source_tech = next((t for t in data["technicians"] if t["id"] == source_id), None)
    target_tech = next((t for t in data["technicians"] if t["id"] == target_id), None)

    # Reject request
    req["status"] = "Rejected"
    req["manager_comments"] = manager_comments or "Rejected by Dispatch Manager."

    save_db(data)

    source_name = source_tech["name"] if source_tech else source_id
    target_name = target_tech["name"] if target_tech else target_id

    log_activity(
        user="Dispatch Manager",
        action="Request Rejected",
        details=f"Rejected reassignment of Job {job_id} from {source_name} to {target_name}. Comments: {req['manager_comments']}",
    )

    return {
        "status": "success",
        "message": f"Rejected request '{request_id}' successfully. Job '{job_id}' remains assigned to {source_name}.",
        "request_id": request_id,
        "job_id": job_id,
        "request_status": "Rejected",
    }
