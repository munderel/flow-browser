"""Watch for any new popover/menu after clicking New project."""

import asyncio
from pathlib import Path

from flow_browser import FlowBrowser, locators as L
from flow_browser.constants import FLOW_URL


async def main() -> None:
    async with FlowBrowser(headless=False, slow_mo=80) as flow:
        await flow.ensure_signed_in()
        page = flow.page
        await page.goto(FLOW_URL, wait_until="domcontentloaded")
        await page.wait_for_timeout(2500)

        # Snapshot DOM signatures before click.
        before = await page.evaluate(
            """() => {
                const tags = ['[role=dialog]', '[role=menu]', '[data-radix-popper-content-wrapper]',
                              'iframe', '[role=alertdialog]'];
                const out = {};
                tags.forEach(s => out[s] = document.querySelectorAll(s).length);
                return out;
            }"""
        )
        print('before:', before)

        # Use Locator.first with no race
        btn = L.new_project_button(page).first
        box = await btn.bounding_box()
        print(f'button bbox: {box}')

        await btn.click()
        print('clicked.')

        # Poll for a new container appearing.
        for tick in range(20):
            await page.wait_for_timeout(500)
            now = await page.evaluate(
                """() => {
                    const tags = ['[role=dialog]', '[role=menu]', '[data-radix-popper-content-wrapper]',
                                  'iframe', '[role=alertdialog]'];
                    const out = {};
                    tags.forEach(s => out[s] = document.querySelectorAll(s).length);
                    return out;
                }"""
            )
            url = page.url
            if any(now[k] != before[k] for k in now) or url != FLOW_URL:
                print(f't={tick*500}ms now={now} url={url}')
                break
        else:
            print(f'no change after 10s. url={page.url}')
            # Dump the whole visible text to see if a side panel slid in
            visible_text = await page.evaluate(
                """() => Array.from(document.querySelectorAll('*'))
                    .filter(e => {
                      const r = e.getBoundingClientRect();
                      return r.width > 0 && r.height > 0 && e.children.length === 0;
                    })
                    .map(e => (e.innerText||e.value||'').trim())
                    .filter(t => t && t.length < 40)
                    .slice(0, 80);
                """
            )
            print('visible leaf text:')
            for t in visible_text:
                print('  ', repr(t))

        # Save final HTML for offline diff.
        Path('inspections/after_new_project_v2.html').write_text(
            await page.content(), encoding='utf-8'
        )


if __name__ == "__main__":
    asyncio.run(main())
