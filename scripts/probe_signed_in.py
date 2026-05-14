"""
Diagnostic: open Flow with the saved profile and dump the DOM so we can pick
a real "signed in" indicator. Bypasses ensure_signed_in().

Outputs:
    inspections/home_raw.html
    inspections/home_raw.a11y.json
    inspections/home_probe.txt    (candidate signed-in markers)
"""

import asyncio
import json
import re
from pathlib import Path

from flow_browser import FlowBrowser
from flow_browser.constants import FLOW_URL


OUT = Path(__file__).resolve().parent.parent / "inspections"


async def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    async with FlowBrowser(headless=False, slow_mo=50) as flow:
        page = flow.page
        await page.goto(FLOW_URL, wait_until="domcontentloaded")
        await page.wait_for_timeout(5000)

        html = await page.content()
        (OUT / "home_raw.html").write_text(html, encoding="utf-8")

        # Probe a variety of likely signed-in markers.
        probes: dict[str, str | int] = {}
        candidates = [
            ("button-google-account", lambda p: p.get_by_role("button", name=re.compile(r"google account", re.I))),
            ("button-account-menu",   lambda p: p.get_by_role("button", name=re.compile(r"account", re.I))),
            ("button-with-avatar-img",lambda p: p.locator("button:has(img[alt*='avatar' i])")),
            ("img-alt-account",       lambda p: p.locator("img[alt*='account' i]")),
            ("img-googleusercontent", lambda p: p.locator("img[src*='googleusercontent' i]")),
            ("link-sign-in",          lambda p: p.get_by_role("link", name=re.compile(r"sign ?in", re.I))),
            ("button-sign-in",        lambda p: p.get_by_role("button", name=re.compile(r"sign ?in", re.I))),
            ("button-new-project",    lambda p: p.get_by_role("button", name=re.compile(r"new project", re.I))),
            ("button-create",         lambda p: p.get_by_role("button", name=re.compile(r"^create", re.I))),
            ("text-credits",          lambda p: p.get_by_text(re.compile(r"\d+\s+credits?", re.I))),
            ("any-aria-label-acct",   lambda p: p.locator("[aria-label*='account' i]")),
            ("data-testid-user",      lambda p: p.locator("[data-testid*='user' i]")),
            ("header-img-rounded",    lambda p: p.locator("header img, nav img").first),
        ]
        for name, fn in candidates:
            try:
                probes[name] = await fn(page).count()
            except Exception as e:
                probes[name] = f"err: {e}"  # type: ignore[assignment]

        probes["__url__"] = page.url
        probes["__title__"] = await page.title()

        (OUT / "home_probe.txt").write_text(
            json.dumps(probes, indent=2), encoding="utf-8"
        )
        print(json.dumps(probes, indent=2))
        print(f"\nDumps in: {OUT}")


if __name__ == "__main__":
    asyncio.run(main())
