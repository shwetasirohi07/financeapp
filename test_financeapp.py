import sqlite3
from pathlib import Path

import finaapp_py as app


def setup_test_storage(tmp_path, monkeypatch):
    db_path = tmp_path / "users.db"
    legacy_path = tmp_path / "users.json"
    monkeypatch.setattr(app, "USER_DB_PATH", db_path)
    monkeypatch.setattr(app, "LEGACY_USER_DB_PATH", legacy_path)
    app.ensure_user_table()
    return db_path, legacy_path


def test_api_key_format_validation():
    ok, _ = app.validate_api_key_format("x" * 24)
    assert ok is True

    ok, message = app.validate_api_key_format("short")
    assert ok is False
    assert "too short" in message.lower()


def test_append_message_keeps_order():
    base = [{"role": "system", "content": "hello"}]
    updated = app.append_message(base, "user", "question")
    assert len(updated) == 2
    assert updated[-1]["role"] == "user"
    assert updated[-1]["content"] == "question"
    assert len(base) == 1


def test_signup_and_fetch_user(tmp_path, monkeypatch):
    setup_test_storage(tmp_path, monkeypatch)

    success, message = app.signup_user(
        "Test User",
        "test@example.com",
        "password123",
        "password123",
    )

    assert success is True
    assert "verify email" in message.lower()

    user = app.fetch_user("test@example.com")
    assert user is not None
    assert user["name"] == "Test User"
    assert user["is_verified"] is False


def test_legacy_user_migration(tmp_path, monkeypatch):
    _, legacy_path = setup_test_storage(tmp_path, monkeypatch)
    legacy_path.write_text(
        """
        {
          "legacy@example.com": {
            "name": "Legacy User",
            "salt": "salt123",
            "password_hash": "hash123",
            "is_verified": true,
            "verification_code": null,
            "reset_code": null
          }
        }
        """.strip(),
        encoding="utf-8",
    )

    notice = app.migrate_legacy_users()
    migrated = app.fetch_user("legacy@example.com")

    assert migrated is not None
    assert migrated["name"] == "Legacy User"
    assert migrated["is_verified"] is True
    assert notice is not None
    assert "migrated 1 account" in notice.lower()


def test_reset_password_updates_hash(tmp_path, monkeypatch):
    setup_test_storage(tmp_path, monkeypatch)
    app.create_user_record(
        "reset@example.com",
        "Reset User",
        "oldsalt",
        app.hash_password("oldpassword", "oldsalt"),
        "123456",
    )
    app.update_user_codes("reset@example.com",
                          reset_code="999999", is_verified=True)

    success, _ = app.reset_password(
        "reset@example.com",
        "999999",
        "newpassword123",
        "newpassword123",
    )

    user = app.fetch_user("reset@example.com")
    assert success is True
    assert user is not None
    assert user["password_hash"] != app.hash_password("oldpassword", "oldsalt")
    assert user["reset_code"] is None


def test_login_requires_existing_account(tmp_path, monkeypatch):
    setup_test_storage(tmp_path, monkeypatch)

    success, message = app.login_user("missing@example.com", "password123")

    assert success is False
    assert "no account found" in message.lower()


def test_login_requires_verified_account(tmp_path, monkeypatch):
    setup_test_storage(tmp_path, monkeypatch)
    app.create_user_record(
        "newuser@example.com",
        "New User",
        "saltxyz",
        app.hash_password("password123", "saltxyz"),
        "111111",
    )

    success, message = app.login_user("newuser@example.com", "password123")

    assert success is False
    assert "not verified" in message.lower()


def test_login_rejects_wrong_password(tmp_path, monkeypatch):
    setup_test_storage(tmp_path, monkeypatch)
    app.create_user_record(
        "verified@example.com",
        "Verified User",
        "saltabc",
        app.hash_password("rightpassword", "saltabc"),
        "222222",
    )
    app.update_user_codes("verified@example.com",
                          verification_code="", is_verified=True)

    success, message = app.login_user("verified@example.com", "wrongpassword")

    assert success is False
    assert "incorrect password" in message.lower()


def test_login_accepts_trimmed_case_insensitive_email(tmp_path, monkeypatch):
    setup_test_storage(tmp_path, monkeypatch)
    app.create_user_record(
        "casecheck@example.com",
        "Case Check",
        "saltcase",
        app.hash_password("password123", "saltcase"),
        "333333",
    )
    app.update_user_codes("casecheck@example.com",
                          verification_code="", is_verified=True)

    success, message = app.login_user(
        "  CaseCheck@Example.com  ", "password123")

    assert success is True
    assert "welcome back" in message.lower()


def test_signup_rejects_duplicate_email_case_insensitive(tmp_path, monkeypatch):
    setup_test_storage(tmp_path, monkeypatch)
    first_success, _ = app.signup_user(
        "Dup User",
        "dup@example.com",
        "password123",
        "password123",
    )
    second_success, second_message = app.signup_user(
        "Dup User 2",
        "DUP@example.com",
        "password456",
        "password456",
    )

    assert first_success is True
    assert second_success is False
    assert "already exists" in second_message.lower()
