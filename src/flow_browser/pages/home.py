from __future__ import annotations

from playwright.async_api import Page

from flow_browser import locators as L
from flow_browser.constants import DEFAULT_TIMEOUT_S, FLOW_URL
from flow_browser.exceptions import NotSignedInError
from flow_browser.types import Project
from flow_browser.utils.logging import logger
from flow_browser.utils.waits import wait_for_locator


class HomePage:
    """Project list / dashboard at labs.google/fx/tools/flow."""

    def __init__(self, page: Page) -> None:
        self.page = page

    async def goto(self) -> None:
        logger.debug(f"navigating to {FLOW_URL}")
        await self.page.goto(FLOW_URL, wait_until="domcontentloaded")
        await self._dismiss_cookie_banner()

    async def _dismiss_cookie_banner(self) -> None:
        """Click 'No thanks' on Google's cookies banner if it's showing."""
        reject = L.cookie_banner_reject(self.page)
        try:
            if await reject.count() > 0 and await reject.is_visible():
                await reject.click()
                logger.debug("dismissed cookie banner")
        except Exception as e:
            logger.debug(f"cookie banner dismiss skipped: {e}")

    async def assert_signed_in(self) -> None:
        await self.goto()
        try:
            await wait_for_locator(
                L.signed_in_indicator(self.page),
                timeout_s=10.0,
                what="signed-in indicator",
            )
        except Exception as e:
            raise NotSignedInError(
                "No signed-in Google account in this profile. "
                "Run: python examples/first_run_signin.py"
            ) from e

    async def list_projects(self) -> list[Project]:
        await self.goto()
        await wait_for_locator(
            L.project_card(self.page).first,
            timeout_s=DEFAULT_TIMEOUT_S,
            what="project list",
        )
        # Snapshot in one evaluate to avoid races against the virtualized list.
        rows: list[dict[str, str]] = await self.page.evaluate(
            """() => Array.from(
                document.querySelectorAll("a[href*='/fx/tools/flow/project/']")
            ).map(a => ({
                href: a.getAttribute('href') || '',
                text: (a.innerText || '').trim(),
                title: a.getAttribute('title') || a.getAttribute('aria-label') || ''
            }))"""
        )
        projects: list[Project] = []
        seen: set[str] = set()
        for row in rows:
            href = row["href"]
            if not href:
                continue
            pid = href.rstrip("/").rsplit("/", 1)[-1]
            if pid in seen:
                continue
            seen.add(pid)
            name = (row["text"].splitlines()[0] if row["text"] else "") or row["title"] or pid
            url = href if href.startswith("http") else f"https://labs.google{href}"
            projects.append(Project(id=pid, name=name, url=url))
        return projects

    async def create_project(self, name: str | None = None) -> Project:
        """Click the New project CTA. Flow creates an empty project and navigates
        to its edit URL within ~3 seconds. `name` is currently informational only
        — Flow assigns its own timestamp-based name; rename via UI if needed."""
        await self.goto()
        before_url = self.page.url
        await L.new_project_button(self.page).click()
        await self.page.wait_for_url("**/fx/tools/flow/project/**", timeout=int(DEFAULT_TIMEOUT_S * 1000))
        url = self.page.url
        if url == before_url:
            raise RuntimeError("New project click did not navigate to a project page")
        pid = url.rstrip("/").rsplit("/", 1)[-1].split("?")[0]
        logger.info(f"created project {pid}")
        return Project(id=pid, name=name or pid, url=url)

    async def open_project(self, project: Project | str) -> None:
        if isinstance(project, Project) and project.url:
            await self.page.goto(project.url, wait_until="domcontentloaded")
            return
        pid = project.id if isinstance(project, Project) else project
        await self.page.goto(
            f"https://labs.google/fx/tools/flow/project/{pid}",
            wait_until="domcontentloaded",
        )

    async def delete_project(self, project: Project | str) -> None:
        """Find the project card by id and click its per-card Delete button,
        then confirm in the dialog."""
        await self.goto()
        pid = project.id if isinstance(project, Project) else project

        # Wait for the specific project's anchor to appear (handles virtualization
        # + post-navigation rerender). If the project is far down the list we may
        # need to scroll; for now we only support cards already in the viewport.
        anchor = self.page.locator(f"a[href*='/project/{pid}']").first
        await wait_for_locator(anchor, timeout_s=DEFAULT_TIMEOUT_S, what=f"project card {pid}")
        await anchor.scroll_into_view_if_needed()
        await self.page.wait_for_timeout(300)

        clicked = await self.page.evaluate(
            """(pid) => {
                const a = document.querySelector(`a[href*='/project/${pid}']`);
                if (!a) return 'no-card';
                let node = a;
                for (let i = 0; i < 10 && node; i++, node = node.parentElement) {
                    const btns = Array.from(node.querySelectorAll('button'));
                    const del = btns.find(b => (b.innerText || '').includes('Delete project'));
                    if (del) { del.click(); return 'clicked'; }
                }
                return 'no-delete-button';
            }""",
            pid,
        )
        if clicked != "clicked":
            raise RuntimeError(f"could not initiate delete for project {pid}: {clicked}")

        await self.page.wait_for_timeout(500)
        confirm = L.confirm_delete_button(self.page)
        await wait_for_locator(confirm, timeout_s=DEFAULT_TIMEOUT_S, what="confirm delete")
        await confirm.click()
        await self.page.wait_for_timeout(1200)
        logger.info(f"deleted project {pid}")
