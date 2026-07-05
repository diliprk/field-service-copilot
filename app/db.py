import json
import os
from datetime import datetime

DATABASE_FILE = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "data", "db.json"
)

INITIAL_DATA = {
    "territories": {
        "North": {
            "name": "North (Marina/Presidio)",
            "color": "#4f46e5",
            "center": [37.798, -122.445],
        },
        "East": {
            "name": "East (Downtown/SoMa)",
            "color": "#8b5cf6",
            "center": [37.785, -122.405],
        },
        "South": {
            "name": "South (Mission/Noe)",
            "color": "#10b981",
            "center": [37.755, -122.420],
        },
        "West": {
            "name": "West (Sunset/Richmond)",
            "color": "#f59e0b",
            "center": [37.770, -122.480],
        },
        "Central": {
            "name": "Central (Twin Peaks/Castro)",
            "color": "#ec4899",
            "center": [37.760, -122.440],
        },
    },
    "technicians": [
        {
            "id": "tech_1",
            "name": "Alice Vance",
            "role": "Technician",
            "territory": "North",
            "skills": ["hvac", "safety"],
            "availability": "Available",
            "assigned_job_ids": ["job_1"],
        },
        {
            "id": "tech_2",
            "name": "Bob Miller",
            "role": "Technician",
            "territory": "West",
            "skills": ["plumbing", "cabling"],
            "availability": "On Job",
            "assigned_job_ids": ["job_2"],
        },
        {
            "id": "tech_3",
            "name": "Charlie Davis",
            "role": "Technician",
            "territory": "Central",
            "skills": ["electrical", "safety"],
            "availability": "Available",
            "assigned_job_ids": ["job_3"],
        },
        {
            "id": "tech_4",
            "name": "Diana Prince",
            "role": "Technician",
            "territory": "South",
            "skills": ["cabling", "hvac"],
            "availability": "Delayed",
            "assigned_job_ids": ["job_4"],
        },
        {
            "id": "tech_5",
            "name": "Evan Wright",
            "role": "Technician",
            "territory": "East",
            "skills": ["electrical", "plumbing"],
            "availability": "Available",
            "assigned_job_ids": ["job_5"],
        },
        {
            "id": "tech_6",
            "name": "Fiona Gallagher",
            "role": "Technician",
            "territory": "North",
            "skills": ["safety", "electrical"],
            "availability": "On Job",
            "assigned_job_ids": ["job_6"],
        },
        {
            "id": "tech_7",
            "name": "George Cooper",
            "role": "Technician",
            "territory": "West",
            "skills": ["hvac", "plumbing"],
            "availability": "Available",
            "assigned_job_ids": ["job_7"],
        },
        {
            "id": "tech_8",
            "name": "Hannah Abbott",
            "role": "Technician",
            "territory": "South",
            "skills": ["plumbing", "electrical"],
            "availability": "Available",
            "assigned_job_ids": ["job_8"],
        },
        {
            "id": "tech_9",
            "name": "Ian Malcolm",
            "role": "Technician",
            "territory": "Central",
            "skills": ["safety", "cabling"],
            "availability": "Offline",
            "assigned_job_ids": [],
        },
        {
            "id": "tech_10",
            "name": "Dave Miller",
            "role": "Dispatch Manager",
            "territory": "Central",
            "skills": ["management"],
            "availability": "Available",
            "assigned_job_ids": [],
        },
    ],
    "jobs": [
        {
            "id": "job_1",
            "customer_name": "John Doe",
            "coordinates": {"lat": 37.795, "lng": -122.440},
            "status": "Assigned",
            "assigned_technician_id": "tech_1",
            "required_skill": "hvac",
            "priority": "High",
            "time_window": "08:00 - 10:00",
            "notes": "Air conditioner making loud noise.",
        },
        {
            "id": "job_2",
            "customer_name": "Jane Smith",
            "coordinates": {"lat": 37.780, "lng": -122.485},
            "status": "Assigned",
            "assigned_technician_id": "tech_2",
            "required_skill": "plumbing",
            "priority": "Medium",
            "time_window": "09:00 - 11:00",
            "notes": "Kitchen sink leak repair.",
        },
        {
            "id": "job_3",
            "customer_name": "Acme Corp",
            "coordinates": {"lat": 37.750, "lng": -122.425},
            "status": "Assigned",
            "assigned_technician_id": "tech_3",
            "required_skill": "electrical",
            "priority": "High",
            "time_window": "08:30 - 10:30",
            "notes": "Main breaker tripping repeatedly.",
        },
        {
            "id": "job_4",
            "customer_name": "Emperor Hotel",
            "coordinates": {"lat": 37.785, "lng": -122.408},
            "status": "Assigned",
            "assigned_technician_id": "tech_4",
            "required_skill": "cabling",
            "priority": "Medium",
            "time_window": "10:00 - 12:00",
            "notes": "Server room ethernet socket replacement.",
        },
        {
            "id": "job_5",
            "customer_name": "Baker Bakery",
            "coordinates": {"lat": 37.798, "lng": -122.415},
            "status": "Assigned",
            "assigned_technician_id": "tech_5",
            "required_skill": "electrical",
            "priority": "High",
            "time_window": "11:00 - 13:00",
            "notes": "Oven thermostat malfunctioning.",
        },
        {
            "id": "job_6",
            "customer_name": "Café Trieste",
            "coordinates": {"lat": 37.801, "lng": -122.407},
            "status": "Assigned",
            "assigned_technician_id": "tech_6",
            "required_skill": "safety",
            "priority": "Low",
            "time_window": "13:00 - 15:00",
            "notes": "Annual fire extinguisher inspection.",
        },
        {
            "id": "job_7",
            "customer_name": "City Library",
            "coordinates": {"lat": 37.778, "lng": -122.418},
            "status": "Assigned",
            "assigned_technician_id": "tech_7",
            "required_skill": "hvac",
            "priority": "Medium",
            "time_window": "12:00 - 14:00",
            "notes": "Thermostat replacement in children's wing.",
        },
        {
            "id": "job_8",
            "customer_name": "YMCA Gym",
            "coordinates": {"lat": 37.770, "lng": -122.455},
            "status": "Assigned",
            "assigned_technician_id": "tech_8",
            "required_skill": "plumbing",
            "priority": "High",
            "time_window": "14:00 - 16:00",
            "notes": "Locker room shower drain blockage.",
        },
        {
            "id": "job_9",
            "customer_name": "Gourmet Deli",
            "coordinates": {"lat": 37.755, "lng": -122.410},
            "status": "Unassigned",
            "assigned_technician_id": None,
            "required_skill": "electrical",
            "priority": "High",
            "time_window": "15:00 - 17:00",
            "notes": "Walk-in freezer power loss.",
        },
        {
            "id": "job_10",
            "customer_name": "Golden Gate Visitor Center",
            "coordinates": {"lat": 37.808, "lng": -122.476},
            "status": "Unassigned",
            "assigned_technician_id": None,
            "required_skill": "safety",
            "priority": "Low",
            "time_window": "16:00 - 18:00",
            "notes": "Emergency lighting battery check.",
        },
        {
            "id": "job_11",
            "customer_name": "Union Square Store",
            "coordinates": {"lat": 37.788, "lng": -122.408},
            "status": "Unassigned",
            "assigned_technician_id": None,
            "required_skill": "hvac",
            "priority": "Medium",
            "time_window": "09:00 - 11:00",
            "notes": "No warm air blowing from vents.",
        },
        {
            "id": "job_12",
            "customer_name": "Mission Dental",
            "coordinates": {"lat": 37.760, "lng": -122.435},
            "status": "Unassigned",
            "assigned_technician_id": None,
            "required_skill": "plumbing",
            "priority": "High",
            "time_window": "10:30 - 12:30",
            "notes": "Dental chair water line issue.",
        },
        {
            "id": "job_13",
            "customer_name": "Sutter Health",
            "coordinates": {"lat": 37.790, "lng": -122.422},
            "status": "Unassigned",
            "assigned_technician_id": None,
            "required_skill": "safety",
            "priority": "High",
            "time_window": "08:00 - 10:00",
            "notes": "Urgent inspection of smoke detector fault.",
        },
        {
            "id": "job_14",
            "customer_name": "Ocean Beach Cafe",
            "coordinates": {"lat": 37.772, "lng": -122.511},
            "status": "Unassigned",
            "assigned_technician_id": None,
            "required_skill": "plumbing",
            "priority": "Medium",
            "time_window": "11:00 - 13:00",
            "notes": "Grease trap overflow.",
        },
        {
            "id": "job_15",
            "customer_name": "Ferry Building Shop",
            "coordinates": {"lat": 37.795, "lng": -122.393},
            "status": "Unassigned",
            "assigned_technician_id": None,
            "required_skill": "cabling",
            "priority": "Low",
            "time_window": "14:00 - 16:00",
            "notes": "New POS terminal data drop.",
        },
        {
            "id": "job_16",
            "customer_name": "GCP Office SF",
            "coordinates": {"lat": 37.789, "lng": -122.390},
            "status": "Unassigned",
            "assigned_technician_id": None,
            "required_skill": "electrical",
            "priority": "Medium",
            "time_window": "13:00 - 15:00",
            "notes": "Conference room TV mounting power outlet.",
        },
        {
            "id": "job_17",
            "customer_name": "Richmond Apartments",
            "coordinates": {"lat": 37.781, "lng": -122.464},
            "status": "Unassigned",
            "assigned_technician_id": None,
            "required_skill": "hvac",
            "priority": "Low",
            "time_window": "15:00 - 17:00",
            "notes": "Filter replacement for HVAC unit.",
        },
        {
            "id": "job_18",
            "customer_name": "Presidio Residence",
            "coordinates": {"lat": 37.797, "lng": -122.460},
            "status": "Unassigned",
            "assigned_technician_id": None,
            "required_skill": "plumbing",
            "priority": "High",
            "time_window": "09:00 - 11:00",
            "notes": "Main water shutoff valve replacement.",
        },
        {
            "id": "job_19",
            "customer_name": "Potrero Hill Loft",
            "coordinates": {"lat": 37.758, "lng": -122.399},
            "status": "Unassigned",
            "assigned_technician_id": None,
            "required_skill": "cabling",
            "priority": "Medium",
            "time_window": "12:00 - 14:00",
            "notes": "Coaxial cable connection repair.",
        },
        {
            "id": "job_20",
            "customer_name": "Mission High School",
            "coordinates": {"lat": 37.761, "lng": -122.428},
            "status": "Unassigned",
            "assigned_technician_id": None,
            "required_skill": "safety",
            "priority": "Low",
            "time_window": "14:30 - 16:30",
            "notes": "Checking exit sign illumination.",
        },
    ],
    "approval_requests": [],
    "activity_log": [
        {
            "id": "act_0",
            "timestamp": datetime.now().isoformat(),
            "user": "System",
            "action": "Database seeded with synthetic demo dataset.",
            "details": "Initialized 10 technicians and 20 service jobs.",
        }
    ],
}


