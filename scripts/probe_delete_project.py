"""Probe: hover/find delete UI for a project card on home."""

import asyncio
from flow_browser import FlowBrowser, locators as L
from flow_browser.constants import FLOW_URL


async def main() -> None:
    async with FlowBrowser(headless=False, slow_mo=80) as flow:
        await flow.ensure_signed_in()
        page = flow.page
        await page.goto(FLOW_URL, wait_until="domcontentloaded")
        await page.wait_for_timeout(2500)

        # First card (newest).
        card = L.project_card(page).first
        href = await card.get_attribute("href")
        print(f"first card href: {href}")

        # Hover to reveal action icons.
        await card.hover()
        await page.wait_for_timeout(500)

        # Look for delete button NEAR the card (in same parent).
        # Each card is wrapped in a div that also contains an Edit + Delete button
        # (we saw these earlier as sr-only "Edit project" / "Delete project" spans).
        items = await page.evaluate(
            """() => {
                const out = [];
                document.querySelectorAll('button, [role=button]').forEach(el => {
                    const r = el.getBoundingClientRect();
                    if (r.width === 0 && r.height === 0) return;
                    const t = (el.innerText || el.ariaLabel || '').trim();
                    if (t.toLowerCase().includes('delete') || t.toLowerCase().includes('edit project')) {
                        out.push({text: t, x: r.x, y: r.y});
                    }
                });
                return out;
            }"""
        )
        print(f'matching buttons: {len(items)}')
        for it in items[:10]:
            print(f'  {it!r}')


if __name__ == "__main__":
    asyncio.run(main())
