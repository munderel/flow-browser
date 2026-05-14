"""Generate a 4-second Veo 3.1 Fast clip — shortest available."""

import asyncio
from pathlib import Path

from flow_browser import FlowBrowser
from flow_browser.utils.logging import logger


PROMPT = (
    "Cinematic close-up of a sleek teal teeth-whitening device powering on, "
    "soft blue LED glow, marble bathroom counter, shallow depth of field, "
    "professional product film"
)
OUT = Path(__file__).resolve().parent.parent / "inspections"


async def main() -> None:
    async with FlowBrowser(headless=False, slow_mo=50) as flow:
        await flow.ensure_signed_in()
        projects = await flow.list_projects()
        if not projects:
            logger.error("no projects")
            return
        await flow.open_project(projects[0])

        videos = await flow.project.generation.submit(
            PROMPT,
            model_name_pattern=r"veo\s*3\.1\s*-?\s*fast",
            output_kind="video",
            aspect_ratio="16:9",
            duration_s=4,
            quantity=1,
        )
        for i, v in enumerate(videos):
            logger.info(f"variant {i}: tile={v.scene_id} url={v.url}")
            if v.url:
                v.bind(flow)
                out = await v.download(OUT / f"veo_short_v{i}.mp4")
                logger.info(f"saved: {out}")


if __name__ == "__main__":
    asyncio.run(main())
