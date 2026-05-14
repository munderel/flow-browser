"""Create a fresh project then immediately delete it. Also cleans up
the stray project left by probe_create_project_v2 if it still exists."""

import asyncio

from flow_browser import FlowBrowser
from flow_browser.utils.logging import logger


STRAY_FROM_PROBE = "c73ee528-694d-4271-b5ea-40e14836dc19"


async def main() -> None:
    async with FlowBrowser(headless=False, slow_mo=80) as flow:
        await flow.ensure_signed_in()

        # 1. Clean up the stray project from the earlier probe, if it's still around.
        projects = await flow.list_projects()
        ids = {p.id for p in projects}
        if STRAY_FROM_PROBE in ids:
            logger.info(f"deleting stray probe project {STRAY_FROM_PROBE}")
            await flow.delete_project(STRAY_FROM_PROBE)
        else:
            logger.info(f"stray probe project {STRAY_FROM_PROBE} already gone")

        # 2. Create -> verify it appears in list -> delete -> verify it's gone.
        new = await flow.create_project("flow-api smoke test")
        logger.info(f"created: {new.id}")

        after_create = await flow.list_projects()
        assert any(p.id == new.id for p in after_create), \
            f"created project {new.id} not found in list"
        logger.info(f"verified in list ({len(after_create)} total projects)")

        await flow.delete_project(new)
        logger.info("deletion call returned")

        after_delete = await flow.list_projects()
        assert all(p.id != new.id for p in after_delete), \
            f"deleted project {new.id} still in list"
        logger.info(f"verified gone ({len(after_delete)} total projects)")

        logger.info("create + delete: PASS")


if __name__ == "__main__":
    asyncio.run(main())
