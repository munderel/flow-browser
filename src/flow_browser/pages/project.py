from __future__ import annotations

from playwright.async_api import Page

from flow_browser.pages.edits import EditsPage
from flow_browser.pages.generation import GenerationPage
from flow_browser.pages.ingredients import IngredientsPage


class ProjectPage:
    """Inside-a-project view: storyboard, scenes, generate/edit dialogs."""

    def __init__(self, page: Page) -> None:
        self.page = page
        self.generation = GenerationPage(page)
        self.ingredients = IngredientsPage(page)
        self.edits = EditsPage(page)

    @property
    def project_id(self) -> str:
        return self.page.url.rstrip("/").rsplit("/", 1)[-1]