def load_db() -> dict:
    os.makedirs(os.path.dirname(DATABASE_FILE), exist_ok=True)
    if not os.path.exists(DATABASE_FILE):
        save_db(INITIAL_DATA)
        return INITIAL_DATA
    try:
        with open(DATABASE_FILE) as f:
            return json.load(f)
    except Exception:
        save_db(INITIAL_DATA)
        return INITIAL_DATA


def save_db(data: dict) -> None:
    os.makedirs(os.path.dirname(DATABASE_FILE), exist_ok=True)
    with open(DATABASE_FILE, "w") as f:
        json.dump(data, f, indent=2)


def reset_db() -> dict:
    # Reset to default
    data = json.loads(json.dumps(INITIAL_DATA))
    data["activity_log"] = [
        {
            "id": "act_0",
            "timestamp": datetime.now().isoformat(),
            "user": "System",
            "action": "Database reset by user request.",
            "details": "Restored 10 technicians and 20 service jobs.",
        }
    ]
    save_db(data)
    return data


def log_activity(user: str, action: str, details: str) -> None:
    data = load_db()
    act_id = f"act_{len(data['activity_log']) + 1}"
    data["activity_log"].append(
        {
            "id": act_id,
            "timestamp": datetime.now().isoformat(),
            "user": user,
            "action": action,
            "details": details,
        }
    )
    save_db(data)


