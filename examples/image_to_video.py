"""
Generate a video from a starting image + prompt.

Usage:
    python examples/image_to_video.py path/to/image.png "the goldfish swims out of the cup"
"""

import asyncio
import sys

from flow_browser import FlowBrowser, Model


async def main() -> None:
    if len(sys.argv) < 3:
        print("usage: image_to_video.py <image> <prompt>")
        sys.exit(1)
    image, prompt = sys.argv[1], " ".join(sys.argv[2:])
    async with FlowBrowser(headless=False) as flow:
        await flow.ensure_signed_in()
        videos = await flow.generate_video(prompt, model=Model.VEO_3_1, image=image)
        out = await videos[0].download("out.mp4")
        print(f"saved: {out}")


if __name__ == "__main__":
    asyncio.run(main())
