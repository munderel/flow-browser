"""
Upload an image to an existing project (set FLOW_PROJECT_ID env var), expect it
to appear as a new tile in the grid.
"""

import asyncio
import os
from pathlib import Path

from flow_browser import FlowBrowser
from flow_browser.utils.logging import logger

PROJECT_ID = os.environ.get("FLOW_PROJECT_ID")
if not PROJECT_ID:
    raise SystemExit("Set FLOW_PROJECT_ID to a Flow project UUID before running.")
REF = Path(__file__).resolve().parent.parent / "inspections" / "ad_nano_banana_pro_v0.png"


async def main() -> None:
    async with FlowBrowser(headless=False, slow_mo=80) as flow:
        await flow.ensure_signed_in()
        await flow.open_project(PROJECT_ID)
        page = flow.page
        await page.wait_for_timeout(2500)

        # Wait until at least one tile is rendered before recording baseline.
        await page.wait_for_function(
            "() => document.querySelectorAll('[data-known-size] [data-tile-id]').length > 0",
            timeout=15000,
        )
        await page.wait_for_timeout(2000)  # let the list fully settle
        existing_ids = await page.evaluate(
            "() => Array.from(document.querySelectorAll('[data-known-size] [data-tile-id]'))"
            ".map(e => e.getAttribute('data-tile-id'))"
        )
        logger.info(f"tiles before upload: {len(existing_ids)}")

        await page.locator("input[type='file']").first.set_input_files(str(REF))
        logger.info("uploaded; waiting for new tile")

        # Poll for a new tile.
        import time

        existing_set = set(existing_ids)
        new_id = None
        deadline = time.monotonic() + 60
        while time.monotonic() < deadline:
            current_ids = await page.evaluate(
                "() => Array.from(document.querySelectorAll('[data-known-size] [data-tile-id]'))"
                ".map(e => e.getAttribute('data-tile-id'))"
            )
            diff = set(current_ids) - existing_set
            if diff:
                new_id = next(iter(diff))
                logger.info(f"new tile detected: {new_id}")
                break
            await page.wait_for_timeout(1000)
        else:
            logger.error("no new tile after 60s")
            return

        info = await page.evaluate(
            f"""() => {{
                const t = document.querySelector("[data-tile-id='{new_id}']");
                if (!t) return null;
                const img = t.querySelector('img');
                return {{
                    img_src: img ? img.getAttribute('src') : null,
                    img_alt: img ? img.getAttribute('alt') : null,
                }};
            }}"""
        )
        logger.info(f"new tile detail: {info}")


if __name__ == "__main__":
    asyncio.run(main())
