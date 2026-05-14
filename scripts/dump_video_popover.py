"""
Open project, click model picker, switch to Video tab, expand model dropdown,
dump everything visible. Reveals: available Veo models + duration controls.
"""

import asyncio
import json
import re
from pathlib import Path

from flow_browser import FlowBrowser, locators as L


OUT = Path(__file__).resolve().parent.parent / "inspections" / "video_popover.json"


async def main() -> None:
    async with FlowBrowser(headless=False, slow_mo=80) as flow:
        await flow.ensure_signed_in()
        projects = await flow.list_projects()
        if not projects:
            return
        await flow.open_project(projects[0])
        await flow.page.wait_for_timeout(2000)

        await L.model_picker(flow.page).click()
        await flow.page.wait_for_timeout(700)

        # Switch to Video tab.
        video_tab = L.output_kind_tab(flow.page, "video")
        if await video_tab.count() > 0:
            await video_tab.first.click()
            await flow.page.wait_for_timeout(500)
            print("switched to Video tab")
        else:
            print("Video tab not found")
            return

        # Dump popover state BEFORE expanding model menu.
        before = await flow.page.evaluate(
            """() => {
                const seen = new Set();
                const out = [];
                document.querySelectorAll(
                    '[role=tab], [role=button], button, [role=menuitem], [role=option]'
                ).forEach(el => {
                    const r = el.getBoundingClientRect();
                    if (r.width === 0 && r.height === 0) return;
                    const text = (el.innerText || '').trim();
                    if (!text || seen.has(text)) return;
                    seen.add(text);
                    out.push({
                        text,
                        role: el.getAttribute('role') || el.tagName.toLowerCase(),
                        selected: el.getAttribute('aria-selected') === 'true' || el.getAttribute('data-state') === 'active',
                    });
                });
                return out;
            }"""
        )

        # Now expand model dropdown.
        trigger = L.model_dropdown_trigger(flow.page)
        if await trigger.count() > 0:
            await trigger.click()
            await flow.page.wait_for_timeout(800)

        after = await flow.page.evaluate(
            """() => {
                const seen = new Set();
                const out = [];
                document.querySelectorAll(
                    '[role=menuitem], [role=option], [data-radix-popper-content-wrapper] button'
                ).forEach(el => {
                    const text = (el.innerText || '').trim();
                    if (!text || seen.has(text)) return;
                    seen.add(text);
                    out.push({
                        text,
                        role: el.getAttribute('role') || el.tagName.toLowerCase(),
                    });
                });
                return out;
            }"""
        )

        OUT.parent.mkdir(parents=True, exist_ok=True)
        OUT.write_text(
            json.dumps({"popover": before, "model_menu": after}, indent=2),
            encoding="utf-8",
        )
        print(f"\n=== VIDEO POPOVER (visible items) ===")
        for it in before:
            sel = " *SELECTED*" if it.get("selected") else ""
            print(f"  [{it['role']}] {it['text'][:120]}{sel}")
        print(f"\n=== MODEL MENU (after expand) ===")
        for it in after:
            print(f"  [{it['role']}] {it['text'][:120]}")
        print(f"\n-> {OUT}")


if __name__ == "__main__":
    asyncio.run(main())
