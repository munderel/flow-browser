"""
One-time sign-in.

Run this once. A Chrome window opens at labs.google/fx/tools/flow. Sign into
Google there (including 2FA / device trust if prompted). When you see the Flow
home page logged in, come back to this terminal and press Enter.

The session is stored under ~/.flow-browser/profile and reused by every
subsequent script run.
"""

import asyncio

from flow_browser import FlowBrowser
from flow_browser.constants import FLOW_URL


async def main() -> None:
    async with FlowBrowser(headless=False, slow_mo=50) as flow:
        await flow.page.goto(FLOW_URL)
        print()
        print("=" * 60)
        print(" Sign into Google in the browser window that just opened.")
        print(" When you see the Flow home page logged in, press Enter here.")
        print("=" * 60)
        print()
        try:
            await asyncio.get_running_loop().run_in_executor(None, input)
        except (KeyboardInterrupt, EOFError):
            print("aborted")
            return

        try:
            await flow.ensure_signed_in()
        except Exception as e:
            print(f"Still not signed in: {e}")
            return
        print("Signed in. Profile saved.")


if __name__ == "__main__":
    asyncio.run(main())
