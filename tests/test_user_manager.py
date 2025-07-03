import pytest
import re
from src.user_manager import create_user, list_users, get_user_by_id

# Mock user store for isolated tests
@pytest.fixture
def clean_user_list(monkeypatch):
    test_users = []

    monkeypatch.setattr("src.user_manager.user_list", test_users)
    monkeypatch.setattr("src.user_manager._save_users", lambda users: None)
    return test_users

# ---------- US010 - CREATE USER ----------

def test_create_user_valid(clean_user_list):
    user = create_user("Alice", "alice@example.com")
    assert user["id"] == 1
    assert user["name"] == "Alice"
    assert user["email"] == "alice@example.com"
    assert "created_at" in user

def test_create_user_duplicate_email(clean_user_list):
    create_user("Alice", "alice@example.com")
    with pytest.raises(ValueError, match="Email already in use"):
        create_user("Another", "alice@example.com")

def test_create_user_invalid_email_format(clean_user_list):
    with pytest.raises(ValueError, match="Invalid email format"):
        create_user("Bob", "bob-at-email")

def test_create_user_empty_name(clean_user_list):
    with pytest.raises(ValueError, match="Name is required"):
        create_user("   ", "bob@example.com")

def test_create_user_name_too_long(clean_user_list):
    long_name = "A" * 51
    with pytest.raises(ValueError, match="Name cannot exceed 50 characters"):
        create_user(long_name, "bob@example.com")

# ---------- US011 - LIST USERS ----------

def test_list_users_basic_pagination(clean_user_list):
    create_user("C", "c@email.com")
    create_user("A", "a@email.com")
    create_user("B", "b@email.com")

    result = list_users(page=1, page_size=2)
    names = [u["name"] for u in result["users"]]

    assert names == ["A", "B"]
    assert result["total_users"] == 3
    assert result["total_pages"] == 2

def test_list_users_empty(clean_user_list):
    result = list_users(page=1, page_size=10)
    assert result["users"] == []
    assert result["total_users"] == 0
    assert result["total_pages"] == 0

def test_list_users_page_out_of_bounds(clean_user_list):
    create_user("X", "x@email.com")
    result = list_users(page=99, page_size=10)
    assert result["users"] == []

def test_list_users_sorting_by_name(clean_user_list):
    create_user("Charlie", "c@email.com")
    create_user("alice", "a@email.com")
    create_user("Bob", "b@email.com")

    result = list_users(page=1, page_size=10)
    names = [u["name"] for u in result["users"]]
    assert names == ["alice", "Bob", "Charlie"]

# ---------- GET USER BY ID ----------

def test_get_user_by_id_success(clean_user_list):
    u = create_user("Test", "test@email.com")
    fetched = get_user_by_id(u["id"])
    assert fetched["email"] == "test@email.com"

def test_get_user_by_id_not_found(clean_user_list):
    with pytest.raises(LookupError, match="User not found"):
        get_user_by_id(999)

def test_get_user_by_id_invalid_format(clean_user_list):
    with pytest.raises(LookupError, match="User not found"):
        get_user_by_id("invalid")
