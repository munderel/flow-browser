"""
Generate a video from a text prompt.

Usage:
    python examples/generate_text_to_video.py "a goldfish in a teacup, cinematic"
"""

import asyncio
import sys

from flow_browser import FlowBrowser, Model


async def main() -> None:
    prompt = " ".join(sys.argv[1:]) or "a goldfish swimming through a teacup, cinematic"
    async with FlowBrowser(headless=False) as flow:
        await flow.ensure_signed_in()
        videos = await flow.generate_video(prompt, model=Model.VEO_3_1_FAST, duration_s=8)
        out = await videos[0].download("out.mp4")
        print(f"saved: {out}")


if __name__ == "__main__":
    asyncio.run(main())
