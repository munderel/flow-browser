"""
Locator smoke test — the fast canary for "Flow's UI changed under us".

Skipped unless FLOW_E2E=1. Drives a real browser to flow home (and the first
project if any exist), then asserts every "always-present" locator resolves
to >= 1 element. Read-only — does not generate anything.

Run:
    $env:FLOW_E2E="1"; pytest -m e2e tests/e2e/test_locators_present.py -v
"""

import os

import pytest

from flow_browser import FlowBrowser, locators as L
from flow_browser.constants import FLOW_URL


pytestmark = [
    pytest.mark.e2e,
    pytest.mark.skipif(os.environ.get("FLOW_E2E") != "1", reason="set FLOW_E2E=1 to run"),
]


# (name, callable -> Locator, allow_zero)
HOME_LOCATORS = [
    ("signed_in_indicator", L.signed_in_indicator, False),
    ("new_project_button", L.new_project_button, False),
]

PROJECT_LOCATORS = [
    ("prompt_textarea", L.prompt_textarea, False),
    ("generate_button", L.generate_button, False),
    ("model_picker", L.model_picker, True),  # may be behind a settings panel
    ("aspect_ratio_picker", L.aspect_ratio_picker, True),
    ("duration_picker", L.duration_picker, True),
    ("scene_cards", L.scene_cards, True),  # empty project has none
    ("ingredients_panel_toggle", L.ingredients_panel_toggle, True),
]


@pytest.mark.asyncio
async def test_home_locators_resolve() -> None:
    async with FlowBrowser(headless=False) as flow:
        await flow.ensure_signed_in()
        await flow.page.goto(FLOW_URL, wait_until="domcontentloaded")
        await flow.page.wait_for_timeout(3000)
        misses: list[str] = []
        for name, fn, allow_zero in HOME_LOCATORS:
            count = await fn(flow.page).count()
            if count == 0 and not allow_zero:
                misses.append(name)
        assert not misses, f"home locators with 0 hits: {misses}"


@pytest.mark.asyncio
async def test_project_locators_resolve() -> None:
    async with FlowBrowser(headless=False) as flow:
        await flow.ensure_signed_in()
        projects = await flow.list_projects()
        if not projects:
            pytest.skip("no existing projects to inspect; create one and re-run")
        await flow.open_project(projects[0])
        await flow.page.wait_for_timeout(3000)
        misses: list[str] = []
        for name, fn, allow_zero in PROJECT_LOCATORS:
            count = await fn(flow.page).count()
            if count == 0 and not allow_zero:
                misses.append(name)
        assert not misses, f"project locators with 0 hits: {misses}"
