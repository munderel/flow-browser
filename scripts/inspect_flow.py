"""
Run this AFTER sign-in to capture the real Flow DOM so locators can be tuned.

Writes one HTML snapshot + one accessibility-tree snapshot per page state to
flow-api/inspections/. These dumps are gitignored (they may contain your
project names / thumbnails).

Usage:
    python scripts/inspect_flow.py
"""

import asyncio
import json
from pathlib import Path

from flow_browser import FlowBrowser
from flow_browser.constants import FLOW_URL
from flow_browser import locators as L


OUT_DIR = Path(__file__).resolve().parent.parent / "inspections"


async def snapshot(page, label: str) -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    html_path = OUT_DIR / f"{label}.html"
    summary_path = OUT_DIR / f"{label}.summary.json"

    html = await page.content()
    html_path.write_text(html, encoding="utf-8")

    # Quick probe: does each currently-defined locator resolve here?
    probes = {
        "signed_in_indicator": L.signed_in_indicator,
        "new_project_button": L.new_project_button,
        "prompt_textarea": L.prompt_textarea,
        "generate_button": L.generate_button,
        "model_picker": L.model_picker,
        "aspect_ratio_picker": L.aspect_ratio_picker,
        "duration_picker": L.duration_picker,
        "scene_cards": L.scene_cards,
        "ingredients_panel_toggle": L.ingredients_panel_toggle,
        "ingredient_upload_input": L.ingredient_upload_input,
    }
    summary: dict[str, int] = {}
    for name, fn in probes.items():
        try:
            summary[name] = await fn(page).count()
        except Exception as e:
            summary[name] = f"err: {e}"  # type: ignore[assignment]
    summary_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(f"  -> {label}: {summary}")


async def main() -> None:
    async with FlowBrowser(headless=False, slow_mo=50) as flow:
        await flow.ensure_signed_in()
        page = flow.page

        print(f"[1/2] home page snapshot...")
        await page.goto(FLOW_URL, wait_until="domcontentloaded")
        await page.wait_for_timeout(3000)
        await snapshot(page, "home")

        # Try clicking into the first project (read-only — no creation).
        try:
            first = L.project_card(page).first
            if await first.count() > 0:
                print(f"[2/2] project page snapshot (opening first existing project)...")
                await first.click()
                await page.wait_for_load_state("domcontentloaded")
                await page.wait_for_timeout(3000)
                await snapshot(page, "project")
            else:
                print("[2/2] no existing projects to open; skipping project snapshot")
                print("      (create one in the UI, re-run to get a project snapshot)")
        except Exception as e:
            print(f"[2/2] could not open a project: {e}")

        print()
        print(f"Snapshots written to {OUT_DIR}")
        print("Inspect *.summary.json first to see which locators currently miss (count: 0).")


if __name__ == "__main__":
    asyncio.run(main())
