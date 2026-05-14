from __future__ import annotations

from pathlib import Path
from typing import Self

from playwright.async_api import Page

from flow_browser.browser import BrowserSession
from flow_browser.constants import DEFAULT_TIMEOUT_S
from flow_browser.exceptions import FlowError
from flow_browser.pages import HomePage, ProjectPage
from flow_browser.types import AspectRatio, Ingredient, Model, Project, Video
from flow_browser.utils.downloads import download_via_url
from flow_browser.utils.logging import logger


class FlowBrowser:
    """High-level facade over a real Chrome driving labs.google/fx/tools/flow.

    Usage:
        async with FlowBrowser() as flow:
            video = await flow.generate_video("a goldfish in a teacup")
            await video.download("out.mp4")
    """

    def __init__(
        self,
        user_data_dir: str | Path | None = None,
        *,
        headless: bool = False,
        executable_path: str | Path | None = None,
        slow_mo: int = 0,
        default_timeout: float = DEFAULT_TIMEOUT_S,
    ) -> None:
        self._session = BrowserSession(
            user_data_dir,
            headless=headless,
            executable_path=executable_path,
            slow_mo=slow_mo,
        )
        self._default_timeout = default_timeout
        self._page: Page | None = None

    async def __aenter__(self) -> Self:
        context = await self._session.start()
        # Reuse the page that opens with persistent_context, or create a new one.
        if context.pages:
            self._page = context.pages[0]
        else:
            self._page = await context.new_page()
        self._page.set_default_timeout(int(self._default_timeout * 1000))
        return self

    async def __aexit__(self, *exc: object) -> None:
        await self._session.stop()
        self._page = None

    @property
    def page(self) -> Page:
        if self._page is None:
            raise RuntimeError("FlowBrowser not entered; use 'async with FlowBrowser() as flow'")
        return self._page

    # --- page-object accessors ------------------------------------------------

    @property
    def home(self) -> HomePage:
        return HomePage(self.page)

    @property
    def project(self) -> ProjectPage:
        return ProjectPage(self.page)

    # --- high-level API --------------------------------------------------------

    async def ensure_signed_in(self) -> None:
        await self.home.assert_signed_in()

    async def list_projects(self) -> list[Project]:
        return await self.home.list_projects()

    async def create_project(self, name: str) -> Project:
        return await self.home.create_project(name)

    async def open_project(self, project: Project | str) -> ProjectPage:
        await self.home.open_project(project)
        return self.project

    async def delete_project(self, project: Project | str) -> None:
        await self.home.delete_project(project)

    async def generate_video(
        self,
        prompt: str,
        *,
        model: Model | None = Model.VEO_3_1_FAST,
        model_name_pattern: str | None = None,
        output_kind: str | None = None,
        aspect_ratio: AspectRatio | str = AspectRatio.LANDSCAPE_16_9,
        quantity: int = 1,
        duration_s: int = 8,
        image: str | Path | None = None,
        project: Project | str | None = None,
    ) -> list[Video]:
        """Generate one or more videos/images. Returns a list — one Video per
        variant. For images, pass model=None + model_name_pattern + output_kind='image'."""
        await self.ensure_signed_in()
        if project is not None:
            await self.open_project(project)
        else:
            await self.create_project(name=prompt[:40])

        videos = await self.project.generation.submit(
            prompt,
            model=model,
            model_name_pattern=model_name_pattern,
            output_kind=output_kind,
            aspect_ratio=aspect_ratio,
            quantity=quantity,
            duration_s=duration_s,
            image=image,
        )
        for v in videos:
            v.bind(self)
        return videos

    async def upload_ingredient(self, image: str | Path) -> Ingredient:
        await self.ensure_signed_in()
        return await self.project.ingredients.upload(image)

    async def extend_scene(self, scene_index: int, prompt: str, seconds: int = 4) -> Video:
        video = await self.project.edits.extend(scene_index, prompt, seconds=seconds)
        return video.bind(self)

    async def download_video(self, video: Video, path: str | Path) -> Path:
        if not video.url:
            raise FlowError("video has no captured URL; cannot download")
        logger.info(f"downloading {video.url} -> {path}")
        return await download_via_url(self._session.context, video.url, path)
