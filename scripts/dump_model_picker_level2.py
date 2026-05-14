"""
Open project, click the settings popover, then click the inner
'Nano Banana 2 arrow_drop_down' button to expose the actual model list,
and dump it.
"""

import asyncio
import json
import re
from pathlib import Path

from flow_browser import FlowBrowser, locators as L


OUT = Path(__file__).resolve().parent.parent / "inspections" / "model_picker_l2.json"


async def main() -> None:
    async with FlowBrowser(headless=False, slow_mo=80) as flow:
        await flow.ensure_signed_in()
        projects = await flow.list_projects()
        if not projects:
            return
        await flow.open_project(projects[0])
        await flow.page.wait_for_timeout(2000)

        # Open outer settings popover.
        outer = L.model_picker(flow.page)
        await outer.click()
        await flow.page.wait_for_timeout(800)

        # Inner: any button whose accessible name contains 'arrow_drop_down'.
        inner = flow.page.get_by_role("button", name=re.compile(r"arrow_drop_down", re.I))
        cnt = await inner.count()
        print(f"inner arrow_drop_down buttons: {cnt}")
        if cnt == 0:
            print("nothing to click")
            return
        await inner.first.click()
        await flow.page.wait_for_timeout(1500)

        items = await flow.page.evaluate(
            """() => {
                const seen = new Set();
                const out = [];
                document.querySelectorAll(
                    '[role=menu] [role=menuitem], [role=listbox] [role=option], ' +
                    '[role=dialog] button, [data-radix-popper-content-wrapper] button, ' +
                    '[data-radix-popper-content-wrapper] [role=menuitem]'
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
        OUT.write_text(json.dumps(items, indent=2), encoding="utf-8")
        print(f"{len(items)} items -> {OUT}")
        for it in items:
            print(f"  [{it['role']}] {it['text'][:120]}")


if __name__ == "__main__":
    asyncio.run(main())
