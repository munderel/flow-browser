"""
Probe: open home, click 'New project', dump what happens.
Reveals whether Flow navigates straight to /project/<id> or opens a dialog first.
"""

import asyncio
import json
import re
from pathlib import Path

from flow_browser import FlowBrowser, locators as L
from flow_browser.constants import FLOW_URL


OUT = Path(__file__).resolve().parent.parent / "inspections"


async def main() -> None:
    async with FlowBrowser(headless=False, slow_mo=80) as flow:
        await flow.ensure_signed_in()
        page = flow.page
        await page.goto(FLOW_URL, wait_until="domcontentloaded")
        await page.wait_for_timeout(2500)

        before_url = page.url
        print(f"before click: url={before_url}")

        btn = L.new_project_button(page)
        cnt = await btn.count()
        print(f"new_project_button matches: {cnt}")
        if cnt == 0:
            return

        await btn.first.click()
        await page.wait_for_timeout(3000)
        after_url = page.url
        print(f"after click: url={after_url}")
        print(f"navigated: {before_url != after_url}")

        (OUT / "after_new_project.html").write_text(
            await page.content(), encoding="utf-8"
        )

        # Look for dialog / modal / textfield asking for a project name.
        dialog_count = await page.locator("[role=dialog]").count()
        input_count = await page.locator("input[type='text']:visible, [contenteditable]:visible").count()
        print(f"role=dialog count: {dialog_count}")
        print(f"visible text input/contenteditable count: {input_count}")

        # Dump any visible buttons inside the new page state.
        items = await page.evaluate(
            """() => {
                const out = [];
                document.querySelectorAll('button, [role=button], a').forEach(el => {
                    const r = el.getBoundingClientRect();
                    if (r.width === 0 && r.height === 0) return;
                    const t = (el.innerText || '').trim();
                    if (t && t.length < 60) out.push(t);
                });
                return Array.from(new Set(out)).slice(0, 60);
            }"""
        )
        print("\nvisible button/link labels:")
        for t in items:
            print(f"  {t!r}")


if __name__ == "__main__":
    asyncio.run(main())
