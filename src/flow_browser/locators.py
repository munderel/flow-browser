"""
All Playwright locators for Google Flow live here.

When Flow's UI changes and something stops working, this is the only file you
should need to patch. Prefer role + accessible-name selectors (stable across
class-name churn) over CSS class chains.

Discovery workflow:
  1. Open Flow in the headed browser (examples/first_run_signin.py).
  2. DevTools -> Inspect the broken element.
  3. Prefer page.get_by_role(...), page.get_by_text(...), page.get_by_label(...),
     page.get_by_placeholder(...), or [data-testid="..."] attributes.
  4. Update the lambda below; the rest of the codebase imports through here.

NOTE: Many of these are placeholders pending the live DOM-inspection pass
(scripts/inspect_flow.py). They are intentionally permissive (case-insensitive
regex) so they survive minor copy tweaks.
"""

from __future__ import annotations

import re

from playwright.async_api import Locator, Page


# --- Auth / global ------------------------------------------------------------

def signed_in_indicator(page: Page) -> Locator:
    """Something that only appears when the user is signed in.

    Flow renders the user's Google avatar as <img alt="User profile image" ...>
    sourced from lh3.googleusercontent.com. Signed-out users get redirected to
    accounts.google.com and never see this image.
    """
    return page.locator("img[alt='User profile image']")


def signin_button(page: Page) -> Locator:
    return page.get_by_role("link", name=re.compile(r"sign ?in", re.I)).first


# --- Global / page chrome -----------------------------------------------------

def cookie_banner_reject(page: Page) -> Locator:
    """Google-wide cookies banner. Class is shared across all Google properties."""
    return page.locator(".glue-cookie-notification-bar__reject")


def cookie_banner_accept(page: Page) -> Locator:
    return page.locator(".glue-cookie-notification-bar__accept")


# --- Home / project list ------------------------------------------------------

def new_project_button(page: Page) -> Locator:
    # Button accessible name is icon-glyph prefixed: "add_2New project".
    # No anchor so the icon prefix doesn't break the match.
    return page.get_by_role("button", name=re.compile(r"new project", re.I))


def project_card(page: Page, name: str | None = None) -> Locator:
    """Project tile on home. Each is an <a> linking to /fx/tools/flow/project/<id>."""
    base = page.locator("a[href*='/fx/tools/flow/project/']")
    if name:
        return base.filter(has_text=re.compile(re.escape(name), re.I))
    return base


def project_card_menu(card: Locator) -> Locator:
    return card.get_by_role("button", name=re.compile(r"more|options|menu", re.I))


def project_delete_menu_item(page: Page) -> Locator:
    return page.get_by_role("menuitem", name=re.compile(r"delete", re.I))


def confirm_delete_button(page: Page) -> Locator:
    """Inside the delete-confirmation dialog only — not the per-card Delete buttons."""
    dialog = page.locator("[role=alertdialog], [role=dialog]").last
    return dialog.get_by_role("button", name=re.compile(r"\bdelete\b|confirm|^ok$|^yes$", re.I)).last


# --- Project view / generation -----------------------------------------------

def prompt_textarea(page: Page) -> Locator:
    """Flow uses a Slate.js rich-text editor as the prompt input.

    DOM: <div role="textbox" aria-multiline="true" contenteditable="true"
            data-slate-editor="true" ...>
    """
    return page.locator("[data-slate-editor='true']").first


def generate_button(page: Page) -> Locator:
    """The 'Create' submit button (arrow_forwardCreate). Use .last because Flow
    also has an 'add_2Create' button elsewhere; the submit is rendered later in DOM."""
    return page.get_by_role("button", name=re.compile(r"create", re.I)).last


def model_picker(page: Page) -> Locator:
    """Toolbar button that opens the settings popover. Its accessible name changes
    with the current state:
      - Image mode: shows model name ('🍌 Nano Banana 2 arrow_drop_down')
      - Video mode: shows 'Video' + aspect glyph + quantity ('Video crop_16_9 x2')
      - Frames / Ingredients modes: similar with their own prefix
    Match on EITHER a known model name OR a 'crop_*' aspect glyph (always present
    in the button name regardless of mode)."""
    return page.get_by_role(
        "button",
        name=re.compile(
            r"veo|banana|imagen|kling|crop_(16_9|9_16|1_1|landscape|portrait|square)",
            re.I,
        ),
    ).first


def model_dropdown_trigger(page: Page) -> Locator:
    """Inside the open settings popover, the button with 'arrow_drop_down' that
    expands the actual model menu. Use AFTER clicking model_picker()."""
    return page.get_by_role("button", name=re.compile(r"arrow_drop_down", re.I)).first


def model_menu_item(page: Page, pattern: str) -> Locator:
    """A menuitem inside the expanded model dropdown."""
    return page.get_by_role("menuitem", name=re.compile(pattern, re.I))


def output_kind_tab(page: Page, kind: str) -> Locator:
    """The Image / Video tab inside the settings popover. kind in {'image','video'}."""
    return page.get_by_role("tab", name=re.compile(kind, re.I))


