"""
Open an existing project and extend its first scene by 4 seconds.

Usage:
    python examples/extend_scene.py "<project name or id>" "more action continues..."
"""

import asyncio
import sys

from flow_browser import FlowBrowser


async def main() -> None:
    if len(sys.argv) < 3:
        print("usage: extend_scene.py <project> <prompt>")
        sys.exit(1)
    project, prompt = sys.argv[1], " ".join(sys.argv[2:])
    async with FlowBrowser(headless=False) as flow:
        await flow.ensure_signed_in()
        await flow.open_project(project)
        video = await flow.extend_scene(scene_index=0, prompt=prompt, seconds=4)
        out = await video.download("out_extended.mp4")
        print(f"saved: {out}")


if __name__ == "__main__":
    asyncio.run(main())
