---
name: zotero-research
description: "Use when the user asks to connect to Zotero, list Zotero collections/papers, synthesize a source-grounded literature review, or deep-read selected papers with Codex. Supports read-only Zotero Web API in cloud sessions and optional upstream ZotPilot locally."
---

# Zotero Research — Codex workflow

This repository-level skill provides a **safe entrypoint**, not a pre-authorized Zotero connection. It does not embed or copy ZotPilot's implementation.

## Choose the backend honestly

1. **Cloud / GitHub-hosted Codex (read-only)**: Use the bundled standard-library script at `.agents/skills/zotero-research/scripts/zotero_cloud.py` with `ZOTERO_USER_ID` and `ZOTERO_API_KEY` in the runtime's secure environment. The script only performs GET operations against Zotero Web API v3. Do not ask the user to paste API keys into chat or commit them to GitHub. A Zotero.org API key is distinct from a Zotero desktop local API key.
2. **Local Codex + Zotero Desktop (full ZotPilot)**: Follow the upstream project https://github.com/xunhe730/ZotPilot . On the user's computer, after checking the upstream project and permissions, run `python -m pip install zotpilot`, `zotpilot setup`, `zotpilot doctor`, and `zotpilot index` as needed. This mode requires desktop Zotero data/PDFs and optionally the Zotero browser connector. The original project provides `ztp-review`, `ztp-tutor`, `ztp-research`, `ztp-profile` and `ztp-setup`. Do not claim they run on GitHub just because this skill exists.

## Cloud read-only usage

From repository root:

```bash
python3 .agents/skills/zotero-research/scripts/zotero_cloud.py collections
python3 .agents/skills/zotero-research/scripts/zotero_cloud.py papers --collection COLLECTION_KEY --limit 100 --output /tmp/zotero-papers.json
python3 .agents/skills/zotero-research/scripts/zotero_cloud.py papers --collection COLLECTION_KEY --limit 100 --fulltext --output /tmp/zotero-papers-fulltext.json
```

`collections` outputs collection keys and names. `papers` outputs the title, abstract, authors, DOI, publication date, tags, parent item key, and—only with `--fulltext`—the synced indexed-text of accessible child attachments. If no full text is indexed/synced, report that explicitly. It is not equivalent to reading PDF figures, formulas, or layout. Do not download or store Zotero exports in public-repository files, commits, GitHub Actions logs, public artifacts, or issue comments. The sample `/tmp` files are runtime-local, **not** GitHub repository content.

## Review workflow

- Establish the user-selected collection, research question, and scope.
- Enumerate every paper in scope and record its Zotero item key. Note coverage: total, full-text available, metadata-only, and failures. Never silently drop papers.
- Produce one evidence card per paper: research question, approach, experimental setup, measured outcomes, limitations, DOI and item key. Mark a field `not verified from full text` when evidence is metadata-only.
- Produce a comparison table of methods/assumptions, strengths, limitations, and research gaps. Organize a review by coherent themes, not a chain of paper abstracts.
- Every substantive empirical claim should cite a paper (DOI/item key and section/quote where available). Do not invent numbers, experiments, or conclusions.
- If full-text coverage is incomplete, state exactly what remains unavailable before making broad claims.

## Deep-reading workflow

- Select a paper; fetch and inspect available indexed full text or an explicitly supplied PDF.
- Explain methods, baselines, datasets, evaluation, findings, confounders, reproducibility, and transferable insights.
- Distinguish verified evidence from informed hypotheses. For images/tables/math requiring visual examination, ask for the original PDF or use local ZotPilot; plain-text indexing is not sufficient.
- Never modify Zotero items/tags/annotations in cloud mode. Local ZotPilot's write-capable actions require explicit user authorization.

## Constraints

- Do not confuse a GitHub repository with a running MCP server or an authorization grant.
- Never commit Zotero credentials, PDFs, copyrighted papers, exported bibliographies, or personal research records into this public repository.
- On authorization/API errors, report the blocker rather than hallucinate library contents.
- Upstream ZotPilot source: https://github.com/xunhe730/ZotPilot (MIT license, separate project). This compatibility workflow is not an official ZotPilot distribution.