def aspect_ratio_picker(page: Page) -> Locator:
    """Inside the open settings popover, tabs named with 'crop_*' icon glyph + ratio."""
    return page.get_by_role("tab", name=re.compile(r"crop_(16_9|9_16|1_1|landscape|portrait|square)", re.I)).first


def aspect_ratio_tab(page: Page, ratio: str) -> Locator:
    """A specific aspect ratio tab. ratio: '16:9', '9:16', '1:1', '4:3', '3:4'."""
    icon_map = {
        "16:9": "crop_16_9",
        "9:16": "crop_9_16",
        "1:1": "crop_square",
        "4:3": "crop_landscape",
        "3:4": "crop_portrait",
    }
    glyph = icon_map.get(ratio, ratio)
    return page.get_by_role("tab", name=re.compile(rf"{glyph}|{re.escape(ratio)}", re.I))


def quantity_tab(page: Page, n: int) -> Locator:
    """Variant-count tab in the settings popover. Tabs are '1x', 'x2', 'x3', 'x4'.

    Flow generates N variants of the prompt when set to xN; result is N tiles
    appearing in the project grid at the same time.
    """
    if n == 1:
        # The "1x" tab uses that exact label.
        pattern = r"^1x$"
    else:
        pattern = rf"^x{n}$"
    return page.get_by_role("tab", name=re.compile(pattern, re.I))


def duration_picker(page: Page) -> Locator:
    """Any of the duration tabs (4s/6s/8s) — used for presence detection."""
    return page.get_by_role("tab", name=re.compile(r"^\d+s$", re.I)).first


def duration_tab(page: Page, seconds: int) -> Locator:
    """The specific duration tab in the Video popover. seconds in {4, 6, 8}."""
    return page.get_by_role("tab", name=re.compile(rf"^{seconds}s$", re.I))


def scene_cards(page: Page) -> Locator:
    """Flow renders generated media as 'tiles' with [data-tile-id='fe_id_<uuid>'].
    Use the outer tile wrapper, not the inner duplicate inside <span>."""
    # The outer tile is a child of [data-known-size] inside the virtuoso list.
    return page.locator("[data-known-size] [data-tile-id]")


def scene_card_busy(card: Locator) -> Locator:
    """Tile shows a progress overlay while rendering. Common markers:
    aria-busy, role=progressbar, or a generic 'loading' / 'processing' span."""
    return card.locator(
        "[aria-busy='true'], [role='progressbar'], "
        "[class*='loading' i], [class*='processing' i]"
    )


def scene_video_element(card: Locator) -> Locator:
    # Veo tiles render <video>; Imagen tiles render <img alt="Generated image">.
    return card.locator("video, img[alt='Generated image']")


def scene_download_button(card: Locator) -> Locator:
    return card.get_by_role("button", name=re.compile(r"download", re.I))


# --- Ingredients / media upload ----------------------------------------------

def ingredients_panel_toggle(page: Page) -> Locator:
    """'Add Media' button opens the media/ingredients panel."""
    return page.get_by_role("button", name=re.compile(r"add media|ingredient", re.I)).first


def ingredient_upload_input(page: Page) -> Locator:
    return page.locator("input[type='file']").first


def ingredient_tiles(page: Page) -> Locator:
    return page.locator("[data-ingredient-id]")


# --- Edits --------------------------------------------------------------------

# --- Tile detail view (after clicking a tile) --------------------------------

def detail_extend_button(page: Page) -> Locator:
    """'Extend' button in tile detail toolbar (icon: keyboard_double_arrow_right)."""
    return page.get_by_role("button", name=re.compile(r"extend", re.I))


def detail_insert_button(page: Page) -> Locator:
    """'Insert' (object) button in tile detail toolbar (icon: add_box)."""
    return page.get_by_role("button", name=re.compile(r"insert", re.I))


def detail_remove_button(page: Page) -> Locator:
    """'Remove' (object) button in tile detail toolbar (icon: ink_eraser)."""
    return page.get_by_role("button", name=re.compile(r"remove", re.I))


def detail_reuse_prompt_button(page: Page) -> Locator:
    """'Reuse text prompt' / 'Reuse prompt' in tile detail toolbar (icon: redo)."""
    return page.get_by_role("button", name=re.compile(r"reuse (text )?prompt", re.I))


def detail_download_button(page: Page) -> Locator:
    """'Download' button in tile detail toolbar."""
    return page.get_by_role("button", name=re.compile(r"^download$|\bdownload\b", re.I))


def detail_back_button(page: Page) -> Locator:
    """'Back' button to leave tile detail view (icon: arrow_back)."""
    return page.get_by_role("button", name=re.compile(r"^back$|\bback\b", re.I))


def detail_done_button(page: Page) -> Locator:
    """'Done' button in tile detail view."""
    return page.get_by_role("button", name=re.compile(r"^done$", re.I))


# --- CAPTCHA / interrupt -----------------------------------------------------

def captcha_iframe(page: Page) -> Locator:
    return page.frame_locator("iframe[title*='reCAPTCHA' i]").locator("body")
