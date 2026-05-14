"""
List all Flow projects on this account.

Usage:
    python examples/manage_projects.py
"""

import asyncio

from flow_browser import FlowBrowser


async def main() -> None:
    async with FlowBrowser(headless=False) as flow:
        await flow.ensure_signed_in()
        projects = await flow.list_projects()
        if not projects:
            print("(no projects yet)")
            return
        for p in projects:
            print(f"  {p.id}  {p.name}")
            if p.url:
                print(f"    {p.url}")


if __name__ == "__main__":
    asyncio.run(main())
