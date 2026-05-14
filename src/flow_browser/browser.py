from __future__ import annotations

from pathlib import Path

from playwright.async_api import BrowserContext, Playwright, async_playwright

from flow_browser.constants import DEFAULT_LOCALE, DEFAULT_USER_DATA_DIR, DEFAULT_VIEWPORT
from flow_browser.utils.logging import logger


_STEALTH_INIT_SCRIPT = """
// Modest hardening — real browsing is the actual defense.
Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
"""


class BrowserSession:
    """Wraps Playwright lifecycle + a persistent BrowserContext.

    One profile dir == one Google account. The profile is created on first run
    and reused on every subsequent run, so the user signs in once.
    """

    def __init__(
        self,
        user_data_dir: str | Path | None = None,
        *,
        headless: bool = False,
        executable_path: str | Path | None = None,
        slow_mo: int = 0,
        viewport: dict[str, int] | None = None,
        locale: str = DEFAULT_LOCALE,
        timezone_id: str | None = None,
    ) -> None:
        self.user_data_dir = Path(user_data_dir) if user_data_dir else DEFAULT_USER_DATA_DIR
        self.headless = headless
        self.executable_path = str(executable_path) if executable_path else None
        self.slow_mo = slow_mo
        self.viewport = viewport or DEFAULT_VIEWPORT
        self.locale = locale
        self.timezone_id = timezone_id

        self._pw: Playwright | None = None
        self._context: BrowserContext | None = None

    async def start(self) -> BrowserContext:
        self.user_data_dir.mkdir(parents=True, exist_ok=True)
        logger.debug(f"launching Chromium with profile {self.user_data_dir}")
        self._pw = await async_playwright().start()
        kwargs: dict = {
            "user_data_dir": str(self.user_data_dir),
            "headless": self.headless,
            "slow_mo": self.slow_mo,
            "viewport": self.viewport,
            "locale": self.locale,
            "args": ["--disable-blink-features=AutomationControlled"],
        }
        if self.executable_path:
            kwargs["executable_path"] = self.executable_path
        if self.timezone_id:
            kwargs["timezone_id"] = self.timezone_id

        self._context = await self._pw.chromium.launch_persistent_context(**kwargs)
        await self._context.add_init_script(_STEALTH_INIT_SCRIPT)
        return self._context

    async def stop(self) -> None:
        if self._context is not None:
            await self._context.close()
            self._context = None
        if self._pw is not None:
            await self._pw.stop()
            self._pw = None

    @property
    def context(self) -> BrowserContext:
        if self._context is None:
            raise RuntimeError("BrowserSession not started; call start() first")
        return self._context
