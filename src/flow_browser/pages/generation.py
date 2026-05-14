from __future__ import annotations

import asyncio
import time
from pathlib import Path

from playwright.async_api import Page

from flow_browser import locators as L
from flow_browser.constants import DEFAULT_TIMEOUT_S, FLOW_URL, GENERATION_TIMEOUT_S
from flow_browser.exceptions import JobTimeoutError
from flow_browser.types import AspectRatio, Model, Scene, Video
from flow_browser.utils.logging import logger
from flow_browser.utils.waits import wait_for_locator


class GenerationPage:
    """Generate dialog inside a project. Handles both video (Veo) and image (Imagen) tiles."""

    def __init__(self, page: Page) -> None:
        self.page = page

    async def _current_tile_ids(self) -> set[str]:
        """Return the set of data-tile-id values currently in the virtuoso list."""
        ids: list[str] = await self.page.evaluate(
            "() => Array.from(document.querySelectorAll("
            "'[data-known-size] [data-tile-id]'"
            ")).map(e => e.getAttribute('data-tile-id'))"
        )
        return {i for i in ids if i}

    async def configure(
        self,
        *,
        model_name_pattern: str | None = None,
        output_kind: str | None = None,
        aspect_ratio: str | None = None,
        quantity: int | None = None,
        duration_s: int | None = None,
    ) -> None:
        """Open the settings popover and apply any subset of model / output kind /
        aspect ratio / quantity / duration. Each is optional and skipped silently
        if not provided or if its tab is missing in the current Flow build.

        duration_s is only meaningful when output_kind='video' (4 / 6 / 8 seconds
        for Veo 3.1 variants)."""
        if not any([model_name_pattern, output_kind, aspect_ratio, quantity, duration_s]):
            return

        picker = L.model_picker(self.page)
        if await picker.count() == 0:
            logger.warning("no model picker visible")
            return
        await picker.click()
        await self.page.wait_for_timeout(600)

        if output_kind:
            tab = L.output_kind_tab(self.page, output_kind)
            if await tab.count() > 0:
                await tab.first.click()
                await self.page.wait_for_timeout(300)
                logger.info(f"output kind set to {output_kind!r}")

        if aspect_ratio:
            ar_tab = L.aspect_ratio_tab(self.page, aspect_ratio)
            if await ar_tab.count() > 0:
                await ar_tab.first.click()
                await self.page.wait_for_timeout(200)
                logger.info(f"aspect ratio set to {aspect_ratio!r}")

        if quantity is not None:
            q_tab = L.quantity_tab(self.page, quantity)
            if await q_tab.count() > 0:
                await q_tab.first.click()
                await self.page.wait_for_timeout(200)
                logger.info(f"quantity set to x{quantity}")
            else:
                logger.warning(f"quantity tab x{quantity} not found")

        if duration_s is not None:
            d_tab = L.duration_tab(self.page, duration_s)
            if await d_tab.count() > 0:
                await d_tab.first.click()
                await self.page.wait_for_timeout(200)
                logger.info(f"duration set to {duration_s}s")
            else:
                logger.warning(f"duration tab {duration_s}s not found (Image mode?)")

        if model_name_pattern:
            trigger = L.model_dropdown_trigger(self.page)
            if await trigger.count() == 0:
                logger.warning("model dropdown trigger not found in popover")
            else:
                await trigger.click()
                await self.page.wait_for_timeout(600)
                item = L.model_menu_item(self.page, model_name_pattern)
                if await item.count() == 0:
                    logger.warning(f"model not found in dropdown: {model_name_pattern!r}")
                else:
                    await item.first.click()
                    logger.info(f"selected model matching {model_name_pattern!r}")

        # Close the popover so it doesn't block the prompt area / Create button.
        await self.page.wait_for_timeout(300)
        await self.page.keyboard.press("Escape")
        await self.page.wait_for_timeout(200)

    # Back-compat alias.
    select_model = configure

    async def submit(
        self,
        prompt: str,
        *,
        model: Model | None = None,
        model_name_pattern: str | None = None,
        output_kind: str | None = None,
        aspect_ratio: AspectRatio | str | None = None,
        quantity: int = 1,
        duration_s: int | None = None,
        image: str | Path | None = None,
        timeout_s: float = GENERATION_TIMEOUT_S,
    ) -> list[Video]:
        """Submit a generation. Returns one Video per produced variant
        (len == 1 for quantity=1, up to 4 for quantity=4)."""
        if not 1 <= quantity <= 4:
            raise ValueError(f"quantity must be 1..4, got {quantity}")

        await wait_for_locator(
            L.prompt_textarea(self.page),
            timeout_s=DEFAULT_TIMEOUT_S,
            what="prompt textarea",
        )

        ar_str: str | None = None
        if aspect_ratio is not None:
            ar_str = aspect_ratio.value if isinstance(aspect_ratio, AspectRatio) else aspect_ratio

        resolved_model = model_name_pattern
        resolved_kind = output_kind
        if resolved_model is None and model is not None:
            resolved_model = model.value.replace("-", r".?")
            if resolved_kind is None and "veo" in model.value:
                resolved_kind = "video"

        await self.configure(
            model_name_pattern=resolved_model,
            output_kind=resolved_kind,
            aspect_ratio=ar_str,
            quantity=quantity,
            duration_s=duration_s,
        )

        # Slate editor: click to focus, then type. fill() may not work on contenteditable.
        editor = L.prompt_textarea(self.page)
        await editor.click()
        # Clear via keyboard then type.
        await self.page.keyboard.press("Control+A")
        await self.page.keyboard.press("Delete")
        await editor.type(prompt, delay=10)

        # Aspect ratio / duration: best-effort, skip silently if missing.
        # (These open as a popover when clicked; selecting from them needs a UI walk.)

        if image is not None:
            file_input = self.page.locator("input[type='file']").first
            await file_input.set_input_files(str(image))

        existing_ids = await self._current_tile_ids()
        logger.debug(f"existing tile count: {len(existing_ids)}")

        await L.generate_button(self.page).click()
        logger.info(f"clicked Create; waiting for {quantity} new tile(s)")

        # Wait for `quantity` new tile ids to show up.
        deadline = time.monotonic() + timeout_s
        new_ids: list[str] = []
        while time.monotonic() < deadline:
            current = await self._current_tile_ids()
            diff = list(current - existing_ids)
            if len(diff) >= quantity:
                new_ids = diff[:quantity]
                break
            await asyncio.sleep(1.0)
        if len(new_ids) < quantity:
            raise JobTimeoutError(
                f"only {len(new_ids)}/{quantity} new tiles appeared within {timeout_s}s"
            )
        logger.info(f"new tiles appeared: {new_ids}")

        project_id = self.page.url.rstrip("/").rsplit("/", 1)[-1].split("?")[0]

        videos: list[Video] = []
        for tile_id in new_ids:
            new_card = self.page.locator(f"[data-known-size] [data-tile-id='{tile_id}']").first
            media = new_card.locator("video, img[alt='Generated image']").first
            remaining_ms = max(1000, int((deadline - time.monotonic()) * 1000))
            try:
                await media.wait_for(state="attached", timeout=remaining_ms)
            except Exception as e:
                raise JobTimeoutError(f"tile {tile_id} did not produce a video/img: {e}") from e
            src = await media.get_attribute("src")
            if src and src.startswith("/"):
                src = "https://labs.google" + src
            videos.append(
                Video(
                    scene_id=tile_id,
                    project_id=project_id,
                    url=src,
                    prompt=prompt,
                    model_name=model,
                )
            )

        return videos

    async def get_scene(self, index: int) -> Scene:
        cards = L.scene_cards(self.page)
        card = cards.nth(index)
        scene_id = await card.get_attribute("data-tile-id") or f"scene-{index}"
        project_id = self.page.url.rstrip("/").rsplit("/", 1)[-1]
        media = L.scene_video_element(card)
        video_url = await media.get_attribute("src") if await media.count() > 0 else None
        return Scene(id=scene_id, index=index, project_id=project_id, video_url=video_url)
