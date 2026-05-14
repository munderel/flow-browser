from __future__ import annotations

import asyncio
import time
from pathlib import Path

from playwright.async_api import Page

from flow_browser.constants import DEFAULT_TIMEOUT_S
from flow_browser.exceptions import JobTimeoutError
from flow_browser.types import Ingredient
from flow_browser.utils.logging import logger


class IngredientsPage:
    """Flow does not have a separate ingredients store — every uploaded image
    becomes a regular tile in the project grid. The 'Ingredients' tab in the
    settings popover lets you reference those tiles when generating new media.

    upload() therefore just sets a file on Flow's hidden upload input and waits
    for a new tile to appear."""

    def __init__(self, page: Page) -> None:
        self.page = page

    async def _current_tile_ids(self) -> set[str]:
        ids: list[str] = await self.page.evaluate(
            "() => Array.from(document.querySelectorAll("
            "'[data-known-size] [data-tile-id]'"
            ")).map(e => e.getAttribute('data-tile-id'))"
        )
        return {i for i in ids if i}

    async def upload(self, image: str | Path, *, timeout_s: float = DEFAULT_TIMEOUT_S) -> Ingredient:
        """Upload an image; returns an Ingredient with the new tile's id.

        In a populated project the hidden input[type='file'] is always present.
        In a freshly-created empty project it's lazily inserted only after the
        user opens the 'Add Media' affordance — we click that first if needed.
        """
        import re

        page = self.page
        await page.wait_for_timeout(1500)
        existing = await self._current_tile_ids()
        logger.debug(f"tiles before upload: {len(existing)}")

        # Poll briefly — Flow lazily renders the file input after navigation.
        for attempt in range(10):
            file_input = page.locator("input[type='file']")
            if await file_input.count() > 0:
                break
            await page.wait_for_timeout(1000)
        if await file_input.count() > 0:
            await file_input.first.set_input_files(str(image))
        else:
            logger.debug("no file input in DOM; using expect_file_chooser via 'Add Media'")
            add_media = page.get_by_role("button", name=re.compile(r"add media", re.I)).first
            if await add_media.count() == 0:
                # Diagnostic dump before failing.
                btns = await page.evaluate(
                    "() => Array.from(document.querySelectorAll('button')).map(b => (b.innerText || '').trim()).filter(Boolean).slice(0, 30)"
                )
                logger.error(f"visible buttons (first 30): {btns}")
                raise RuntimeError("no input[type='file'] and no 'Add Media' button")
            async with page.expect_file_chooser(timeout=int(timeout_s * 1000)) as fc_info:
                await add_media.click()
                # Some builds open a menu first; try clicking 'Upload' item if it appears.
                await page.wait_for_timeout(400)
                upload_choice = page.get_by_role(
                    "menuitem", name=re.compile(r"upload|device|computer|from file", re.I)
                )
                if await upload_choice.count() > 0:
                    await upload_choice.first.click()
            chooser = await fc_info.value
            await chooser.set_files(str(image))

        deadline = time.monotonic() + timeout_s
        while time.monotonic() < deadline:
            current = await self._current_tile_ids()
            new = current - existing
            if new:
                tile_id = next(iter(new))
                name = Path(image).stem
                logger.info(f"uploaded {image} as tile {tile_id}")
                return Ingredient(id=tile_id, name=name)
            await asyncio.sleep(0.7)
        raise JobTimeoutError(f"no new tile appeared within {timeout_s}s after upload")

    async def list(self) -> list[Ingredient]:
        """List every uploaded/generated tile in the current project."""
        ids = await self._current_tile_ids()
        return [Ingredient(id=i) for i in ids]
