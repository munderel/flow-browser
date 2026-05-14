"""Upload an image then open the 'View uploaded media' panel and see what shows."""

import asyncio
import re
from pathlib import Path

from flow_browser import FlowBrowser
from flow_browser.utils.logging import logger


REF = Path(__file__).resolve().parent.parent / "inspections" / "ad_nano_banana_pro_v0.png"


async def main() -> None:
    async with FlowBrowser(headless=False, slow_mo=80) as flow:
        await flow.ensure_signed_in()
        projects = await flow.list_projects()
        await flow.open_project(projects[0])
        page = flow.page
        await page.wait_for_timeout(2000)

        # Upload via hidden input.
        await page.locator("input[type='file']").first.set_input_files(str(REF))
        logger.info("file set; waiting 5s for upload")
        await page.wait_for_timeout(5000)

        # Open 'View uploaded media' panel.
        view_btn = page.get_by_role("button", name=re.compile(r"view uploaded media", re.I))
        n = await view_btn.count()
        logger.info(f"view-uploaded-media buttons: {n}")
        if n > 0:
            await view_btn.first.click()
            await page.wait_for_timeout(2000)

        # Dump everything in the now-open panel.
        snapshot = await page.evaluate(
            """() => {
                // Find any container with 'uploaded' in aria-label or data-testid.
                const out = {};
                ['[data-ingredient-id]', '[data-asset-id]', '[data-media-id]',
                 '[data-upload-id]', '[data-tile-id]', '[data-id]'].forEach(s => {
                    out[s] = document.querySelectorAll(s).length;
                });
                // Also grab all img alts present.
                out.img_alts = Array.from(new Set(
                    Array.from(document.querySelectorAll('img')).map(i => i.getAttribute('alt'))
                )).filter(Boolean);
                return out;
            }"""
        )
        logger.info(f"after panel open: {snapshot}")

        Path("inspections/after_ingredient_v2.html").write_text(
            await page.content(), encoding="utf-8"
        )


if __name__ == "__main__":
    asyncio.run(main())
