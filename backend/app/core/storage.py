"""
File-based storage: replaces PostgreSQL.
Repos are stored as JSON in data/repos.json.
Query history is kept in memory per session.
"""
import json
import os
import uuid
from datetime import datetime
from typing import List, Optional, Dict
from threading import Lock
from app.core.config import settings

REPOS_FILE = os.path.join(settings.DATA_DIR, "repos.json")
USERS_FILE = os.path.join(settings.DATA_DIR, "users.json")
_lock = Lock()

# In-memory query history (cleared on restart — no DB needed)
_query_history: List[dict] = []


def _ensure_dirs():
    os.makedirs(settings.DATA_DIR, exist_ok=True)
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    os.makedirs(settings.FAISS_INDEX_PATH, exist_ok=True)


def _load_repos() -> Dict[str, dict]:
    _ensure_dirs()
    if not os.path.exists(REPOS_FILE):
        return {}
    try:
        with open(REPOS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def _save_repos(repos: Dict[str, dict]):
    _ensure_dirs()
    with open(REPOS_FILE, "w", encoding="utf-8") as f:
        json.dump(repos, f, indent=2, default=str)


# --- REPO CRUD ---

def create_repo(name: str, source_type: str, user_id: str, github_url: Optional[str] = None) -> dict:
    with _lock:
        repos = _load_repos()
        repo_id = str(uuid.uuid4())
        repo = {
            "id": repo_id,
            "user_id": user_id,
            "name": name,
            "source_type": source_type,
            "github_url": github_url,
            "local_path": None,
            "faiss_index_path": None,
            "status": "pending",
            "error_message": None,
            "file_count": 0,
            "chunk_count": 0,
            "language_stats": {},
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
        }
        repos[repo_id] = repo
        _save_repos(repos)
        return dict(repo)


def get_repo(repo_id: str) -> Optional[dict]:
    repos = _load_repos()
    return repos.get(repo_id)


def list_repos(user_id: Optional[str] = None) -> List[dict]:
    repos = _load_repos()
    items = list(repos.values())
    if user_id:
        items = [r for r in items if r.get("user_id") == user_id]
    return sorted(items, key=lambda r: r["created_at"], reverse=True)


def update_repo(repo_id: str, **kwargs) -> Optional[dict]:
    with _lock:
        repos = _load_repos()
        if repo_id not in repos:
            return None
        repos[repo_id].update(kwargs)
        repos[repo_id]["updated_at"] = datetime.utcnow().isoformat()
        _save_repos(repos)
        return dict(repos[repo_id])


def delete_repo(repo_id: str) -> bool:
    with _lock:
        repos = _load_repos()
        if repo_id not in repos:
            return False
        del repos[repo_id]
        _save_repos(repos)
        return True


# --- QUERY HISTORY (in-memory) ---

def add_query_history(entry: dict) -> dict:
    entry["id"] = str(uuid.uuid4())
    entry["created_at"] = datetime.utcnow().isoformat()
    _query_history.append(entry)
    # Keep last 500 entries in memory
    if len(_query_history) > 500:
        _query_history.pop(0)
    return entry


def get_query_history(repo_id: str, limit: int = 50) -> List[dict]:
    return [
        q for q in reversed(_query_history)
        if q.get("repository_id") == repo_id
    ][:limit]


def update_query_feedback(query_id: str, feedback: str) -> bool:
    for q in _query_history:
        if q["id"] == query_id:
            q["feedback"] = feedback
            return True
    return False


# --- USER STORAGE (JSON-based, no database) ---

def _load_users() -> Dict[str, dict]:
    _ensure_dirs()
    if not os.path.exists(USERS_FILE):
        return {}
    try:
        with open(USERS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def _save_users(users: Dict[str, dict]):
    _ensure_dirs()
    with open(USERS_FILE, "w", encoding="utf-8") as f:
        json.dump(users, f, indent=2, default=str)


def create_user(email: str, username: str, hashed_password: str) -> dict:
    with _lock:
        users = _load_users()
        # Check uniqueness
        for u in users.values():
            if u["email"] == email:
                raise ValueError("Email already registered")
            if u["username"] == username:
                raise ValueError("Username already taken")
        user_id = str(uuid.uuid4())
        user = {
            "id": user_id,
            "email": email,
            "username": username,
            "hashed_password": hashed_password,
            "is_active": True,
            "avatar_url": None,
            "created_at": datetime.utcnow().isoformat(),
        }
        users[user_id] = user
        _save_users(users)
        return dict(user)


def get_user_by_email(email: str) -> Optional[dict]:
    users = _load_users()
    for u in users.values():
        if u["email"] == email:
            return dict(u)
    return None


def get_user_by_id(user_id: str) -> Optional[dict]:
    users = _load_users()
    return dict(users[user_id]) if user_id in users else None
