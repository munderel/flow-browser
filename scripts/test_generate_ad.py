"""
End-to-end test: open the existing project, switch to Nano Banana Pro,
generate a teeth-whitening ad image, save the artifact.

Usage:
    python scripts/test_generate_ad.py
"""

import asyncio
from pathlib import Path

from flow_browser import FlowBrowser
from flow_browser.utils.logging import logger


AD_PROMPT = (
    "Premium teeth whitening ad: a glowing confident smile next to a sleek modern "
    "teal-and-white whitening kit on a soft pastel background, bright studio lighting, "
    "minimalist composition, copy space at the top for a headline, photorealistic, "
    "professional advertising photography, 4k"
)

OUT_DIR = Path(__file__).resolve().parent.parent / "inspections"


async def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    async with FlowBrowser(headless=False, slow_mo=50) as flow:
        await flow.ensure_signed_in()
        logger.info("signed in")

        projects = await flow.list_projects()
        if not projects:
            logger.error("no existing projects; create one in the UI first")
            return
        target = projects[0]
        logger.info(f"opening project: {target.name} ({target.id})")
        await flow.open_project(target)

        videos = await flow.project.generation.submit(
            AD_PROMPT,
            model_name_pattern=r"nano\s*banana\s*pro",
            output_kind="image",
            aspect_ratio="16:9",
            quantity=2,
        )
        logger.info(f"generated {len(videos)} variant(s)")

        for i, v in enumerate(videos):
            logger.info(f"  variant {i}: tile={v.scene_id} url={v.url}")
            if v.url:
                v.bind(flow)
                out = await v.download(OUT_DIR / f"ad_nano_banana_pro_v{i}.png")
                logger.info(f"  saved: {out}")
            else:
                logger.error(f"  variant {i}: no URL captured")


if __name__ == "__main__":
    asyncio.run(main())
