# Zotero Research for Codex

This folder adds a repository-scoped `zotero-research` skill to `chenyang-99/codex`. It is **not** the full upstream ZotPilot implementation, and copying this folder to GitHub does not establish any Zotero authorization.

## Cloud / Codex Cloud: read-only Zotero Web API

Set `ZOTERO_USER_ID` (numeric ID) and `ZOTERO_API_KEY` (a **read-only** Zotero Web API key) in the Codex runtime's secure environment. Never add credentials to source code, GitHub issues, GitHub Actions YAML, artifacts, chat, or logs. Generate a dedicated key at https://www.zotero.org/settings/keys.

Run these from this repository's root:

```bash
python3 .agents/skills/zotero-research/scripts/zotero_cloud.py collections
python3 .agents/skills/zotero-research/scripts/zotero_cloud.py papers --collection YOUR_COLLECTION_KEY --limit 100 --output /tmp/zotero-papers.json
python3 .agents/skills/zotero-research/scripts/zotero_cloud.py papers --collection YOUR_COLLECTION_KEY --limit 100 --fulltext --output /tmp/zotero-fulltext.json
```

The first command lists keys and collection names. The other commands read metadata and optionally synced **indexed-text** from attachment items. Full text may be missing if not indexed or synced. Cloud mode cannot annotate a local PDF or see the Zotero desktop SQLite database. Never commit the generated JSON files.

Once data exists in the runtime, ask Codex:

> Use zotero-research. Analyze every paper in the chosen collection. Report the number of total papers, papers with indexed text, and metadata-only papers. Write evidence cards, an analytical comparison table, topic-based review, unresolved questions, and a prioritized deep-reading list. Link findings to Zotero item keys and DOIs. Do not infer empirical results from abstracts.

## Local computer: full original ZotPilot

For vector search, PDF parsing, Zotero PDF annotation, and the original `ztp-review` / `ztp-tutor` / `ztp-research` workflows, install the upstream project on the computer where Zotero Desktop is installed:

```bash
python -m pip install zotpilot
zotpilot setup
zotpilot doctor
zotpilot index
```

Official upstream: https://github.com/xunhe730/ZotPilot

## What is deployed and what remains

- **Deployed**: a Codex repo-scoped Skill definition and a standard-library read-only Zotero Web API helper.
- **Not yet connected**: the user's Zotero library (requires their separate secure API authorization).
- **Not deployed**: a hosted always-on MCP server or the complete ZotPilot desktop pipeline.
- **Important**: This is a public GitHub repository. Keep personal paper content and bibliographies in the runtime's private filesystem, not GitHub.

Zotero API references: https://www.zotero.org/support/dev/web_api/v3/basics and https://www.zotero.org/support/dev/web_api/v3/fulltext_content.
