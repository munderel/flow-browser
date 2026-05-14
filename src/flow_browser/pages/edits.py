from __future__ import annotations

import asyncio
import time

from playwright.async_api import Page

from flow_browser import locators as L
from flow_browser.constants import DEFAULT_TIMEOUT_S, GENERATION_TIMEOUT_S
from flow_browser.exceptions import JobTimeoutError, UITimeoutError
from flow_browser.types import Video
from flow_browser.utils.logging import logger
from flow_browser.utils.waits import wait_for_locator


class EditsPage:
    """Tile-level edits: extend, insert object, remove object.

    Flow's edit UX:
      1. Click a tile in the grid -> opens detail view with toolbar
         (Extend / Insert / Remove / Reuse prompt / Download / Back / ...)
      2. Click the action button -> opens a prompt panel (Slate editor + Create)
      3. Fill prompt + click Create -> new tile appears in the project grid
      4. Click Back to return to grid
    """

    def __init__(self, page: Page) -> None:
        self.page = page

    async def _current_tile_ids(self) -> set[str]:
        ids: list[str] = await self.page.evaluate(
            "() => Array.from(document.querySelectorAll("
            "'[data-known-size] [data-tile-id]'"
            ")).map(e => e.getAttribute('data-tile-id'))"
        )
        return {i for i in ids if i}

    async def _open_tile_detail(self, scene_index_or_id: int | str) -> None:
        """Click into a tile's detail view by 0-based index or by data-tile-id."""
        if isinstance(scene_index_or_id, int):
            tile = L.scene_cards(self.page).nth(scene_index_or_id)
        else:
            tile = self.page.locator(
                f"[data-known-size] [data-tile-id='{scene_index_or_id}']"
            ).first
        await tile.scroll_into_view_if_needed()
        await tile.click()
        # Detail view is open when one of these toolbar buttons appears.
        await wait_for_locator(
            L.detail_extend_button(self.page),
            timeout_s=DEFAULT_TIMEOUT_S,
            what="tile detail view",
        )

    async def close_detail(self) -> None:
        """Click Back to return to the project grid."""
        back = L.detail_back_button(self.page)
        if await back.count() > 0:
            await back.first.click()
            await self.page.wait_for_timeout(500)

    async def _run_edit_action(
        self,
        action_button: callable,
        prompt: str | None,
        *,
        action_name: str,
        timeout_s: float = GENERATION_TIMEOUT_S,
    ) -> Video:
        """Common pipeline: click action button, fill prompt if any, click Create,
        wait for a new tile to appear, capture its url."""
        existing = await self._current_tile_ids()
        logger.debug(f"existing tile ids before {action_name}: {len(existing)}")

        btn = action_button(self.page)
        await wait_for_locator(btn, timeout_s=DEFAULT_TIMEOUT_S, what=f"{action_name} button")
        await btn.first.click()
        await self.page.wait_for_timeout(800)

        if prompt:
            editor = L.prompt_textarea(self.page)
            try:
                await wait_for_locator(editor, timeout_s=15.0, what=f"{action_name} prompt editor")
                await editor.click()
                await self.page.keyboard.press("Control+A")
                await self.page.keyboard.press("Delete")
                await editor.type(prompt, delay=10)
            except UITimeoutError:
                logger.warning(f"no prompt editor visible for {action_name}; submitting without text")

        await L.generate_button(self.page).click()
        logger.info(f"clicked Create for {action_name}; waiting for new tile")

        deadline = time.monotonic() + timeout_s
        new_id: str | None = None
        while time.monotonic() < deadline:
            current = await self._current_tile_ids()
            diff = current - existing
            if diff:
                new_id = next(iter(diff))
                break
            await asyncio.sleep(1.0)
        if new_id is None:
            raise JobTimeoutError(f"no new tile after {action_name} within {timeout_s}s")
        logger.info(f"{action_name} produced tile {new_id}")

        new_card = self.page.locator(f"[data-known-size] [data-tile-id='{new_id}']").first
        media = new_card.locator("video, img[alt='Generated image']").first
        remaining_ms = max(1000, int((deadline - time.monotonic()) * 1000))
        await media.wait_for(state="attached", timeout=remaining_ms)
        src = await media.get_attribute("src")
        if src and src.startswith("/"):
            src = "https://labs.google" + src

        project_id = self.page.url.rstrip("/").rsplit("/", 1)[-1].split("?")[0]
        return Video(
            scene_id=new_id,
            project_id=project_id,
            url=src,
            prompt=prompt,
        )

    async def extend(
        self,
        scene_index_or_id: int | str,
        prompt: str | None = None,
        seconds: int | None = None,
    ) -> Video:
        """Extend a video tile. Optional `prompt` is the continuation prompt;
        leave None to let Flow auto-continue. `seconds` is not always exposed
        in the extend dialog — best-effort, ignored if no duration tab appears."""
        await self._open_tile_detail(scene_index_or_id)
        # Open Extend panel.
        await L.detail_extend_button(self.page).first.click()
        await self.page.wait_for_timeout(800)
        if seconds is not None:
            d_tab = L.duration_tab(self.page, seconds)
            if await d_tab.count() > 0:
                await d_tab.first.click()
                await self.page.wait_for_timeout(200)
        # Fill prompt + click Create + wait for new tile.
        # The Extend button has already been clicked; the prompt + create flow
        # is shared with _run_edit_action — but it would re-click Extend. Inline.
        existing = await self._current_tile_ids()
        if prompt:
            editor = L.prompt_textarea(self.page)
            try:
                await wait_for_locator(editor, timeout_s=15.0, what="extend prompt editor")
                await editor.click()
                await self.page.keyboard.press("Control+A")
                await self.page.keyboard.press("Delete")
                await editor.type(prompt, delay=10)
            except UITimeoutError:
                logger.warning("no prompt editor for extend; submitting without text")

        await L.generate_button(self.page).click()
        logger.info("clicked Create for extend; waiting for new tile")

        deadline = time.monotonic() + GENERATION_TIMEOUT_S
        new_id: str | None = None
        while time.monotonic() < deadline:
            current = await self._current_tile_ids()
            diff = current - existing
            if diff:
                new_id = next(iter(diff))
                break
            await asyncio.sleep(1.0)
        if new_id is None:
            raise JobTimeoutError("no new tile after extend")
        new_card = self.page.locator(f"[data-known-size] [data-tile-id='{new_id}']").first
        media = new_card.locator("video, img[alt='Generated image']").first
        remaining_ms = max(1000, int((deadline - time.monotonic()) * 1000))
        await media.wait_for(state="attached", timeout=remaining_ms)
        src = await media.get_attribute("src")
        if src and src.startswith("/"):
            src = "https://labs.google" + src
        project_id = self.page.url.rstrip("/").rsplit("/", 1)[-1].split("?")[0]
        return Video(scene_id=new_id, project_id=project_id, url=src, prompt=prompt)

    async def insert_object(self, scene_index_or_id: int | str, prompt: str) -> Video:
        await self._open_tile_detail(scene_index_or_id)
        return await self._run_edit_action(L.detail_insert_button, prompt, action_name="insert")

    async def remove_object(self, scene_index_or_id: int | str, prompt: str | None = None) -> Video:
        await self._open_tile_detail(scene_index_or_id)
        return await self._run_edit_action(L.detail_remove_button, prompt, action_name="remove")
