# flow-api — Agent briefing

This is the `flow-browser` public Python library (Google Flow / Veo 3.1 client), checked out as a sibling of the [`upwhiten-workspace`](../upwhiten-workspace/) hub.

## Status

- **Vendored public release.** Git remote is `munderel/flow-browser`; the checkout matches `main` with no local divergence (single commit: "Initial public release of flow-browser"). This is not a fork.
- **Upstream README is authoritative.** Installation, the full feature matrix, the architecture diagram, the disclaimers, the "when something breaks" runbook — all in [README.md](README.md). Read it before doing anything here.
- **No upwhiten consumers yet.** No sibling repo currently imports `flow_browser`. The checkout is here so the hub can experiment with Veo 3.1-generated creatives for the Meta ads workflow at `../upwhiten-meta-ads/`.

## How to work with this repo

1. **For API questions or usage:** read [README.md](README.md). It's comprehensive (~90 lines) — features table, async quickstart, architecture, status.
2. **For fixes or features:** contribute upstream at `munderel/flow-browser`, then re-pull here. Don't fork into a private divergence — you'll lose access to upstream improvements and bug fixes to the brittle locator layer.
3. **For UI breakage** (Flow's UI changes regularly): run `python scripts/inspect_flow.py`, patch [src/flow_browser/locators.py](src/flow_browser/locators.py), upstream the fix.

## What NOT to do

- **Don't write a private upwhiten-specific fork in this folder.** If you need an upwhiten-specific wrapper, build it in `../upwhiten-meta-ads/` or a new sibling repo and import `flow_browser` as a dependency.
- **Don't commit `~/.flow-browser/profile`** or any session state. The persistent Chrome profile holds your real Google session — keep it outside the repo.
- **Don't add upwhiten secrets to this repo.** It's a public library; secrets do not belong here.
- **Don't read `inspections/`** (locator-debug DOM dumps — large, transient).
