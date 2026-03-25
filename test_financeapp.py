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
