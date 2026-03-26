# -*- coding: utf-8 -*-
import hashlib
import http.client
import os
import re
import sqlite3
import time
import unicodedata
from pathlib import Path
from typing import Callable

import pandas as pd
import streamlit as st
from dotenv import load_dotenv
from mistralai.client import Mistral

# Load `.env` file (ignored by git) for local development
load_dotenv()

st.set_page_config(page_title="Financial Advisor Bot", page_icon="💰")

st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Manrope:wght@400;500;700;800&family=Playfair+Display:wght@700;800&display=swap');

    :root {
        --bg-main: #f6efe3;
        --bg-card: rgba(255, 251, 245, 0.78);
        --bg-accent: #0e3938;
        --text-main: #182126;
        --text-soft: #54606b;
        --gold: #d9a441;
        --coral: #db6d57;
        --mint: #63baa8;
        --ink-blue: #19384f;
        --line: rgba(14, 57, 56, 0.14);
        --shadow: 0 24px 70px rgba(17, 60, 58, 0.14);
    }

    @keyframes bg-shift {
        0%   { background-position: 0% 50%; }
        50%  { background-position: 100% 50%; }
        100% { background-position: 0% 50%; }
    }

    .stApp {
        background: linear-gradient(
            135deg,
            #f9efe0,
            #f0e8d0,
            #ddf4ec,
            #e8f5f0,
            #fdf3e3,
            #e5f0eb,
            #f9ede0
        );
        background-size: 400% 400%;
        animation: bg-shift 18s ease infinite;
        color: var(--text-main);
        font-family: 'Manrope', sans-serif;
    }

    .block-container {
        padding-top: 2.2rem;
        padding-bottom: 2rem;
        max-width: 1120px;
    }

    h1, h2, h3 {
        color: var(--text-main);
        letter-spacing: -0.02em;
    }

    .hero-shell {
        position: relative;
        overflow: hidden;
        padding: 2.1rem 2.1rem 1.6rem 2.1rem;
        border: 1px solid rgba(255, 255, 255, 0.55);
        border-radius: 34px;
        background:
            linear-gradient(135deg, rgba(255, 248, 236, 0.98), rgba(242, 255, 250, 0.82)),
            rgba(255, 255, 255, 0.7);
        box-shadow: var(--shadow);
        backdrop-filter: blur(14px);
        margin-bottom: 1.2rem;
    }

    .hero-shell::after {
        content: "";
        position: absolute;
        width: 340px;
        height: 340px;
        right: -110px;
        top: -120px;
        border-radius: 50%;
        background: radial-gradient(circle, rgba(219, 109, 87, 0.24), transparent 68%);
    }

    .hero-shell::before {
        content: "";
        position: absolute;
        inset: auto auto -140px -90px;
        width: 280px;
        height: 280px;
        border-radius: 50%;
        background: radial-gradient(circle, rgba(25, 56, 79, 0.12), transparent 70%);
    }

    .eyebrow {
        display: inline-block;
        padding: 0.38rem 0.8rem;
        border-radius: 999px;
        background: rgba(17, 60, 58, 0.08);
        color: var(--bg-accent);
        font-size: 0.78rem;
        font-weight: 800;
        text-transform: uppercase;
        letter-spacing: 0.12em;
        margin-bottom: 0.9rem;
    }

    .hero-title {
        font-family: 'Playfair Display', serif;
        font-size: clamp(2.6rem, 5.8vw, 5.3rem);
        line-height: 0.9;
        margin: 0;
        max-width: 9ch;
    }

    .hero-subtitle {
        max-width: 45rem;
        font-size: 1.06rem;
        line-height: 1.8;
        color: var(--text-soft);
        margin: 1rem 0 0 0;
    }

    .hero-grid {
        display: grid;
        grid-template-columns: 1.5fr 1fr;
        gap: 1.2rem;
        align-items: stretch;
    }

    .hero-stack {
        display: flex;
        flex-direction: column;
        justify-content: space-between;
        min-height: 100%;
    }

    .headline-accent {
        color: var(--coral);
    }

    .hero-metrics {
        display: flex;
        gap: 0.8rem;
        margin-top: 1.4rem;
        flex-wrap: wrap;
    }

    .metric-pill {
        min-width: 140px;
        border-radius: 18px;
        padding: 0.85rem 1rem;
        background: rgba(255, 255, 255, 0.68);
        border: 1px solid rgba(14, 57, 56, 0.1);
        box-shadow: 0 14px 24px rgba(24, 33, 38, 0.06);
    }

    .metric-pill strong {
        display: block;
        font-size: 1.1rem;
        color: var(--bg-accent);
    }

    .metric-pill span {
        font-size: 0.82rem;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        color: var(--text-soft);
    }

    .stat-card {
        position: relative;
        overflow: hidden;
        background: linear-gradient(180deg, rgba(14, 57, 56, 0.98), rgba(17, 71, 69, 0.95));
        color: #f5f4ef;
        border-radius: 28px;
        padding: 1.35rem;
        box-shadow: 0 18px 40px rgba(17, 60, 58, 0.24);
        display: flex;
        flex-direction: column;
        justify-content: space-between;
        min-height: 100%;
    }

    .stat-card::after {
        content: "";
        position: absolute;
        width: 180px;
        height: 180px;
        right: -40px;
        bottom: -60px;
        border-radius: 50%;
        background: radial-gradient(circle, rgba(217, 164, 65, 0.2), transparent 65%);
    }

    .stat-label {
        opacity: 0.72;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        font-size: 0.76rem;
        font-weight: 700;
    }

    .stat-value {
        font-size: 2rem;
        font-weight: 800;
        margin-top: 0.35rem;
    }

    .stat-copy {
        margin-top: 0.45rem;
        color: rgba(245, 244, 239, 0.8);
        line-height: 1.5;
        font-size: 0.95rem;
    }

    .hero-action {
        margin-top: 1rem;
    }

    .hero-action button {
        width: 100%;
        min-height: 52px;
        border-radius: 16px;
        border: 1px solid rgba(255, 255, 255, 0.14);
        background: linear-gradient(135deg, rgba(255, 248, 223, 0.98), rgba(231, 245, 240, 0.96));
        color: #163433;
        font-weight: 800;
        box-shadow: 0 10px 24px rgba(11, 30, 29, 0.2);
    }

    .hero-action button:hover {
        border-color: rgba(219, 109, 87, 0.35);
        transform: translateY(-1px);
    }

    .hero-panel-copy {
        margin-top: 0.9rem;
    }

    .hero-panel-actions {
        margin-top: 1rem;
        display: grid;
        gap: 0.65rem;
    }

    .hero-panel-actions .stButton > button {
        min-height: 58px;
        border-radius: 16px;
        white-space: normal;
        line-height: 1.35;
    }

    .market-strip {
        display: grid;
        grid-template-columns: repeat(3, minmax(150px, 1fr));
        gap: 0.7rem;
        margin-top: 1rem;
    }

    .market-card {
        border-radius: 18px;
        padding: 0.8rem 0.9rem;
        background: rgba(255, 255, 255, 0.07);
        border: 1px solid rgba(255, 255, 255, 0.08);
        min-width: 0;
    }

    .market-card strong {
        display: block;
        font-size: 0.92rem;
        color: #fff8df;
        white-space: nowrap;
        word-break: keep-all;
        overflow-wrap: normal;
    }

    .market-card span {
        display: block;
        margin-top: 0.2rem;
        font-size: 0.82rem;
        color: rgba(245, 244, 239, 0.78);
    }

    .feature-band {
        display: grid;
        grid-template-columns: repeat(3, minmax(0, 1fr));
        gap: 0.9rem;
        margin: 1rem 0 1rem 0;
    }

    .feature-card {
        border-radius: 24px;
        padding: 1.1rem 1.1rem;
        background: var(--bg-card);
        border: 1px solid var(--line);
        box-shadow: 0 16px 32px rgba(55, 72, 88, 0.08);
    }

    .feature-card h3 {
        margin: 0 0 0.35rem 0;
        font-size: 1rem;
    }

    .feature-card p {
        margin: 0;
        font-size: 0.93rem;
        color: var(--text-soft);
        line-height: 1.55;
    }

    .prompt-ribbon {
        display: flex;
        gap: 0.75rem;
        flex-wrap: wrap;
        margin: 0 0 1.4rem 0;
    }

    .prompt-chip {
        border-radius: 999px;
        padding: 0.85rem 1rem;
        background: rgba(255, 255, 255, 0.82);
        border: 1px solid rgba(14, 57, 56, 0.1);
        box-shadow: 0 12px 28px rgba(24, 33, 38, 0.05);
        font-size: 0.9rem;
        color: var(--ink-blue);
        font-weight: 700;
    }

    .metric-button-row,
    .market-button-row,
    .feature-button-row {
        margin-top: 0.85rem;
    }

    .metric-button-row .stButton > button {
        min-height: 82px;
        border-radius: 18px;
        border: 1px solid rgba(14, 57, 56, 0.08);
        background: rgba(255, 255, 255, 0.72);
        color: var(--bg-accent);
        font-weight: 800;
        box-shadow: 0 14px 24px rgba(24, 33, 38, 0.06);
    }

    .market-button-row .stButton > button {
        min-height: 154px;
        border-radius: 18px;
        border: 1px solid rgba(255, 255, 255, 0.08);
        background: rgba(255, 255, 255, 0.07);
        color: #fff8df;
        font-weight: 800;
        box-shadow: none;
        white-space: normal;
        line-height: 1.5;
    }

    .market-button-row .stButton > button:hover {
        border-color: rgba(255, 255, 255, 0.18);
        background: rgba(255, 255, 255, 0.11);
    }

    .feature-button-row .stButton > button {
        width: 200px !important;
        height: 200px !important;
        min-height: 200px !important;
        border-radius: 50% !important;
        border: 1px solid var(--line);
        background: var(--gold) !important;
        color: var(--text-main) !important;
        font-weight: 700;
        font-size: 0.78rem !important;
        line-height: 1.35;
        box-shadow: 0 16px 32px rgba(55, 72, 88, 0.08);
        white-space: normal;
        overflow: hidden;
        text-overflow: ellipsis;
        padding: 1.8rem 1.2rem !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        text-align: center;
        margin: 0 auto;
    }

    div[data-testid="column"] .stButton > button {
        width: 100%;
        min-height: 72px;
        padding: 0.9rem 1rem;
        border-radius: 999px;
        border: 1px solid rgba(14, 57, 56, 0.12);
        background: linear-gradient(135deg, rgba(255, 255, 255, 0.92), rgba(243, 250, 247, 0.9));
        color: var(--ink-blue);
        font-weight: 800;
        font-size: 0.92rem;
        line-height: 1.35;
        text-align: center;
        box-shadow: 0 14px 28px rgba(24, 33, 38, 0.08);
        transition: transform 0.18s ease, box-shadow 0.18s ease, border-color 0.18s ease, background 0.18s ease;
        cursor: pointer;
    }

    div[data-testid="column"] .stButton > button:hover {
        transform: translateY(-2px);
        border-color: rgba(219, 109, 87, 0.34);
        background: linear-gradient(135deg, rgba(255, 250, 242, 0.96), rgba(236, 248, 244, 0.96));
        box-shadow: 0 18px 30px rgba(24, 33, 38, 0.12);
    }

    div[data-testid="column"] .stButton > button:active {
        transform: translateY(0);
        box-shadow: 0 10px 18px rgba(24, 33, 38, 0.09);
    }

    .section-lead {
        margin: 0 0 0.85rem 0;
        font-size: 0.95rem;
        text-transform: uppercase;
        letter-spacing: 0.12em;
        color: var(--bg-accent);
        font-weight: 800;
    }

    [data-testid="stChatMessage"] {
        border: 1px solid var(--line);
        border-radius: 24px;
        background: rgba(255, 255, 255, 0.74);
        box-shadow: 0 14px 30px rgba(24, 33, 38, 0.07);
        padding: 0.3rem 0.45rem;
        backdrop-filter: blur(10px);
    }

    [data-testid="stChatMessage"][aria-label="Chat message from user"] {
        background: linear-gradient(135deg, rgba(255, 245, 224, 0.92), rgba(255, 251, 244, 0.92));
    }

    [data-testid="stChatMessage"][aria-label="Chat message from assistant"] {
        background: linear-gradient(135deg, rgba(244, 251, 248, 0.92), rgba(255, 255, 255, 0.88));
    }

    [data-testid="stChatMessage"] [data-testid="stMarkdownContainer"] p {
        color: var(--text-main);
        line-height: 1.7;
    }

    [data-testid="stChatInputTextArea"] textarea {
        border-radius: 18px !important;
        border: 1px solid rgba(17, 60, 58, 0.18) !important;
        background: rgba(255, 255, 255, 0.86) !important;
        box-shadow: 0 12px 24px rgba(24, 33, 38, 0.05);
        min-height: 58px !important;
    }

    .stButton > button {
        border-radius: 999px;
        border: none;
        background: linear-gradient(135deg, var(--gold), #efc66a);
        color: #1d262b;
        font-weight: 800;
        box-shadow: 0 12px 26px rgba(217, 164, 65, 0.32);
    }

    [data-testid="stSidebar"] {
        background:
            linear-gradient(180deg, rgba(10, 36, 36, 0.98), rgba(16, 52, 51, 0.96)),
            #0d3131;
        border-right: 1px solid rgba(255, 255, 255, 0.08);
    }

    [data-testid="stSidebar"] * {
        color: #eef4ef;
    }

    [data-testid="stSidebar"] .stTextInput input {
        background: rgba(255, 255, 255, 0.08);
        border: 1px solid rgba(255, 255, 255, 0.14);
        border-radius: 14px;
    }

    .sidebar-note {
        border-radius: 18px;
        padding: 1rem;
        background: rgba(255, 255, 255, 0.08);
        border: 1px solid rgba(255, 255, 255, 0.1);
        line-height: 1.6;
        color: rgba(238, 244, 239, 0.84);
    }

    .sidebar-note strong {
        color: #fff4cb;
    }

    [data-testid="stSidebar"] .stButton > button {
        background: rgba(255, 255, 255, 0.08) !important;
        color: #f5ede0 !important;
        box-shadow: 0 4px 14px rgba(0, 0, 0, 0.24) !important;
        border: 1px solid rgba(255, 255, 255, 0.12) !important;
    }

    [data-testid="stSidebar"] .stButton > button:hover {
        background: rgba(219, 109, 87, 0.3) !important;
    }

    .profile-card {
        display: flex;
        align-items: center;
        gap: 0.8rem;
        background: rgba(255, 255, 255, 0.06);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 18px;
        padding: 0.85rem 1rem;
        margin-bottom: 0.6rem;
    }

    .profile-avatar {
        width: 44px;
        height: 44px;
        border-radius: 50%;
        background: linear-gradient(135deg, #d9a441, #db6d57);
        display: flex;
        align-items: center;
        justify-content: center;
        font-weight: 800;
        font-size: 1rem;
        color: #fff;
        flex-shrink: 0;
    }

    .profile-name {
        font-weight: 700;
        font-size: 0.9rem;
        color: #fff;
    }

    .profile-email {
        font-size: 0.75rem;
        color: rgba(238, 244, 239, 0.6);
        word-break: break-all;
    }

    .profile-badge {
        display: inline-block;
        margin-top: 0.25rem;
        font-size: 0.68rem;
        padding: 0.15rem 0.55rem;
        border-radius: 99px;
        background: rgba(99, 186, 168, 0.2);
        color: #63baa8;
        border: 1px solid rgba(99, 186, 168, 0.35);
    }

    .profile-badge.unverified {
        background: rgba(217, 164, 65, 0.15);
        color: #d9a441;
        border-color: rgba(217, 164, 65, 0.3);
    }

    .logout-btn > div > button {
        background: rgba(219, 109, 87, 0.18) !important;
        border-color: rgba(219, 109, 87, 0.4) !important;
        color: #f5a08f !important;
    }

    .logout-btn > div > button:hover {
        background: rgba(219, 109, 87, 0.42) !important;
    }

    @media (max-width: 900px) {
        .hero-grid,
        .feature-band,
        .market-strip {
            grid-template-columns: 1fr;
        }

        .hero-shell {
            padding: 1.4rem;
        }
    }
    </style>
    """,
    unsafe_allow_html=True,
)

BASE_DIR = Path(__file__).resolve().parent
USER_DB_PATH = BASE_DIR / "users.db"
LEGACY_USER_DB_PATH = BASE_DIR / "users.json"
DEFAULT_MODEL = "mistral-large-latest"
DEFAULT_SYSTEM_PROMPT = """You are a helpful financial advisor assistant.
Provide advice on budgeting, investing, savings, and personal finance.
Keep answers clear and practical. Always mention this is educational, not professional financial advice."""


def hash_password(password: str, salt: str) -> str:
    """Create a deterministic password hash using SHA-256 and a per-user salt."""
    return hashlib.sha256(f"{salt}:{password}".encode("utf-8")).hexdigest()


def normalize_text(value: object) -> str:
    """Return display-safe text with normalized unicode and trimmed whitespace."""
    if value is None:
        return ""
    if not isinstance(value, str):
        value = str(value)
    return unicodedata.normalize("NFKC", value).replace("\r\n", "\n").replace("\r", "\n").strip()


@st.cache_resource(show_spinner=False)
def initialize_auth_storage() -> str | None:
    """Initialize persistent auth storage once per app process."""
    ensure_user_table()
    return migrate_legacy_users()


@st.cache_resource(show_spinner=False)
def get_mistral_client(api_key: str) -> Mistral:
    """Create and cache the Mistral client per API key."""
    return Mistral(api_key=api_key)


@st.cache_data(ttl=60, show_spinner=False)
def check_mistral_connectivity() -> tuple[bool, str]:
    """Perform a lightweight upstream connectivity check."""
    connection = http.client.HTTPSConnection("api.mistral.ai", timeout=5)
    try:
        connection.request("HEAD", "/")
        response = connection.getresponse()
        if response.status < 500:
            return True, "Mistral service reachable"
        return False, f"Mistral service returned status {response.status}"
    except OSError:
        return False, "Network connection to Mistral is unavailable"
    finally:
        connection.close()


def validate_api_key_format(api_key: str) -> tuple[bool, str]:
    """Run cheap local validation before hitting the upstream service."""
    clean_key = api_key.strip()
    if len(clean_key) < 20:
        return False, "The MISTRAL_API_KEY looks too short. Check the full key and try again."
    if any(ch.isspace() for ch in clean_key):
        return False, "The MISTRAL_API_KEY contains spaces or line breaks. Paste the exact key value only."
    return True, "API key format looks valid"


def build_service_status(api_key: str) -> tuple[bool, str]:
    """Summarize whether the app is ready to send live AI requests."""
    key_ok, key_message = validate_api_key_format(api_key)
    if not key_ok:
        return False, key_message

    connectivity_ok, connectivity_message = check_mistral_connectivity()
    if not connectivity_ok:
        return False, connectivity_message

    return True, "AI service is ready"


def should_enable_live_ai(api_key: str) -> tuple[bool, str]:
    """Expose service readiness as a small testable decision helper."""
    return build_service_status(api_key)


def get_db_connection() -> sqlite3.Connection:
    """Open a SQLite connection for local authentication storage."""
    connection = sqlite3.connect(USER_DB_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def ensure_user_table() -> None:
    """Create the local users table if it does not already exist."""
    with get_db_connection() as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                email TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                salt TEXT NOT NULL,
                password_hash TEXT NOT NULL,
                is_verified INTEGER NOT NULL DEFAULT 0,
                verification_code TEXT,
                reset_code TEXT
            )
            """
        )
        connection.commit()


def migrate_legacy_users() -> str | None:
    """Import users from the legacy JSON store into SQLite once when available."""
    if not LEGACY_USER_DB_PATH.exists():
        return None

    try:
        legacy_payload = LEGACY_USER_DB_PATH.read_text(encoding="utf-8")
    except OSError:
        return "Legacy users.json was found but could not be read."

    if not legacy_payload.strip():
        return None

    try:
        import json
        legacy_users = json.loads(legacy_payload)
    except json.JSONDecodeError:
        return "Legacy users.json was found but is not valid JSON."

    if not isinstance(legacy_users, dict) or not legacy_users:
        return None

    migrated_count = 0
    with get_db_connection() as connection:
        for email, user in legacy_users.items():
            if not isinstance(user, dict):
                continue

            clean_email = str(email).strip().lower()
            if not clean_email or fetch_user(clean_email):
                continue

            name = str(user.get("name", clean_email)).strip() or clean_email
            salt = user.get("salt")
            password_hash = user.get("password_hash")
            if not salt or not password_hash:
                continue

            connection.execute(
                """
                INSERT INTO users (email, name, salt, password_hash, is_verified, verification_code, reset_code)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    clean_email,
                    name,
                    str(salt),
                    str(password_hash),
                    int(bool(user.get("is_verified", False))),
                    user.get("verification_code"),
                    user.get("reset_code"),
                ),
            )
            migrated_count += 1
        connection.commit()

    if migrated_count:
        backup_path = LEGACY_USER_DB_PATH.with_suffix(".json.migrated")
        try:
            LEGACY_USER_DB_PATH.rename(backup_path)
        except OSError:
            return f"Migrated {migrated_count} account(s) from users.json into users.db."
        return f"Migrated {migrated_count} account(s) from users.json into users.db and renamed the legacy file to {backup_path.name}."

    return None


def fetch_user(email: str) -> dict | None:
    """Fetch a single user record from SQLite."""
    with get_db_connection() as connection:
        row = connection.execute(
            "SELECT email, name, salt, password_hash, is_verified, verification_code, reset_code FROM users WHERE email = ?",
            (email,),
        ).fetchone()
    if not row:
        return None
    return {
        "email": row["email"],
        "name": row["name"],
        "salt": row["salt"],
        "password_hash": row["password_hash"],
        "is_verified": bool(row["is_verified"]),
        "verification_code": row["verification_code"],
        "reset_code": row["reset_code"],
    }


def create_user_record(email: str, name: str, salt: str, password_hash: str, verification_code: str) -> None:
    """Insert a newly created user into SQLite."""
    with get_db_connection() as connection:
        connection.execute(
            """
            INSERT INTO users (email, name, salt, password_hash, is_verified, verification_code, reset_code)
            VALUES (?, ?, ?, ?, 0, ?, NULL)
            """,
            (email, name, salt, password_hash, verification_code),
        )
        connection.commit()


def update_user_codes(email: str, verification_code: str | None = None, reset_code: str | None = None, is_verified: bool | None = None) -> None:
    """Update code or verification fields for an existing user."""
    user = fetch_user(email)
    if not user:
        return
    next_verification_code = user["verification_code"] if verification_code is None else verification_code
    next_reset_code = user["reset_code"] if reset_code is None else reset_code
    next_is_verified = user["is_verified"] if is_verified is None else is_verified
    with get_db_connection() as connection:
        connection.execute(
            """
            UPDATE users
            SET verification_code = ?, reset_code = ?, is_verified = ?
            WHERE email = ?
            """,
            (next_verification_code, next_reset_code, int(next_is_verified), email),
        )
        connection.commit()


def update_user_password(email: str, salt: str, password_hash: str) -> None:
    """Update password credentials for an existing user."""
    with get_db_connection() as connection:
        connection.execute(
            """
            UPDATE users
            SET salt = ?, password_hash = ?, reset_code = NULL
            WHERE email = ?
            """,
            (salt, password_hash, email),
        )
        connection.commit()


def create_reset_code() -> str:
    """Generate a short numeric code for local verification and reset flows."""
    return f"{int.from_bytes(os.urandom(3), 'big') % 1_000_000:06d}"


def mask_email(email: str) -> str:
    """Return a masked email for displaying local verification or reset codes."""
    local_part, _, domain = email.partition("@")
    if len(local_part) <= 2:
        masked_local = local_part[:1] + "*" * max(len(local_part) - 1, 0)
    else:
        masked_local = f"{local_part[0]}{'*' * (len(local_part) - 2)}{local_part[-1]}"
    return f"{masked_local}@{domain}"


def verify_user(email: str, code: str) -> tuple[bool, str]:
    """Verify a user email using the locally stored verification code."""
    clean_email = email.strip().lower()
    user = fetch_user(clean_email)
    if not user:
        return False, "No account found for that email."
    if user.get("is_verified"):
        return True, "Email is already verified."
    if code.strip() != user.get("verification_code"):
        return False, "Verification code is incorrect."

    update_user_codes(clean_email, verification_code="", is_verified=True)
    return True, "Email verified. You can sign in now."


def create_reset_request(email: str) -> tuple[bool, str]:
    """Generate a local password reset code for an existing account."""
    clean_email = email.strip().lower()
    user = fetch_user(clean_email)
    if not user:
        return False, "No account found for that email."

    reset_code = create_reset_code()
    update_user_codes(clean_email, reset_code=reset_code)
    return True, f"Reset code for {mask_email(clean_email)}: {reset_code}"


def reset_password(email: str, code: str, new_password: str, confirm_password: str) -> tuple[bool, str]:
    """Reset a user's password after validating a stored reset code."""
    clean_email = email.strip().lower()
    user = fetch_user(clean_email)
    if not user:
        return False, "No account found for that email."
    if code.strip() != user.get("reset_code"):
        return False, "Reset code is incorrect."
    if len(new_password) < 8:
        return False, "Password must be at least 8 characters long."
    if new_password != confirm_password:
        return False, "Passwords do not match."

    salt = os.urandom(16).hex()
    update_user_password(clean_email, salt, hash_password(new_password, salt))
    return True, "Password updated. Please sign in with the new password."


def initialize_session_state() -> None:
    """Initialize required Streamlit session state values."""
    st.session_state.setdefault(
        "messages", [{"role": "system", "content": SYSTEM_PROMPT}])
    st.session_state.setdefault("queued_prompt", None)
    st.session_state.setdefault("auth_mode", "login")
    st.session_state.setdefault("authenticated", False)
    st.session_state.setdefault("current_user", None)
    st.session_state.setdefault("auth_notice", None)


def reset_chat_state() -> None:
    """Reset chat-specific session state while keeping authentication values."""
    st.session_state.messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    st.session_state.queued_prompt = None


def generate_assistant_reply(client: Mistral, messages: list[dict]) -> str:
    """Call Mistral with bounded retries and clear fallback errors."""
    retry_delays = [0.6, 1.2]
    last_error = None

    for attempt_index in range(len(retry_delays) + 1):
        try:
            response = client.chat.complete(
                model=MODEL,
                messages=[
                    {"role": item["role"],
                        "content": normalize_text(item["content"])}
                    for item in messages
                ],
                temperature=0.7,
                max_tokens=500,
                timeout_ms=20000,
            )
            return normalize_text(response.choices[0].message.content)
        except Exception as exc:
            last_error = normalize_text(str(exc))
            if attempt_index < len(retry_delays):
                time.sleep(retry_delays[attempt_index])

    lowered_error = (last_error or "").lower()
    if "timeout" in lowered_error or "timed out" in lowered_error:
        return "I could not get a response from the AI service in time. Please try again in a few seconds, or ask a shorter question."
    if "unauthorized" in lowered_error or "api key" in lowered_error or "authentication" in lowered_error:
        return "The AI service rejected the request. Check that your MISTRAL_API_KEY is valid and try again."
    if "rate" in lowered_error or "429" in lowered_error or "quota" in lowered_error:
        return "The AI service is currently rate limiting requests. Wait a moment and try again."
    return "The AI service is temporarily unavailable. Please try again shortly. If the issue continues, verify your network connection and API key."


def bootstrap_runtime(api_key: str) -> tuple[Mistral, bool, str, str | None]:
    """Prepare cached runtime dependencies and status for the app."""
    client = get_mistral_client(api_key)
    service_ready, service_status_message = should_enable_live_ai(api_key)
    migration_notice = initialize_auth_storage()
    return client, service_ready, service_status_message, migration_notice


def append_message(messages: list[dict], role: str, content: str) -> list[dict]:
    """Return an updated message list with one appended message."""
    next_messages = list(messages)
    next_messages.append({"role": role, "content": content})
    return next_messages


def signup_user(name: str, email: str, password: str, confirm_password: str) -> tuple[bool, str]:
    """Create a new local user account after validation."""
    clean_name = name.strip()
    clean_email = email.strip().lower()

    if len(clean_name) < 2:
        return False, "Name must be at least 2 characters long."
    if not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", clean_email):
        return False, "Enter a valid email address."
    if len(password) < 8:
        return False, "Password must be at least 8 characters long."
    if password != confirm_password:
        return False, "Passwords do not match."

    if fetch_user(clean_email):
        return False, "An account with this email already exists."

    salt = os.urandom(16).hex()
    verification_code = create_reset_code()
    create_user_record(
        clean_email,
        clean_name,
        salt,
        hash_password(password, salt),
        verification_code,
    )
    update_user_codes(clean_email, verification_code="", is_verified=True)
    return True, "Account created and verified. You can sign in now."


def login_user(email: str, password: str) -> tuple[bool, str]:
    """Authenticate a user against the local credential store."""
    clean_email = email.strip().lower()
    user = fetch_user(clean_email)
    if not user:
        return False, "No account found for that email."
    if not user.get("is_verified"):
        return False, "Email not verified yet. Use Verify Email before signing in."

    expected_hash = hash_password(password, user["salt"])
    if expected_hash != user["password_hash"]:
        return False, "Incorrect password."

    st.session_state.authenticated = True
    st.session_state.current_user = {
        "email": clean_email,
        "name": user.get("name", clean_email),
        "is_verified": user.get("is_verified", False),
    }
    reset_chat_state()
    return True, f"Welcome back, {st.session_state.current_user['name']}."


def logout_user() -> None:
    """Log out the current user and clear chat data."""
    st.session_state.authenticated = False
    st.session_state.current_user = None
    reset_chat_state()


def render_auth_screen() -> None:
    """Render login and sign-up options before access to the app."""
    st.markdown(
        """
        <section class="hero-shell">
            <div class="hero-grid">
                <div class="hero-stack">
                    <div>
                        <div class="eyebrow">Secure Entry</div>
                        <h1 class="hero-title">Access your <span class="headline-accent">finance studio</span>.</h1>
                        <p class="hero-subtitle">
                            Create an account or sign in to keep your financial conversations tied to your own session.
                        </p>
                    </div>
                </div>
                <div class="stat-card">
                    <div>
                        <div class="stat-label">Private access</div>
                        <div class="stat-value">Login</div>
                        <div class="stat-copy hero-panel-copy">Credentials are stored locally in this app workspace with hashed passwords.</div>
                    </div>
                </div>
            </div>
        </section>
        """,
        unsafe_allow_html=True,
    )

    toggle_left, toggle_right = st.columns(2)
    with toggle_left:
        if st.button("Login", use_container_width=True, type="primary" if st.session_state.auth_mode == "login" else "secondary"):
            st.session_state.auth_mode = "login"
    with toggle_right:
        if st.button("Sign Up", use_container_width=True, type="primary" if st.session_state.auth_mode == "signup" else "secondary"):
            st.session_state.auth_mode = "signup"

    if st.session_state.auth_notice:
        st.info(st.session_state.auth_notice)

    if st.session_state.auth_mode == "login":
        with st.form("login_form", clear_on_submit=False):
            email = st.text_input("Email")
            password = st.text_input("Password", type="password")
            submitted = st.form_submit_button(
                "Sign In", use_container_width=True)
            if submitted:
                success, message = login_user(email, password)
                if success:
                    st.session_state.auth_notice = None
                    st.success(message)
                    st.rerun()
                st.error(message)
    else:
        with st.form("signup_form", clear_on_submit=True):
            name = st.text_input("Full Name")
            email = st.text_input("Email")
            password = st.text_input("Password", type="password")
            confirm_password = st.text_input(
                "Confirm Password", type="password")
            submitted = st.form_submit_button(
                "Create Account", use_container_width=True)
            if submitted:
                success, message = signup_user(
                    name, email, password, confirm_password)
                if success:
                    st.session_state.auth_mode = "login"
                    st.session_state.auth_notice = message
                    st.success(
                        "Account created. Complete email verification below.")
                else:
                    st.error(message)

    utility_col_left, utility_col_right = st.columns(2)
    with utility_col_left:
        with st.expander("Verify Email", expanded=False):
            with st.form("verify_email_form", clear_on_submit=True):
                verify_email_value = st.text_input(
                    "Email", key="verify_email_value")
                verify_code_value = st.text_input(
                    "Verification Code", key="verify_code_value")
                verify_submitted = st.form_submit_button(
                    "Verify", use_container_width=True)
                if verify_submitted:
                    success, message = verify_user(
                        verify_email_value, verify_code_value)
                    if success:
                        st.session_state.auth_notice = None
                        st.success(message)
                    else:
                        st.error(message)

    with utility_col_right:
        with st.expander("Reset Password", expanded=False):
            request_tab, reset_tab = st.tabs(["Get Code", "Use Code"])
            with request_tab:
                with st.form("request_reset_form", clear_on_submit=False):
                    reset_email_value = st.text_input(
                        "Email", key="reset_email_value")
                    request_submitted = st.form_submit_button(
                        "Generate Reset Code", use_container_width=True)
                    if request_submitted:
                        success, message = create_reset_request(
                            reset_email_value)
                        if success:
                            st.session_state.auth_notice = message
                            st.success(
                                "Reset code generated. Use it in the next tab.")
                        else:
                            st.error(message)
            with reset_tab:
                with st.form("reset_password_form", clear_on_submit=True):
                    reset_email_confirm = st.text_input(
                        "Email", key="reset_email_confirm")
                    reset_code = st.text_input("Reset Code", key="reset_code")
                    new_password = st.text_input(
                        "New Password", type="password", key="new_password")
                    confirm_new_password = st.text_input(
                        "Confirm New Password", type="password", key="confirm_new_password")
                    reset_submitted = st.form_submit_button(
                        "Reset Password", use_container_width=True)
                    if reset_submitted:
                        success, message = reset_password(
                            reset_email_confirm,
                            reset_code,
                            new_password,
                            confirm_new_password,
                        )
                        if success:
                            st.session_state.auth_mode = "login"
                            st.session_state.auth_notice = None
                            st.success(message)
                        else:
                            st.error(message)


# ---- Financial Data Parser ----

def _parse_amount(num_str: str, suffix: str) -> float:
    val = float(num_str.replace(",", ""))
    s = (suffix or "").lower()
    if s == "k":
        val *= 1_000
    elif s == "m":
        val *= 1_000_000
    return val


def _to_monthly(val: float, period: str) -> float:
    p = (period or "").lower()
    if ("bi" in p or "fortn" in p) and "week" in p:
        return val * 26 / 12
    if "week" in p:
        return val * 52 / 12
    if "day" in p:
        return val * 365 / 12
    if "year" in p or "annual" in p:
        return val / 12
    return val  # default: monthly


_PERIOD_PAT = (
    r"(?:a|per|each|every)?\s*"
    r"(week(?:ly)?|bi-?week(?:ly)?|fortnight(?:ly)?"
    r"|month(?:ly)?|year(?:ly)?|annual(?:ly)?|day(?:ly)?)"
)
_AMT_PAT = r"\$?([\d,]+(?:\.\d+)?)\s*([km])?"
_RANGE_PAT = (
    r"\$?([\d,]+(?:\.\d+)?)\s*([km])?"
    r"\s*(?:to about|to|\u2013|-)\s*"
    r"\$?([\d,]+(?:\.\d+)?)\s*([km])?"
)
_KW = {
    "income":   r"(?:earn|income|salary|make|paid|take.?home|gross|net pay|paycheck|bring in)",
    "expenses": r"(?:spend|expense|expenses|cost|costs|budget|outgoing|bills|monthly cost)",
    "savings":  r"(?:sav(?:e|ing|ings)|put away|set aside|stash)",
    "debt":     r"(?:debt|loan|owe|mortgage|credit card|student loan|car payment|balance owed)",
}


def extract_financials(messages: list) -> dict:
    """Extract income/expenses/savings/debt normalized to monthly.

    Handles: k/m shorthand, weekly/biweekly/annual/daily periods,
    ranges (uses midpoint), and percentage-based savings.
    """
    result = {}
    texts = [m["content"].lower()
             for m in messages if m.get("role") != "system"]
    for cat, kw in _KW.items():
        for text in reversed(texts):
            val = None
            ctx = rf"(?:{kw}[^.!?]{{0,60}}|[^.!?]{{0,40}}{kw}[^.!?]{{0,20}})"
            # Try range: "earn $2,000 to $3,500 a month"
            for match in re.finditer(
                rf"{ctx}{_RANGE_PAT}(?:[^.!?]{{0,30}}{_PERIOD_PAT})?",
                text, re.IGNORECASE,
            ):
                try:
                    lo = _parse_amount(match.group(1), match.group(2))
                    hi = _parse_amount(match.group(3), match.group(4))
                    period = match.group(
                        5) if match.lastindex and match.lastindex >= 5 else "month"
                    val = _to_monthly((lo + hi) / 2, period or "month")
                    break
                except Exception:
                    continue
            if val is None:
                # Try plain amount: "my salary is 4.5k per year"
                for match in re.finditer(
                    rf"{ctx}{_AMT_PAT}(?:[^.!?]{{0,30}}{_PERIOD_PAT})?",
                    text, re.IGNORECASE,
                ):
                    try:
                        amt = _parse_amount(match.group(1), match.group(2))
                        period = match.group(
                            3) if match.lastindex and match.lastindex >= 3 else "month"
                        if amt > 10:
                            val = _to_monthly(amt, period or "month")
                            break
                    except Exception:
                        continue
            if val is not None:
                result[cat] = round(val, 2)
                break

    # Percentage savings: "I save 15% of my income"
    if "income" in result and "savings" not in result:
        for text in reversed(texts):
            pct_match = re.search(
                r"(?:sav(?:e|ing|ings)|set aside|put away)[^.!?]{0,40}([\d]+(?:\.\d+)?)\s*%"
                r"|(\d+(?:\.\d+)?)\s*%[^.!?]{0,40}(?:sav(?:e|ing|ings)|set aside|put away)",
                text, re.IGNORECASE,
            )
            if pct_match:
                pct_val = float(pct_match.group(1) or pct_match.group(2))
                result["savings"] = round(result["income"] * pct_val / 100, 2)
                break

    return result


def compute_metrics(fin: dict) -> dict:
    """Derive surplus, savings rate, emergency runway, and debt payoff estimate."""
    m = {}
    inc = fin.get("income")
    exp = fin.get("expenses")
    sav = fin.get("savings")
    dbt = fin.get("debt")
    if inc and exp:
        m["surplus"] = round(inc - exp, 2)
    if sav and inc and inc > 0:
        m["savings_rate"] = round(sav / inc * 100, 1)
    if sav and exp and exp > 0:
        m["runway_months"] = round(sav / exp, 1)
    contribution = sav or (m["surplus"] if m.get("surplus", 0) > 0 else None)
    if dbt and contribution:
        m["payoff_months"] = int(round(dbt / contribution))
    return m


def render_snapshot() -> None:
    """Render a live Financial Snapshot section derived from chat data."""
    fin = extract_financials(st.session_state.messages)
    if not fin:
        return
    metrics = compute_metrics(fin)

    st.markdown(
        '<div class="section-lead">\U0001f4ca Your Financial Snapshot</div>',
        unsafe_allow_html=True,
    )

    # KPI metrics row
    kpi = []
    if "income" in fin:
        kpi.append(("Monthly Income", f"${fin['income']:,.0f}", None, "off"))
    if "expenses" in fin:
        kpi.append(
            ("Monthly Expenses", f"${fin['expenses']:,.0f}", None, "off"))
    if "savings_rate" in metrics:
        kpi.append(
            ("Savings Rate", f"{metrics['savings_rate']:.1f}%", None, "off"))
    if "surplus" in metrics:
        s = metrics["surplus"]
        kpi.append((
            "Monthly Surplus",
            f"${abs(s):,.0f}",
            "positive" if s >= 0 else "deficit",
            "normal" if s >= 0 else "inverse",
        ))
    if kpi:
        for col, (label, value, delta, dc) in zip(st.columns(len(kpi)), kpi):
            col.metric(label, value, delta=delta, delta_color=dc)

    # Bar chart + progress gauges
    chart_rows = []
    for cat, label in [
        ("income", "Income"), ("expenses", "Expenses"),
        ("savings", "Savings"), ("debt", "Debt"),
    ]:
        if cat in fin:
            chart_rows.append({"Category": label, "Amount ($)": fin[cat]})

    if len(chart_rows) >= 2:
        chart_col, gauge_col = st.columns([3, 2])
        with chart_col:
            st.bar_chart(
                chart_rows, x="Category", y="Amount ($)",
                color="#d9a441", use_container_width=True,
            )
        with gauge_col:
            if "savings_rate" in metrics:
                rate = metrics["savings_rate"]
                st.markdown(f"**Savings Rate** \u2014 {rate:.1f}%")
                st.progress(min(rate / 50.0, 1.0))
                st.caption("Great!" if rate >=
                           20 else "Aim for 20%+ to build long-term wealth")
            if "runway_months" in metrics:
                rm = metrics["runway_months"]
                st.markdown(f"**Emergency Runway** \u2014 {rm:.1f} months")
                st.progress(min(rm / 6.0, 1.0))
                st.caption("Healthy cushion!" if rm >=
                           3 else "Work toward 3\u20136 months of expenses")
            if "payoff_months" in metrics:
                pm = metrics["payoff_months"]
                yrs, mos = divmod(pm, 12)
                timeline = f"{yrs}y {mos}mo" if yrs else f"{mos} months"
                st.markdown(f"**Debt Payoff** \u2014 ~{timeline}")
                st.caption("Estimated at your current contribution rate")

    st.divider()


# ---- API key ----
api_key = os.getenv("MISTRAL_API_KEY") or st.sidebar.text_input(
    "MISTRAL_API_KEY",
    type="password",
    help="Enter your Mistral API key. Best practice: add this in Streamlit → Settings → Secrets."
)

if not api_key:
    st.info("🔑 Please add your MISTRAL_API_KEY in Secrets or enter it in the sidebar.")
    st.stop()

service_ready, service_status_message = build_service_status(api_key)

# Initialize Mistral client
MODEL = DEFAULT_MODEL
SYSTEM_PROMPT = DEFAULT_SYSTEM_PROMPT
client, service_ready, service_status_message, migration_notice = bootstrap_runtime(
    api_key)

# ---- Initialize Session State ----
initialize_session_state()
if migration_notice and not st.session_state.auth_notice:
    st.session_state.auth_notice = migration_notice

if not st.session_state.authenticated:
    render_auth_screen()
    with st.sidebar:
        st.header("Access")
        st.caption("Create an account or log in before starting a conversation.")
    st.stop()

# ---- UI ----
visible_messages = len(
    [m for m in st.session_state.messages if m["role"] != "system"])

metric_labels = [
    ("Focus\nBudgeting", "Help me build a practical monthly budget with clear categories and savings targets."),
    ("Mode\nLong-term wealth",
     "Help me create a long-term wealth-building plan with saving and investing priorities."),
    ("Tone\nClear and calm",
     "Explain my financial options in a clear, calm, beginner-friendly way."),
]

market_labels = [
    ("Emergency Fund\nPlan for 3 to 6 months",
     "Help me build an emergency fund plan for 3 to 6 months of expenses."),
    ("Debt Strategy\nSnowball or avalanche clarity",
     "Compare debt snowball versus debt avalanche for my situation."),
    ("Investing\nRisk explained simply",
     "Explain investing risk in simple language and how I should think about it."),
]

feature_labels = [
    ("Budget With Intention\nClear monthly priorities and realistic tradeoffs.",
     "Build me a budget that prioritizes essentials, savings, and realistic discretionary spending."),
    ("Invest Without Noise\nRisk, diversification, and planning in plain language.",
     "Teach me a calm, long-term investing approach with diversification and risk basics."),
    ("Save For Real Life\nEmergency funds, debt reduction, and milestone savings.",
     "Help me create a savings roadmap for emergencies, debt reduction, and personal milestones."),
]

st.markdown(
    f"""
    <section class="hero-shell">
        <div class="hero-grid">
            <div class="hero-stack">
                <div>
                    <div class="eyebrow">Money Clarity Studio</div>
                    <h1 class="hero-title">Make your <span class="headline-accent">money life</span> look as smart as it feels.</h1>
                    <p class="hero-subtitle">
                        An editorial-grade finance assistant for budgeting, debt strategy, investing, and next-step planning,
                        designed to turn uncertainty into elegant action.
                    </p>
                </div>
            </div>
            <div class="stat-card">
                <div>
                    <div class="stat-label">Live conversation</div>
                    <div class="stat-value">{visible_messages}</div>
                    <div class="stat-copy hero-panel-copy">Insights exchanged so far, with practical guidance tailored to your next money move.</div>
                </div>
            </div>
        </div>
    </section>
    """,
    unsafe_allow_html=True,
)

st.markdown('<div class="metric-button-row">', unsafe_allow_html=True)
metric_cols = st.columns(3)
for index, (label, prompt) in enumerate(metric_labels):
    with metric_cols[index]:
        if st.button(label, key=f"metric_{index}", use_container_width=True):
            st.session_state.queued_prompt = prompt
            st.rerun()
st.markdown('</div>', unsafe_allow_html=True)

hero_action_col_left, hero_action_col_right = st.columns([1.55, 1])
with hero_action_col_right:
    st.markdown('<div class="hero-panel-actions">', unsafe_allow_html=True)
    if st.button("Start Live Conversation", key="hero_live_conversation", use_container_width=True):
        st.session_state.queued_prompt = "Help me build a practical personal finance plan based on my income, expenses, savings, and debt."
        st.rerun()
    if st.button("Emergency Fund", key="hero_emergency_fund", use_container_width=True):
        st.session_state.queued_prompt = "Help me build an emergency fund plan for 3 to 6 months of expenses."
        st.rerun()
    if st.button("Debt Strategy", key="hero_debt_strategy", use_container_width=True):
        st.session_state.queued_prompt = "Compare debt snowball versus debt avalanche for my situation."
        st.rerun()
    if st.button("Investing Basics", key="hero_investing_basics", use_container_width=True):
        st.session_state.queued_prompt = "Explain investing risk in simple language and how I should think about it."
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

st.markdown('<div class="section-lead">What this studio does best</div>',
            unsafe_allow_html=True)
st.markdown('<div class="feature-button-row">', unsafe_allow_html=True)
feature_cols = st.columns(3)
for index, (label, prompt) in enumerate(feature_labels):
    with feature_cols[index]:
        if st.button(label, key=f"feature_{index}", use_container_width=True):
            st.session_state.queued_prompt = prompt
            st.rerun()
st.markdown('</div>', unsafe_allow_html=True)

st.markdown('<div class="section-lead">Instant conversation starters</div>',
            unsafe_allow_html=True)
_STARTER_PROMPTS = [
    "Build me a realistic monthly budget with savings targets",
    "Compare paying off debt versus investing extra cash",
    "Create a 12-month emergency fund plan for my income",
    "Explain index funds like I am just getting started",
]
_chip_cols = st.columns(len(_STARTER_PROMPTS))
for _i, _prompt_text in enumerate(_STARTER_PROMPTS):
    with _chip_cols[_i]:
        if st.button(_prompt_text, key=f"chip_{_i}", use_container_width=True):
            st.session_state.queued_prompt = _prompt_text
            st.rerun()

# ---- Finance Visual Snapshot (static illustrative charts) ----
st.markdown('<div class="section-lead">Finance Visual Snapshot</div>',
            unsafe_allow_html=True)

_kpi1, _kpi2, _kpi3 = st.columns(3)
_kpi1.metric("Net Worth", "$148,200", "+3.2%")
_kpi2.metric("Monthly Savings", "$1,250", "+$180")
_kpi3.metric("Debt Ratio", "24%", "-2%")

_chart_left, _chart_right = st.columns([1.1, 1])

with _chart_left:
    st.markdown("**Savings Growth (12 Months)**")
    _growth_df = pd.DataFrame(
        {
            "Month": ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
                      "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"],
            "Savings ($)": [5000, 5600, 6200, 6900, 7600, 8500,
                            9400, 10300, 11400, 12600, 13900, 15300],
        }
    ).set_index("Month")
    st.line_chart(_growth_df, use_container_width=True)

with _chart_right:
    st.markdown("**Portfolio Allocation**")
    _alloc_df = pd.DataFrame(
        {
            "Category": ["Equity", "Debt", "Emergency", "Gold", "Cash"],
            "Percent": [45, 22, 15, 10, 8],
        }
    ).set_index("Category")
    st.bar_chart(_alloc_df, use_container_width=True)

st.markdown("**Income vs Expenses**")
_inc_exp = pd.DataFrame(
    {
        "Month": ["Jul", "Aug", "Sep", "Oct", "Nov", "Dec"],
        "Income": [4200, 4300, 4250, 4400, 4500, 4600],
        "Expenses": [3100, 3050, 3200, 3150, 3250, 3300],
    }
).set_index("Month")
st.bar_chart(_inc_exp, use_container_width=True)

st.divider()

# ---- Financial Snapshot (auto-updates as you chat) ----
render_snapshot()

# ---- Display chat history ----
for m in st.session_state.messages:
    if m["role"] == "system":  # Don't display system prompt
        continue
    with st.chat_message("user" if m["role"] == "user" else "assistant"):
        st.markdown(normalize_text(m["content"]))

# ---- Chat Input ----
user_msg = st.chat_input("Type your financial question here...")
_pending = st.session_state.get("queued_prompt")
if _pending:
    st.session_state.queued_prompt = None
    user_msg = _pending
if user_msg:
    user_msg = normalize_text(user_msg)

    # Add user message to history
    st.session_state.messages = append_message(
        st.session_state.messages, "user", user_msg)
    with st.chat_message("user"):
        st.markdown(user_msg)

    # ---- Call Mistral API ----
    if not service_ready:
        bot_reply = (
            "The live AI service is not available right now. "
            f"Reason: {service_status_message}. "
            "Please fix the connection or API key and try again."
        )
    else:
        with st.spinner("Thinking..."):
            bot_reply = generate_assistant_reply(
                client, st.session_state.messages)

    # Add assistant response to history
    st.session_state.messages = append_message(
        st.session_state.messages, "assistant", bot_reply)
    with st.chat_message("assistant"):
        st.markdown(bot_reply)

# ---- Sidebar ----
with st.sidebar:
    st.header("Control Room")
    st.caption(
        "Tune the experience and keep your financial conversations focused.")

    if service_ready:
        st.success("AI service status: ready")
    else:
        st.warning(f"AI service status: {service_status_message}")

    if st.session_state.current_user:
        _u = st.session_state.current_user
        _initials = "".join(p[0].upper()
                            for p in _u["name"].split()[:2]) or "?"
        _badge_cls = "profile-badge" if _u.get(
            "is_verified") else "profile-badge unverified"
        _badge_txt = "✓ Verified" if _u.get("is_verified") else "⏳ Pending"
        st.markdown(
            f"""
            <div class="profile-card">
                <div class="profile-avatar">{_initials}</div>
                <div>
                    <div class="profile-name">{_u['name']}</div>
                    <div class="profile-email">{_u['email']}</div>
                    <span class="{_badge_cls}">{_badge_txt}</span>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        with st.expander("👤 Account Settings"):
            st.caption("Change your password")
            _old_pw = st.text_input(
                "Current password", type="password", key="acct_old_pw")
            _new_pw = st.text_input(
                "New password", type="password", key="acct_new_pw")
            _conf_pw = st.text_input(
                "Confirm new password", type="password", key="acct_conf_pw")
            if st.button("Update Password", use_container_width=True, key="acct_update_pw"):
                if not _old_pw or not _new_pw or not _conf_pw:
                    st.error("Please fill in all fields.")
                elif _new_pw != _conf_pw:
                    st.error("New passwords do not match.")
                elif len(_new_pw) < 8:
                    st.error("Password must be at least 8 characters.")
                else:
                    _db_user = fetch_user(_u["email"])
                    if _db_user and _db_user["password_hash"] == hash_password(_old_pw, _db_user["salt"]):
                        _new_salt = os.urandom(16).hex()
                        update_user_password(
                            _u["email"], _new_salt, hash_password(_new_pw, _new_salt))
                        st.success("Password updated successfully.")
                    else:
                        st.error("Current password is incorrect.")

        st.markdown('<div class="logout-btn">', unsafe_allow_html=True)
        if st.button("🚪 Log Out", use_container_width=True, key="sidebar_logout"):
            logout_user()
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    st.divider()

    if st.button("🗑️ Clear Chat History", use_container_width=True):
        reset_chat_state()
        st.rerun()

    st.divider()

    st.markdown(
        """
        <div class="sidebar-note">
            <strong>About this studio</strong><br>
            Designed for elegant, practical money conversations powered by Mistral AI.<br><br>
            <strong>Important:</strong> Guidance here is educational and should not replace advice from a qualified financial professional.
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.divider()

    st.caption(f"Messages in conversation: {visible_messages}")