def get_kpis(data: dict) -> dict:
    jobs = data["jobs"]
    approvals = data["approval_requests"]
    techs = data["technicians"]

    total_jobs = len(jobs)
    assigned_jobs = sum(1 for j in jobs if j["status"] == "Assigned")
    unassigned_jobs = sum(1 for j in jobs if j["status"] == "Unassigned")
    in_progress_jobs = sum(1 for j in jobs if j["status"] == "In Progress")
    completed_jobs = sum(1 for j in jobs if j["status"] == "Completed")

    pending_approvals = sum(1 for a in approvals if a["status"] == "Pending")

    # Active technicians are those with role = Technician and availability in ["Available", "On Job", "Delayed"]
    active_techs = sum(
        1 for t in techs if t["role"] == "Technician" and t["availability"] != "Offline"
    )

    # Delayed jobs
    delayed_jobs = sum(
        1
        for t in techs
        if t["availability"] == "Delayed"
        for j in jobs
        if j["assigned_technician_id"] == t["id"]
    )

    return {
        "total_jobs": total_jobs,
        "assigned_jobs": assigned_jobs,
        "unassigned_jobs": unassigned_jobs,
        "in_progress_jobs": in_progress_jobs,
        "completed_jobs": completed_jobs,
        "pending_approvals": pending_approvals,
        "active_techs": active_techs,
        "delayed_jobs": delayed_jobs,
    }
