import os
import shutil
import socket
import subprocess
import time
from contextlib import closing
from pathlib import Path

import pytest
from playwright.sync_api import sync_playwright


ROOT = Path(__file__).resolve().parent
APP_FILE = ROOT / "finaapp_py.py"


def _find_free_port() -> int:
    with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as sock:
        sock.bind(("127.0.0.1", 0))
        sock.listen(1)
        return sock.getsockname()[1]


def _wait_for_server(port: int, timeout: float = 20.0) -> None:
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            with closing(socket.create_connection(("127.0.0.1", port), timeout=1)):
                return
        except OSError:
            time.sleep(0.2)
    raise RuntimeError(f"Streamlit server did not start on port {port}")


def _start_streamlit_process(port: int, tmp_path: Path) -> subprocess.Popen:
    env = os.environ.copy()
    env["MISTRAL_API_KEY"] = "x" * 24
    env["HOME"] = str(tmp_path)
    streamlit_executable = shutil.which("streamlit")
    if not streamlit_executable:
        pytest.skip("streamlit executable was not found on PATH")
    return subprocess.Popen(
        [
            streamlit_executable,
            "run",
            str(APP_FILE),
            "--server.headless",
            "true",
            "--server.port",
            str(port),
        ],
        cwd=ROOT,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )


def test_login_screen_smoke(tmp_path):
    port = _find_free_port()
    process = _start_streamlit_process(port, tmp_path)

    try:
        try:
            _wait_for_server(port)
        except RuntimeError as exc:
            output = process.stdout.read() if process.stdout else ""
            if "No module named 'streamlit'" in output:
                pytest.skip(
                    "streamlit executable is present but not runnable in the current test environment")
            raise RuntimeError(f"{exc}\nStreamlit output:\n{output}") from exc
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto(f"http://127.0.0.1:{port}", wait_until="networkidle")
            page.get_by_text("Secure Entry").wait_for(timeout=15000)
            page.get_by_text("Login").wait_for(timeout=15000)
            page.get_by_text("Sign Up").wait_for(timeout=15000)
            browser.close()
    finally:
        process.terminate()
        process.wait(timeout=10)


def test_signup_form_visible(tmp_path):
    port = _find_free_port()
    process = _start_streamlit_process(port, tmp_path)

    try:
        try:
            _wait_for_server(port)
        except RuntimeError as exc:
            output = process.stdout.read() if process.stdout else ""
            if "No module named 'streamlit'" in output:
                pytest.skip(
                    "streamlit executable is present but not runnable in the current test environment")
            raise RuntimeError(f"{exc}\nStreamlit output:\n{output}") from exc
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto(f"http://127.0.0.1:{port}", wait_until="networkidle")
            page.get_by_role("button", name="Sign Up").click()
            page.get_by_label("Full Name").wait_for(timeout=15000)
            page.get_by_label("Email").wait_for(timeout=15000)
            page.get_by_label("Password").wait_for(timeout=15000)
            browser.close()
    finally:
        process.terminate()
        process.wait(timeout=10)
