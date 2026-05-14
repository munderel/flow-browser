"""Create an empty project then dump every visible button + input to see what
upload mechanism (if any) exists in this layout."""

import asyncio
import json
from pathlib import Path

from flow_browser import FlowBrowser
from flow_browser.utils.logging import logger


OUT = Path(__file__).resolve().parent.parent / "inspections" / "empty_project_dump.json"


async def main() -> None:
    async with FlowBrowser(headless=False, slow_mo=80) as flow:
        await flow.ensure_signed_in()
        new = await flow.create_project("empty-probe")
        logger.info(f"created {new.id}")
        await flow.page.wait_for_timeout(3000)

        info = await flow.page.evaluate(
            """() => {
                const buttons = Array.from(document.querySelectorAll('button, [role=button]'))
                    .filter(el => {
                        const r = el.getBoundingClientRect();
                        return r.width > 0 && r.height > 0;
                    })
                    .map(el => (el.innerText || '').trim())
                    .filter(t => t && t.length < 80);
                const inputs = Array.from(document.querySelectorAll('input, textarea')).map(el => ({
                    tag: el.tagName.toLowerCase(),
                    type: el.getAttribute('type'),
                    placeholder: el.getAttribute('placeholder'),
                    aria_label: el.getAttribute('aria-label'),
                }));
                const fileInputs = document.querySelectorAll("input[type='file']").length;
                return { buttons: Array.from(new Set(buttons)), inputs, fileInputs };
            }"""
        )
        OUT.write_text(json.dumps(info, indent=2), encoding="utf-8")
        print(f"file inputs: {info['fileInputs']}")
        print(f"\nbuttons ({len(info['buttons'])}):")
        for b in info['buttons']:
            print(f"  {b!r}")
        print(f"\ninputs ({len(info['inputs'])}):")
        for i in info['inputs']:
            print(f"  {i}")

        # Cleanup.
        await flow.delete_project(new)


if __name__ == "__main__":
    asyncio.run(main())
