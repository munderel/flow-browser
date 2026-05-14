# flow-browser

Unofficial async Python client for [Google Flow](https://labs.google/fx/tools/flow) (Veo 3.1 video generation studio). Drives a real Chrome instance via Playwright using your already-signed-in Google profile — no cookie scraping, no TLS impersonation, no reverse-engineered HTTP endpoints. Your traffic looks like you using Flow normally.

```python
from flow_browser import FlowBrowser

async with FlowBrowser() as flow:
    videos = await flow.generate_video(
        "a goldfish swimming through a teacup, cinematic, slow motion",
        model_name_pattern=r"veo\s*3\.1\s*-?\s*fast",   # any visible model name
        output_kind="video",                              # "image" or "video"
        aspect_ratio="16:9",                              # 16:9, 9:16, 1:1, 4:3, 3:4 (image only: 1:1, 4:3, 3:4)
        duration_s=8,                                     # 4, 6, 8 (Veo only)
        quantity=1,                                       # 1..4 — number of variants in one shot
    )
    await videos[0].download("out.mp4")
```

### Available features

| Feature | API | Cost-aware test |
|---|---|---|
| List projects | `flow.list_projects()` | `examples/manage_projects.py` |
| Create / open / delete project | `flow.create_project / open_project / delete_project` | `scripts/test_create_delete_project.py` |
| Generate image (Nano Banana Pro/2, Imagen 4) | `flow.generate_video(..., output_kind="image")` or `flow.project.generation.submit(...)` | `scripts/test_generate_ad.py` |
| Generate video (Veo 3.1 Lite/Fast/Quality) | `flow.generate_video(..., output_kind="video", duration_s=...)` | `scripts/test_veo_short.py`, `scripts/test_veo_long.py` |
| Multiple variants in one request (1–4) | `quantity=N` | `scripts/test_generate_ad.py` (quantity=2) |
| Upload reference media | `flow.upload_ingredient(path)` or `flow.project.ingredients.upload(path)` | `scripts/test_combined_features.py` |
| Extend / insert / remove on a tile | `flow.project.edits.extend / insert_object / remove_object` | `scripts/test_extend_scene.py` |
| Download any tile | `video.bind(flow).download(path)` | every example |

## Quickstart

```powershell
cd flow-api
uv sync                              # or: pip install -e ".[dev]"
python -m playwright install chromium

python examples/first_run_signin.py  # one-time: sign into Google in the open window
python examples/generate_text_to_video.py "a goldfish in a teacup"
```

After `first_run_signin.py`, the persistent Chrome profile at `~/.flow-browser/profile` remembers your session. Every subsequent run is non-interactive.

## Honest disclaimers

- **Ban risk: low but non-zero.** Driving a real browser with your real signed-in session is the lowest-detection automation you can do — but it's still automation of a paid Google product, which Google's ToS forbids. If you're nervous, use a dedicated Google account.
- **UI breakage: expected periodically.** Flow's UI is not a stable API. When Google ships a UI change, locators break — usually one or two selectors per change. The locator smoke test catches it; patching is a small edit in [src/flow_browser/locators.py](src/flow_browser/locators.py).
- **Throughput is human-paced.** Each generation is a real click + a real render wait. This is a one-browser-tab-at-a-time tool, not a batch pipeline.
- **CAPTCHAs: solve in headed mode.** If Google challenges you, the open window stays put — solve it once and rerun.

## When something breaks

1. Run `python scripts/inspect_flow.py`. It dumps the current Flow DOM + a per-locator hit count to `inspections/*.summary.json`.
2. Any locator with `count: 0` is broken. Find the new selector in `inspections/*.html` (or DevTools in the open window).
3. Patch the offending function in [src/flow_browser/locators.py](src/flow_browser/locators.py). Prefer `get_by_role(..., name=...)` over CSS classes — accessible names are stable, class names are not.
4. Rerun.

## Status

- [x] Scaffold + sign-in flow + persistent profile
- [x] Project list / create / delete — **verified live**
- [x] Image generation (Nano Banana Pro / 2 / Imagen 4) — **verified live**
- [x] Video generation (Veo 3.1 Lite / Fast / Quality / Lite-Lower) — **verified live** (4s + 8s)
- [x] Settings popover: output kind, aspect ratio, quantity (1–4 variants), duration (4/6/8s)
- [x] Media upload (uploads as a project tile via Add Media) — **verified live**
- [x] Scene extend / insert / remove via tile detail view — code-complete, see `scripts/test_extend_scene.py` to verify live
- [x] Selectors tuned against live Flow DOM
- [ ] Locator smoke test suite
- [ ] CI

## Architecture

```
FlowBrowser (client.py)              <- high-level facade
    │
    ├── BrowserSession (browser.py)  <- Playwright persistent context
    │
    ├── HomePage      (pages/home.py)
    ├── ProjectPage   (pages/project.py)
    │     ├── GenerationPage  (pages/generation.py)
    │     ├── IngredientsPage (pages/ingredients.py)
    │     └── EditsPage       (pages/edits.py)
    │
    └── locators.py  <- THE brittle layer; all selectors live here
```

## License

MIT. See [LICENSE](LICENSE).
