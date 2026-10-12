# Social Topic Radar — Anonymous, read-only research probes

A **zero-social-account / zero-cookie / zero-paid-API** GitHub Actions experiment.

## What is deployed

- \`probe.py\`: checks X public search, creator timeline, a real post and up to 5 public replies; checks whether one Xiaohongshu note URL and one Douyin public video URL actually return verifiable post metadata (a generic HTML shell is **not** success).
- \`discovery.py\`: monitors 6 public X AI creators, gathers up to 8 recent posts per handle, filters for AI topics, ranks by disclosed engagement counts, and samples up to 6 public replies on 2 prioritized posts. The ranking is a **heuristic**, not AI editorial judgment.
- \`rss_discovery.py\`: anonymously collects recent entries from OpenAI News, Google AI blog, and GitHub blog official RSS feeds, with per-feed success/failure tracking.
- \`.github/workflows/anonymous-social-probe.yml\`: executes those read-only tests each day around **09:15 Beijing time**, after pushes to this folder, or through manual dispatch. Scheduled timing is best effort.

## Latest verified behavior (October 13, 2026, Beijing time)

Multiple real Actions executions succeeded. X creator availability fluctuated, with 3–5 of 6 tested handles returning posts per run, 7–13 candidate posts, and 12 verified sampled replies. Public RSS sources returned 40 entries on the latest tested run (15 OpenAI, 15 Google AI, 10 GitHub). These are *obtained item counts* rather than guarantees.

**Not working or not deployed:** X arbitrary keyword search was reported unavailable by the tested public endpoint; Xiaohongshu example note redirected to 404; Douyin example link returned a shell without verified caption/body; the Xiaohongshu and Douyin comment APIs were not enabled. No claim of complete three-platform coverage should be made.

## Open current report

GitHub → Actions → **Anonymous social content probe** → latest green run → Artifacts → **anonymous-probe-report**. ZIP contains:

- \`report.json\` and \`report.md\`: truthful capability test evidence.
- \`topic-candidates.json\` and \`topic-candidates.md\`: actual public X candidate content and sample replies.
- \`public-rss-candidates.json\` and \`public-rss-candidates.md\`: official RSS entries.

Artifacts expire after 14 days; this is not a persistent history database. The process does **not** automatically post to X, Douyin, Xiaohongshu or send ChatGPT notifications.

## Zero-login boundaries

No login, cookies, tokens, X API keys, proxies, account creation, captcha bypass, or user-specific browser sessions. The pinned open-source [X-Aggregate-Data](https://github.com/qianyubtc/X-Aggregate-Data) reader is pulled from a fixed Git commit and allowed only read-only operations. GitHub Actions grants \`contents: read\` — it cannot write to the repo.

A finished GitHub job does **not** establish that the platform yielded content. Explicitly inspect \`content_status\`, \`comments_status\`, source coverage, per-run error fields, and source URLs. Inaccessible posts, protected accounts, deleted items and restricted comments remain inaccessible.

## Operations and costs

The public repository uses GitHub's standard hosted Actions runner; standard public repository runs typically incur no additional Actions charges, subject to GitHub policies and fair use. No extra API subscription is configured.

To disable scheduled runs, edit/remove the schedule in the workflow or disable the workflow in GitHub Actions. This is an ephemeral scheduled research probe, not a persistent Docker server or a promise of unrestricted access to three social platforms.
