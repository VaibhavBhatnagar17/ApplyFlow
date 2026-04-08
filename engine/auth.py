"""Simple authentication system with hashed passwords and per-user data."""

import json
import hashlib
import secrets
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent / "data"
USERS_FILE = DATA_DIR / "users.json"
USERS_DIR = DATA_DIR / "users"


def _hash_password(password: str, salt: str = "") -> tuple[str, str]:
    if not salt:
        salt = secrets.token_hex(16)
    hashed = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 100000).hex()
    return hashed, salt


def _load_users() -> dict:
    if USERS_FILE.exists():
        with open(USERS_FILE) as f:
            return json.load(f)
    return {}


def _save_users(users: dict):
    USERS_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(USERS_FILE, "w") as f:
        json.dump(users, f, indent=2)


def register(username: str, password: str, display_name: str = "") -> tuple[bool, str]:
    username = username.strip().lower()
    if not username or not password:
        return False, "Username and password are required."
    if len(password) < 4:
        return False, "Password must be at least 4 characters."
    if len(username) < 3:
        return False, "Username must be at least 3 characters."

    users = _load_users()
    if username in users:
        return False, "Username already taken."

    hashed, salt = _hash_password(password)
    users[username] = {
        "password_hash": hashed,
        "salt": salt,
        "display_name": display_name or username,
    }
    _save_users(users)

    user_dir = USERS_DIR / username
    user_dir.mkdir(parents=True, exist_ok=True)

    return True, "Account created successfully!"


def login(username: str, password: str) -> tuple[bool, str]:
    username = username.strip().lower()
    users = _load_users()

    if username not in users:
        return False, "Invalid username or password."

    user = users[username]
    hashed, _ = _hash_password(password, user["salt"])

    if hashed != user["password_hash"]:
        return False, "Invalid username or password."

    return True, user.get("display_name", username)


def get_user_dir(username: str) -> Path:
    user_dir = USERS_DIR / username.strip().lower()
    user_dir.mkdir(parents=True, exist_ok=True)
    return user_dir
