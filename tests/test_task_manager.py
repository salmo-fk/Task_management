import sys
import os
import copy
import pytest
from datetime import datetime, timedelta

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.task_manager import (
    get_tasks, get_task_by_id, add_task, update_task,
    update_task_status, delete_task, search_tasks, task_list
)

class TestTaskManager:

    def setup_method(self):
        self.initial_tasks = [
            {
                "id": 1,
                "title": "Première tâche",
                "description": "Description de la première tâche",
                "status": "TODO",
                "created_at": "2025-06-30T22:00:00"
            },
            {
                "id": 2,
                "title": "Deuxième tâche",
                "description": "Description de la deuxième tâche",
                "status": "DONE",
                "created_at": "2025-06-30T22:01:00"
            },
            {
                "id": 3,
                "title": "Tâche en cours",
                "description": "Une tâche avec statut ONGOING",
                "status": "ONGOING",
                "created_at": "2025-06-30T22:02:00"
            }
        ]
        task_list.clear()
        task_list.extend(copy.deepcopy(self.initial_tasks))

    # --- US001 - Create task ---

    def test_add_task_with_title_only(self):
        task = add_task("Nouvelle tâche")
        assert task["title"] == "Nouvelle tâche"
        assert task["description"] == ""
        assert task["status"] == "TODO"
        assert isinstance(task["id"], int)
        # created_at is ISO format string
        created_at = datetime.fromisoformat(task["created_at"])
        now = datetime.now()
        # Allow created_at to be within 5 seconds of test execution time
        assert now - timedelta(seconds=5) <= created_at <= now
        
        # TODO: verifier que la tache soit bien ajoutée dans la task list

    def test_add_task_with_title_and_description(self):
        task = add_task("Tâche avec description", "Une description valide")
        assert task["title"] == "Tâche avec description"
        assert task["description"] == "Une description valide"

    def test_add_task_title_empty_should_fail(self):
        with pytest.raises(ValueError) as excinfo:
            add_task("")
        assert "Title is required" in str(excinfo.value)

        with pytest.raises(ValueError) as excinfo:
            add_task("     ")
        assert "Title is required" in str(excinfo.value)

    def test_add_task_title_too_long_should_fail(self):
        long_title = "a" * 101
        with pytest.raises(ValueError) as excinfo:
            add_task(long_title)
        assert "Title cannot exceed 100 characters" in str(excinfo.value)

    def test_add_task_description_too_long_should_fail(self):
        long_desc = "a" * 501
        with pytest.raises(ValueError) as excinfo:
            add_task("Titre valide", long_desc)
        assert "Description cannot exceed 500 characters" in str(excinfo.value)

    def test_add_task_title_trimming_spaces(self):
        task = add_task("  Titre avec espaces  ", "Description")
        assert task["title"] == "Titre avec espaces"
        assert task["description"] == "Description"

    # --- US002 - Get task by ID ---

    def test_get_existing_task_by_id(self):
        task = get_task_by_id(1)
        assert task["id"] == 1
        assert "title" in task
        assert "description" in task
        assert "status" in task
        assert "created_at" in task

    def test_get_task_by_nonexistent_id_should_fail(self):
        with pytest.raises(LookupError) as excinfo:
            get_task_by_id(999)
        assert "Task not found" in str(excinfo.value)

    # --- US003 - Modifier titre et description ---

    def test_update_task_title_valid(self):
        task = update_task(1, title="Nouveau titre", description=None)
        assert task["title"] == "Nouveau titre"
        assert task["description"] == self.initial_tasks[0]["description"]

    def test_update_task_description_valid(self):
        task = update_task(1, title=None, description="Nouvelle description")
        assert task["title"] == self.initial_tasks[0]["title"]
        assert task["description"] == "Nouvelle description"

    def test_update_task_title_and_description(self):
        task = update_task(1, title="Titre modifié", description="Desc modifiée")
        assert task["title"] == "Titre modifié"
        assert task["description"] == "Desc modifiée"

    def test_update_task_title_empty_should_fail(self):
        with pytest.raises(ValueError) as excinfo:
            update_task(1, title="", description=None)
        assert "Title is required" in str(excinfo.value)

    def test_update_task_title_too_long_should_fail(self):
        long_title = "a" * 101
        with pytest.raises(ValueError) as excinfo:
            update_task(1, title=long_title, description=None)
        assert "Title cannot exceed 100 characters" in str(excinfo.value)

    def test_update_task_description_too_long_should_fail(self):
        long_desc = "a" * 501
        with pytest.raises(ValueError) as excinfo:
            update_task(1, title=None, description=long_desc)
        assert "Description cannot exceed 500 characters" in str(excinfo.value)

    def test_update_nonexistent_task_should_fail(self):
        with pytest.raises(LookupError) as excinfo:
            update_task(999, title="ok", description="ok")
        assert "Task not found" in str(excinfo.value)

    def test_update_task_ignore_non_modifiable_fields(self):
        # update_task ne modifie que title et description, ignore id, status, created_at
        task = update_task(1, title="Titre val", description="Desc val")
        assert task["id"] == 1
        assert task["status"] == "TODO"
        # Pas de modification non voulue

    # --- US004 - Changer le statut ---

    def test_change_status_valid(self):
        for status in ["TODO", "ONGOING", "DONE"]:
            task = update_task_status(1, status)
            assert task["status"] == status

    def test_change_status_invalid_should_fail(self):
        with pytest.raises(ValueError) as excinfo:
            update_task_status(1, "INVALID")
        assert "Invalid status" in str(excinfo.value)

    def test_change_status_nonexistent_task_should_fail(self):
        with pytest.raises(LookupError) as excinfo:
            update_task_status(999, "TODO")
        assert "Task not found" in str(excinfo.value)

    # --- US005 - Supprimer une tâche ---

    def test_delete_existing_task(self):
        delete_task(1)
        with pytest.raises(LookupError):
            get_task_by_id(1)

    def test_delete_then_operations_should_fail(self):
        delete_task(1)
        with pytest.raises(LookupError):
            update_task(1, title="nouveau")
        with pytest.raises(LookupError):
            delete_task(1)
        with pytest.raises(LookupError):
            get_task_by_id(1)

    # --- Recherche simple ---

    def test_search_tasks_found(self):
        results = search_tasks("première")
        assert any("Première tâche" == t["title"] for t in results)

    def test_search_tasks_not_found(self):
        results = search_tasks("inexistant")
        assert results == []