# Changelog

## 0.1.1 — 2026-11-22

- Possible credentials in a recipe are now replaced with `[REDACTED]` instead of stopping the export. This applies to `--full`, `--section`, and the summary. A warning shows how many were masked.
- README: update instructions that always work (`install --force`), installer prerequisites (uv, pipx, Node.js for `npx skills`), and PATH help.

## 0.1.0 — 2026-11-22

- First packaged release. Install with `uv tool install` or `pipx install` from GitHub.
- `--version` flag.
- Agent skill installable with `npx skills add` or as a Claude Code plugin.
- Offline tests, CI on Python 3.9 to 3.13, and a weekly live check of the Marketplace.
