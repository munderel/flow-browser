"""Hover and click a video tile to find Extend/Insert/Remove controls.

Set FLOW_PROJECT_ID to a Flow project UUID before running.
"""

import asyncio
import os
import re
from pathlib import Path

from flow_browser import FlowBrowser
from flow_browser.utils.logging import logger


PROJECT_ID = os.environ.get("FLOW_PROJECT_ID")
if not PROJECT_ID:
    raise SystemExit("Set FLOW_PROJECT_ID to a Flow project UUID before running.")


async def visible_labels(page) -> list[str]:
    return await page.evaluate(
        """() => {
            const out = new Set();
            document.querySelectorAll('button, [role=button], [role=menuitem]').forEach(el => {
                const r = el.getBoundingClientRect();
                if (r.width === 0 && r.height === 0) return;
                const t = (el.innerText || '').trim();
                if (t && t.length < 60) out.add(t);
            });
            return Array.from(out);
        }"""
    )


async def main() -> None:
    async with FlowBrowser(headless=False, slow_mo=100) as flow:
        await flow.ensure_signed_in()
        await flow.open_project(PROJECT_ID)
        page = flow.page
        await page.wait_for_timeout(3000)

        # Find a video tile.
        video_tiles = page.locator("[data-known-size] [data-tile-id]:has(video)")
        n = await video_tiles.count()
        logger.info(f"video tiles: {n}")
        if n == 0:
            # No video yet; use first tile of any kind
            video_tiles = page.locator("[data-known-size] [data-tile-id]")
            n = await video_tiles.count()
            logger.info(f"using any tile; total: {n}")
        tile = video_tiles.first

        baseline = set(await visible_labels(page))

        # 1) Hover.
        await tile.hover()
        await page.wait_for_timeout(800)
        hover_new = set(await visible_labels(page)) - baseline
        logger.info(f"on hover, new labels: {sorted(hover_new)}")

        # 2) Click.
        await tile.click()
        await page.wait_for_timeout(1500)
        click_new = set(await visible_labels(page)) - baseline
        logger.info(f"after click, new labels: {sorted(click_new)}")

        # 3) Right-click for context menu.
        bbox = await tile.bounding_box()
        if bbox:
            await page.mouse.click(bbox['x'] + bbox['width']/2, bbox['y'] + bbox['height']/2, button='right')
            await page.wait_for_timeout(1000)
            rclick_new = set(await visible_labels(page)) - baseline
            logger.info(f"after right-click, new labels: {sorted(rclick_new)}")

        Path("inspections/after_tile_interactions.html").write_text(
            await page.content(), encoding="utf-8"
        )


if __name__ == "__main__":
    asyncio.run(main())
