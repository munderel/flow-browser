"""Probe ingredient upload: set a file on input[type=file], dump what shows up."""

import asyncio
from pathlib import Path

from flow_browser import FlowBrowser
from flow_browser.utils.logging import logger


REF_IMAGE = Path(__file__).resolve().parent.parent / "inspections" / "ad_nano_banana_pro_v0.png"


async def main() -> None:
    async with FlowBrowser(headless=False, slow_mo=80) as flow:
        await flow.ensure_signed_in()
        projects = await flow.list_projects()
        if not projects:
            return
        await flow.open_project(projects[0])
        page = flow.page
        await page.wait_for_timeout(2000)

        # Snapshot ingredient state before.
        before = await page.evaluate(
            """() => ({
                file_inputs: document.querySelectorAll("input[type='file']").length,
                data_ingredient: document.querySelectorAll('[data-ingredient-id]').length,
                file_inputs_accept: Array.from(document.querySelectorAll("input[type='file']"))
                    .map(i => i.getAttribute('accept'))
            })"""
        )
        logger.info(f"before: {before}")

        if not REF_IMAGE.exists():
            logger.error(f"reference image not found: {REF_IMAGE}")
            return

        # Just set the file on the input — no panel-opening dance.
        await page.locator("input[type='file']").first.set_input_files(str(REF_IMAGE))
        await page.wait_for_timeout(2500)

        after = await page.evaluate(
            """() => ({
                data_ingredient: document.querySelectorAll('[data-ingredient-id]').length,
                ingredient_ids: Array.from(document.querySelectorAll('[data-ingredient-id]'))
                    .map(e => e.getAttribute('data-ingredient-id')),
            })"""
        )
        logger.info(f"after: {after}")

        # Save page HTML for offline study.
        Path("inspections/after_ingredient_upload.html").write_text(
            await page.content(), encoding="utf-8"
        )


if __name__ == "__main__":
    asyncio.run(main())
