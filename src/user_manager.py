import json
import os
import re
from datetime import datetime
from typing import List, Dict, Optional, Union

USER_FILE = "users.json"
VALID_EMAIL_REGEX = r"^[\w\.-]+@[\w\.-]+\.\w+$"

_default_users: List[Dict] = []

# Internal functions to load/save users
def _load_users() -> List[Dict]:
    if os.path.exists(USER_FILE):
        try:
            with open(USER_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            _save_users(_default_users)
            return _default_users.copy()
    else:
        _save_users(_default_users)
        return _default_users.copy()

def _save_users(users: List[Dict]) -> None:
    try:
        with open(USER_FILE, "w", encoding="utf-8") as f:
            json.dump(users, f, ensure_ascii=False, indent=2)
    except IOError:
        pass

user_list = _load_users()


# ========== US010 ==========
def create_user(name: str, email: str) -> Dict:
    name = name.strip()
    email = email.strip().lower()

    if not name:
        raise ValueError("Name is required")
    if len(name) > 50:
        raise ValueError("Name cannot exceed 50 characters")
    if not re.match(VALID_EMAIL_REGEX, email):
        raise ValueError("Invalid email format")
    if any(u["email"].lower() == email for u in user_list):
        raise ValueError("Email already in use")

    user_id = max((u["id"] for u in user_list), default=0) + 1
    new_user = {
        "id": user_id,
        "name": name,
        "email": email,
        "created_at": datetime.now().isoformat()
    }

    user_list.append(new_user)
    _save_users(user_list)
    return new_user


# ========== US011 ==========
def list_users(page: int = 1, page_size: int = 20) -> Dict:
    if page < 1 or page_size < 1:
        raise ValueError("Invalid pagination parameters")

    sorted_users = sorted(user_list, key=lambda u: u["name"].lower())
    total_users = len(sorted_users)
    total_pages = (total_users + page_size - 1) // page_size

    if page > total_pages and total_users != 0:
        paginated_users = []
    else:
        start = (page - 1) * page_size
        end = start + page_size
        paginated_users = sorted_users[start:end]

    return {
        "users": paginated_users,
        "page": page,
        "page_size": page_size,
        "total_users": total_users,
        "total_pages": total_pages
    }


# ========== Helper ==========
def get_user_by_id(user_id: Union[int, str]) -> Dict:
    try:
        user_id = int(user_id)
    except (ValueError, TypeError):
        raise LookupError("User not found")

    for u in user_list:
        if u["id"] == user_id:
            return u
    raise LookupError("User not found")
