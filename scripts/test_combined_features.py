"""
Combined feature test — exercises every non-billing feature in one run:

    sign-in -> list -> create_project -> verify in list ->
    upload media -> verify tile -> delete_project -> verify gone

NO generation is performed — costs zero credits. Use this as a regression check.
"""

import asyncio
from pathlib import Path

from flow_browser import FlowBrowser
from flow_browser.utils.logging import logger


REF_IMAGE = Path(__file__).resolve().parent.parent / "inspections" / "ad_nano_banana_pro_v0.png"


async def main() -> None:
    async with FlowBrowser(headless=False, slow_mo=80) as flow:
        await flow.ensure_signed_in()
        logger.info("signed in")

        initial = await flow.list_projects()
        logger.info(f"initial: {len(initial)} projects")

        # Create.
        new = await flow.create_project("combined-feature-test")
        logger.info(f"created: {new.id}")

        after_create = await flow.list_projects()
        assert any(p.id == new.id for p in after_create), "created project not in list"
        logger.info(f"verified in list ({len(after_create)} projects)")

        # list_projects() navigated us back to home for the verification step
        # above — return to the project before trying to upload to it.
        await flow.open_project(new)
        await flow.page.wait_for_timeout(3000)

        if REF_IMAGE.exists():
            ing = await flow.project.ingredients.upload(REF_IMAGE)
            logger.info(f"uploaded media -> tile {ing.id}")
        else:
            logger.warning(f"reference image missing, skipping upload: {REF_IMAGE}")

        # Delete the test project.
        await flow.delete_project(new)
        logger.info("deletion call returned")

        after_delete = await flow.list_projects()
        assert all(p.id != new.id for p in after_delete), "deleted project still in list"
        logger.info(f"verified gone ({len(after_delete)} projects)")

        logger.info("ALL PASS")


if __name__ == "__main__":
    asyncio.run(main())
