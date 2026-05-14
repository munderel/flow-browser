from __future__ import annotations

from pathlib import Path

from playwright.async_api import BrowserContext, Locator, Page, TimeoutError as PWTimeout

from flow_browser.constants import DOWNLOAD_TIMEOUT_S
from flow_browser.exceptions import JobTimeoutError
from flow_browser.utils.logging import logger


async def download_via_button(
    page: Page,
    download_button: Locator,
    out_path: str | Path,
    *,
    timeout_s: float = DOWNLOAD_TIMEOUT_S,
) -> Path:
    """Click an in-UI download button and save the resulting download."""
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        async with page.expect_download(timeout=int(timeout_s * 1000)) as dl_info:
            await download_button.click()
        download = await dl_info.value
        await download.save_as(str(out_path))
        logger.info(f"saved download to {out_path}")
        return out_path
    except PWTimeout as e:
        raise JobTimeoutError(f"download did not start within {timeout_s}s") from e


async def download_via_url(
    context: BrowserContext,
    url: str,
    out_path: str | Path,
) -> Path:
    """Re-fetch an asset URL using the browser context's auth cookies."""
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    response = await context.request.get(url)
    if not response.ok:
        raise RuntimeError(f"download failed: HTTP {response.status} for {url}")
    out_path.write_bytes(await response.body())
    logger.info(f"saved download to {out_path}")
    return out_path
