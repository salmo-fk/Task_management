import json
import os
from typing import List, Dict, Optional, Union
from datetime import datetime

DATA_FILE = "tasks.json"
VALID_STATUSES = {"TODO", "ONGOING", "DONE"}

DEFAULT_TASKS = [
    {
        "id": 1,
        "title": "Première tâche",
        "description": "Description de la première tâche",
        "status": "TODO",
        "created_at": datetime.now().isoformat()
    },
    {
        "id": 2,
        "title": "Deuxième tâche",
        "description": "Description de la deuxième tâche",
        "status": "DONE",
        "created_at": datetime.now().isoformat()
    }
]

def _load_tasks() -> List[Dict]:
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            _save_tasks(DEFAULT_TASKS)
            return DEFAULT_TASKS.copy()
    else:
        _save_tasks(DEFAULT_TASKS)
        return DEFAULT_TASKS.copy()

def _save_tasks(tasks: List[Dict]) -> None:
    try:
        with open(DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(tasks, f, ensure_ascii=False, indent=2)
    except IOError:
        pass

task_list = _load_tasks()

def _validate_task_id(task_id: Union[int, str]) -> int:
    """Valide que task_id est un int convertible. Sinon lève ValueError."""
    try:
        id_int = int(task_id)
        if id_int < 1:
            raise ValueError()
        return id_int
    except (ValueError, TypeError):
        raise ValueError("Invalid ID format")

def get_tasks(
    page: int = 1,
    page_size: int = 20  # défaut 20
) -> Dict:
    """
    Retourne un dict avec les tâches paginées + métadonnées.
    Clés : tasks (liste), page, page_size, total_tasks, total_pages
    """
    if page < 1:
        raise ValueError("Invalid page number")
    if page_size < 1:
        raise ValueError("Invalid page size")

    total_tasks = len(task_list)
    total_pages = (total_tasks + page_size - 1) // page_size

    # Si page hors limites, retourner liste vide
    if page > total_pages and total_tasks != 0:
        paginated_tasks = []
    else:
        start = (page - 1) * page_size
        end = start + page_size
        paginated_tasks = task_list[start:end]

    return {
        "tasks": paginated_tasks,
        "page": page,
        "page_size": page_size,
        "total_tasks": total_tasks,
        "total_pages": total_pages
    }

def add_task(title: str, description: str = "") -> Dict:
    title = title.strip()
    description = description.strip()

    if not title:
        raise ValueError("Title is required")
    if len(title) > 100:
        raise ValueError("Title cannot exceed 100 characters")
    if len(description) > 500:
        raise ValueError("Description cannot exceed 500 characters")

    new_id = max((t["id"] for t in task_list), default=0) + 1
    new_task = {
        "id": new_id,
        "title": title,
        "description": description,
        "status": "TODO",
        "created_at": datetime.now().isoformat()
    }
    task_list.append(new_task)
    _save_tasks(task_list)
    return new_task

def get_task_by_id(task_id: Union[int, str]) -> Dict:
    task_id = _validate_task_id(task_id)
    for task in task_list:
        if task["id"] == task_id:
            return task
    raise LookupError("Task not found")

def update_task(
    task_id: Union[int, str],
    title: Optional[str] = None,
    description: Optional[str] = None
) -> Dict:
    """Modifie titre et/ou description. Ignore id, status, created_at."""
    task = get_task_by_id(task_id)

    if title is not None:
        title = title.strip()
        if not title:
            raise ValueError("Title is required")
        if len(title) > 100:
            raise ValueError("Title cannot exceed 100 characters")
        task["title"] = title

    if description is not None:
        description = description.strip()
        if len(description) > 500:
            raise ValueError("Description cannot exceed 500 characters")
        task["description"] = description

    _save_tasks(task_list)
    return task

def update_task_status(task_id: Union[int, str], new_status: str) -> Dict:
    """
    Met à jour le statut d'une tâche.
    Valide statut dans VALID_STATUSES.
    """
    task = get_task_by_id(task_id)
    if new_status not in VALID_STATUSES:
        raise ValueError(f"Invalid status. Allowed values: {', '.join(VALID_STATUSES)}")
    task["status"] = new_status
    _save_tasks(task_list)
    return task

def delete_task(task_id: Union[int, str]) -> None:
    task_id = _validate_task_id(task_id)
    global task_list
    for i, task in enumerate(task_list):
        if task["id"] == task_id:
            del task_list[i]
            _save_tasks(task_list)
            return
    raise LookupError("Task not found")

def search_tasks(keyword: str) -> List[Dict]:
    keyword_lower = keyword.lower()
    return [t for t in task_list if keyword_lower in t["title"].lower() or keyword_lower in t["description"].lower()]

