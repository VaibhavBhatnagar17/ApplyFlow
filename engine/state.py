"""Per-user state persistence. Each user gets isolated profile, jobs, and applications."""

import json
from pathlib import Path
from dataclasses import asdict
from datetime import date

from .profile import Profile, JobPreferences

DATA_DIR = Path(__file__).parent.parent / "data"
JOBS_FILE = DATA_DIR / "active_jobs.json"


def _user_state_path(username: str) -> Path:
    if username:
        path = DATA_DIR / "users" / username.strip().lower() / "state.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        return path
    return DATA_DIR / "user_state.json"


def _load_user_state(username: str) -> dict:
    path = _user_state_path(username)
    if path.exists():
        with open(path) as f:
            return json.load(f)
    return {}


def _save_user_state(username: str, state: dict):
    path = _user_state_path(username)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        json.dump(state, f, indent=2)


def save_profile(profile: Profile, prefs: JobPreferences, username: str = ""):
    state = _load_user_state(username)
    state["profile"] = asdict(profile)
    state["preferences"] = asdict(prefs)
    _save_user_state(username, state)


def load_profile(username: str = "") -> tuple[Profile | None, JobPreferences | None]:
    state = _load_user_state(username)
    if "profile" not in state:
        return None, None
    p = Profile(**{k: v for k, v in state["profile"].items() if k in Profile.__dataclass_fields__})
    pr = JobPreferences(**{k: v for k, v in state["preferences"].items() if k in JobPreferences.__dataclass_fields__})
    return p, pr


def save_application(job_id: str, company: str, title: str, url: str,
                     status: str = "applied", notes: str = "", username: str = ""):
    state = _load_user_state(username)
    apps = state.setdefault("applications", [])
    for app in apps:
        if app["job_id"] == job_id:
            app["status"] = status
            app["notes"] = notes
            _save_user_state(username, state)
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
    _save_user_state(username, state)


def load_applications(username: str = "") -> list[dict]:
    state = _load_user_state(username)
    return state.get("applications", [])


def update_application_status(job_id: str, status: str, notes: str = "", username: str = ""):
    state = _load_user_state(username)
    for app in state.get("applications", []):
        if app["job_id"] == job_id:
            app["status"] = status
            if notes:
                app["notes"] = notes
            break
    _save_user_state(username, state)


def save_resume_text(text: str, username: str = ""):
    state = _load_user_state(username)
    state["resume_text"] = text
    _save_user_state(username, state)


def load_resume_text(username: str = "") -> str:
    state = _load_user_state(username)
    return state.get("resume_text", "")


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
