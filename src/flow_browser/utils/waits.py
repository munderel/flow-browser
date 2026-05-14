from __future__ import annotations

import asyncio
import time

from playwright.async_api import Locator, Page, TimeoutError as PWTimeout

from flow_browser.constants import GENERATION_TIMEOUT_S
from flow_browser.exceptions import JobTimeoutError, UITimeoutError
from flow_browser.locators import scene_card_busy, scene_video_element
from flow_browser.utils.logging import logger


async def wait_for_locator(locator: Locator, timeout_s: float, *, what: str) -> None:
    try:
        await locator.wait_for(state="visible", timeout=int(timeout_s * 1000))
    except PWTimeout as e:
        raise UITimeoutError(f"timed out waiting for {what} after {timeout_s}s") from e


async def wait_for_scene_ready(
    scene_card: Locator,
    *,
    timeout_s: float = GENERATION_TIMEOUT_S,
    poll_interval_s: float = 1.5,
) -> None:
    """Wait until a scene card stops showing a busy/progress indicator and a <video> exists."""
    deadline = time.monotonic() + timeout_s
    while time.monotonic() < deadline:
        busy_count = await scene_card_busy(scene_card).count()
        video_count = await scene_video_element(scene_card).count()
        if busy_count == 0 and video_count > 0:
            logger.debug("scene ready")
            return
        await asyncio.sleep(poll_interval_s)
    raise JobTimeoutError(f"scene did not finish rendering within {timeout_s}s")


async def capture_video_url(
    page: Page,
    *,
    timeout_s: float = GENERATION_TIMEOUT_S,
    url_substring: str = ".mp4",
) -> str:
    """Race condition-free capture of the rendered video URL by watching network responses."""
    try:
        async with page.expect_response(
            lambda r: url_substring in r.url and r.status == 200,
            timeout=int(timeout_s * 1000),
        ) as resp_info:
            pass
        response = await resp_info.value
        return response.url
    except PWTimeout as e:
        raise JobTimeoutError(f"no video response within {timeout_s}s") from e
