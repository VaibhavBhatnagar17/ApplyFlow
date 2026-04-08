"""JSON-based state persistence for user profile, preferences, and tracker."""

import json
from pathlib import Path
from dataclasses import asdict
from datetime import date

from .profile import Profile, JobPreferences

DATA_DIR = Path(__file__).parent.parent / "data"
STATE_FILE = DATA_DIR / "user_state.json"
JOBS_FILE = DATA_DIR / "active_jobs.json"


def save_profile(profile: Profile, prefs: JobPreferences):
    state = _load_state()
    state["profile"] = asdict(profile)
    state["preferences"] = asdict(prefs)
    _save_state(state)


def load_profile() -> tuple[Profile | None, JobPreferences | None]:
    state = _load_state()
    if "profile" not in state:
        return None, None
    p = Profile(**{k: v for k, v in state["profile"].items() if k in Profile.__dataclass_fields__})
    pr = JobPreferences(**{k: v for k, v in state["preferences"].items() if k in JobPreferences.__dataclass_fields__})
    return p, pr


def save_application(job_id: str, company: str, title: str, url: str, status: str = "applied", notes: str = ""):
    state = _load_state()
    apps = state.setdefault("applications", [])
    for app in apps:
        if app["job_id"] == job_id:
            app["status"] = status
            app["notes"] = notes
            _save_state(state)
            return
    apps.append({
        "job_id": job_id,
        "company": company,
        "title": title,
        "url": url,
        "status": status,
        "date_applied": date.today().isoformat(),
        "notes": notes,
    })
    _save_state(state)


def load_applications() -> list[dict]:
    state = _load_state()
    return state.get("applications", [])


def update_application_status(job_id: str, status: str, notes: str = ""):
    state = _load_state()
    for app in state.get("applications", []):
        if app["job_id"] == job_id:
            app["status"] = status
            if notes:
                app["notes"] = notes
            break
    _save_state(state)


def load_active_jobs() -> list[dict]:
    path = JOBS_FILE
    if not path.exists():
        path = DATA_DIR / "sample_jobs.json"
    if not path.exists():
        return []
    with open(path) as f:
        data = json.load(f)
    return data.get("verified_listings", data if isinstance(data, list) else [])


def save_active_jobs(listings: list[dict]):
    if JOBS_FILE.exists():
        with open(JOBS_FILE) as f:
            data = json.load(f)
    else:
        data = {"verified_listings": []}
    if isinstance(data, dict):
        data["verified_listings"] = listings
    else:
        data = {"verified_listings": listings}
    with open(JOBS_FILE, "w") as f:
        json.dump(data, f, indent=2)


def add_jobs_to_active(new_entries: list[dict]):
    listings = load_active_jobs()
    existing_keys = {(j.get("company", "").lower(), j.get("title", "").lower()) for j in listings}
    added = 0
    for entry in new_entries:
        key = (entry.get("company", "").lower(), entry.get("title", "").lower())
        if key not in existing_keys:
            listings.append(entry)
            existing_keys.add(key)
            added += 1
    if added:
        save_active_jobs(listings)
    return added


def _load_state() -> dict:
    if STATE_FILE.exists():
        with open(STATE_FILE) as f:
            return json.load(f)
    return {}


def _save_state(state: dict):
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2)
