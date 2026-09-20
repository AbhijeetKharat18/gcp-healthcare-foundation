"""Browser end-to-end tests driving the real UI with Playwright/Chromium.

Opt-in (needs a browser): run with `NLA_E2E=1 pytest` or `make qa-e2e`. Boots
the app (mock LLM + DuckDB), loads the page in headless Chromium, asks a
question, and checks the answer renders; then submits an out-of-scope query and
checks the guardrail message appears.
"""

from __future__ import annotations

import os
import socket
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

import pytest

pytestmark = pytest.mark.e2e

_POC_ROOT = Path(__file__).resolve().parents[3]  # .../poc/nl-analytics-assistant


def _launch_kwargs() -> dict:
    """Use a specific Chromium binary if NLA_CHROMIUM_PATH is set.

    Handy where Playwright's pinned browser revision isn't installed but a
    Chromium binary exists (e.g. a preinstalled one). On a normal machine leave
    it unset and Playwright uses its own (run `playwright install chromium`).
    """
    path = os.getenv("NLA_CHROMIUM_PATH")
    return {"executable_path": path} if path else {}


def _free_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def _wait_healthy(url: str, timeout: float = 30.0) -> None:
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            with urllib.request.urlopen(url, timeout=1) as resp:
                if resp.status == 200:
                    return
        except Exception:
            time.sleep(0.3)
    raise RuntimeError(f"server did not become healthy at {url}")


@pytest.fixture(scope="module")
def base_url():
    if os.getenv("NLA_E2E") != "1":
        pytest.skip("set NLA_E2E=1 to run browser E2E tests")
    pytest.importorskip("playwright.sync_api")

    port = _free_port()
    env = {
        **os.environ,
        "NLA_PROVIDER": "mock",
        "NLA_EXECUTOR": "duckdb",
        "PYTHONPATH": "app",
    }
    proc = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "nl_analytics.main:app", "--port", str(port)],
        cwd=str(_POC_ROOT),
        env=env,
    )
    url = f"http://127.0.0.1:{port}"
    try:
        _wait_healthy(f"{url}/healthz")
        yield url
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=10)
        except subprocess.TimeoutExpired:
            proc.kill()


def test_ui_answers_a_question(base_url):
    from playwright.sync_api import sync_playwright

    with sync_playwright() as p:
        browser = p.chromium.launch(**_launch_kwargs())
        page = browser.new_page()
        page.goto(base_url)
        assert "NL Analytics Assistant" in page.title()

        page.fill("#q", "average length of stay by encounter type")
        page.click("#ask")

        page.wait_for_selector("#ok-body:not(.hidden)", timeout=15000)
        sql = page.inner_text("#sql").lower()
        assert "select" in sql and "v_encounter_facts" in sql
        rows = page.query_selector_all("#table tr")
        assert len(rows) > 1  # header + at least one data row
        browser.close()


def test_ui_shows_guardrail_block(base_url):
    from playwright.sync_api import sync_playwright

    with sync_playwright() as p:
        browser = p.chromium.launch(**_launch_kwargs())
        page = browser.new_page()
        page.goto(base_url)

        page.fill("#q", "delete all encounters")
        page.click("#ask")

        page.wait_for_selector(".notice.err", timeout=15000)
        err = page.inner_text(".notice.err").lower()
        assert "block" in err or "guardrail" in err
        browser.close()
