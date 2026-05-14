"""
Optional live test: open a project that has at least one video tile, extend
its first scene by 4 more seconds with a continuation prompt, save the result.

Set FLOW_PROJECT_ID to a Flow project UUID before running.
COSTS CREDITS — only run when you want to verify the extend flow.
"""

import asyncio
import os
from pathlib import Path

from flow_browser import FlowBrowser
from flow_browser.utils.logging import logger


PROJECT_ID = os.environ.get("FLOW_PROJECT_ID")
if not PROJECT_ID:
    raise SystemExit("Set FLOW_PROJECT_ID to a Flow project UUID before running.")
OUT = Path(__file__).resolve().parent.parent / "inspections"


async def main() -> None:
    async with FlowBrowser(headless=False, slow_mo=80) as flow:
        await flow.ensure_signed_in()
        await flow.open_project(PROJECT_ID)
        await flow.page.wait_for_timeout(3000)

        # Find the first video tile (scene_index 0 may not be a video — pick by selector).
        video_tiles_locator = flow.page.locator(
            "[data-known-size] [data-tile-id]:has(video)"
        )
        n = await video_tiles_locator.count()
        if n == 0:
            logger.error("no video tiles in this project; run a Veo generation first")
            return
        # Use the data-tile-id of the first video tile.
        tile_id = await video_tiles_locator.first.get_attribute("data-tile-id")
        logger.info(f"extending video tile: {tile_id}")

        extended = await flow.project.edits.extend(
            tile_id,
            prompt="the camera pulls back slowly to reveal the full product line on a marble counter",
            seconds=4,
        )
        logger.info(f"new tile: {extended.scene_id} url={extended.url}")

        if extended.url:
            extended.bind(flow)
            out = await extended.download(OUT / "veo_extended.mp4")
            logger.info(f"saved: {out}")


if __name__ == "__main__":
    asyncio.run(main())
