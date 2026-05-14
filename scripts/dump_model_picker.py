"""
Open the existing project, click the model picker, dump every visible menu
item / option so we can see what models are actually available.
"""

import asyncio
import json
from pathlib import Path

from flow_browser import FlowBrowser, locators as L


OUT = Path(__file__).resolve().parent.parent / "inspections" / "model_picker.json"


async def main() -> None:
    async with FlowBrowser(headless=False, slow_mo=50) as flow:
        await flow.ensure_signed_in()
        projects = await flow.list_projects()
        if not projects:
            print("no projects")
            return
        await flow.open_project(projects[0])
        await flow.page.wait_for_timeout(2000)

        picker = L.model_picker(flow.page)
        if await picker.count() == 0:
            print("no model picker visible")
            return
        await picker.click()
        await flow.page.wait_for_timeout(1500)

        # Grab all visible text in any role=menu / role=listbox / role=dialog
        items: list[dict] = await flow.page.evaluate(
            """() => {
                const collected = [];
                const containers = document.querySelectorAll(
                    '[role=menu], [role=listbox], [role=dialog], [data-radix-popper-content-wrapper]'
                );
                containers.forEach(c => {
                    c.querySelectorAll(
                        '[role=menuitem], [role=option], button, li, a'
                    ).forEach(el => {
                        const text = (el.innerText || '').trim();
                        if (text) collected.push({
                            text,
                            role: el.getAttribute('role') || el.tagName.toLowerCase(),
                            disabled: el.getAttribute('aria-disabled') === 'true' || el.disabled === true,
                        });
                    });
                });
                return collected;
            }"""
        )

        OUT.parent.mkdir(parents=True, exist_ok=True)
        OUT.write_text(json.dumps(items, indent=2), encoding="utf-8")
        print(f"{len(items)} items captured -> {OUT}")
        for it in items:
            print(f"  [{it['role']}] {it['text'][:120]}")


if __name__ == "__main__":
    asyncio.run(main())
