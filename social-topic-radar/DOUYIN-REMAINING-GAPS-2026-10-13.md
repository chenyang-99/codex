# Douyin remaining capabilities — direct GitHub cloud verification (2026-10-13)

## User hard limits
Zero Douyin personal-account login, user-supplied Cookie or new paid service. A temporary anonymous guest session or the vendor's published free demo identity is allowed. Stop on login wall/CAPTCHA/risk controls; no proxy rotation, CAPTCHA bypass, repeated requests under a blocked identity, or hidden access.

## Newly validated facts

1. GitHub Actions run: https://github.com/chenyang-99/codex/actions/runs/38378324103 (job 115232188540), `social-topic-radar/douyin_reply_diagnostic.py`
   - Actual public AI-topic Douyin video: https://www.douyin.com/video/7692794233737331338
   - First-level comments: 16 actual text-bearing records, endpoint HTTP 200.
   - Four comments report nested replies. One parent selected with `reply_count=2`.
   - Actual nested replies retrieved: **0**. Documented `/api/v1/douyin/video/comments/replies` returned HTTP **502**, structured error code was not exposed in that response.
   - This excludes 'parent has no replies' as the immediate cause; cannot establish whether platform anti-bot, upstream signature drift, or public demo service failure caused 502.

2. GitHub Actions run: https://github.com/chenyang-99/codex/actions/runs/38378651281, `social-topic-radar/douyin_native_search_audit.py`
   - Fetched official free demo public `https://demo.douyin.wtf/openapi.json`, HTTP 200, search route count: 0.
   - Public v5 REST routes include content detail, author posts, top comments and nested comment route, but **not native full-platform keyword search**.
   - The upstream source `src/dtk/platforms/douyin/endpoints.py` contains `VIDEO_SEARCH` and `GENERAL_SEARCH` URL constants; they are **not registered in ENDPOINTS**, and `src/dtk/mcp/routing.py` explicitly classifies `ResourceKind.SEARCH` as unserviceable. A source constant is not an implemented endpoint.

3. Same daily GitHub workflow run:
   - Verified public demo API 3 video seed lookups, 2 distinct creator feeds, 8 related AI videos, 2 comment pages yielding 16 actual first-level comment texts.
   - Actual returned likes/comments/collect/share counts are **sampled creator-post values**, not all-platform viral rankings.
   - Chinese demand analysis combines those with Bilibili/V2EX comments, retaining platform labels. It does not claim every comment is an AI pain point.

## Independent alternatives examined

- [why20261/douyin-datas-insight](https://github.com/why20261/douyin-datas-insight): requires a separately obtained `GUAIKEI_API_TOKEN` from a paid service; no account login is not equal to no paid API. **Not deployed**.
- [LIghtJUNction/douyin](https://github.com/LIghtJUNction/douyin): platform web search/comments explicitly require a logged-in browser Cookie or official OAuth. **Not deployed**.
- [EpicSaber/douyin-analytics-scraper](https://github.com/EpicSaber/douyin-analytics-scraper): README is for an Apify pay-per-result actor; search/profile modes recommend residential proxies and incur platform charges. **Not deployed**.
- Web index discovery has produced candidate video URLs, but cannot serve as verifiable, complete native keyword search.

## Actual delivery

- Added one-shot nested reply diagnostic; failures do not trigger retries.
- Added daily schema audit to detect new native search support in the public demo.
- Existing daily creator-source video/comment sampling retained, not altered to claim all-platform search.
- No account or service purchase and no import of Douyin credentials.

## Current acceptance verdict

| Requirement | State |
|---|---|
| Verified video details and recent posts from a few creators | PASS (bounded) |
| Engagement numbers within those sampled videos | PASS (bounded) |
| Some real first-level comments | PASS (bounded) |
| Any query over all Douyin videos and a defensible platform-wide hot ranking | **NOT PASS** |
| Real text of second-level comment replies | **NOT PASS (HTTP 502)** |
| Stable, independent long-term backend | **NOT PASS** (shared free demo) |

**Do not claim complete Douyin data access.** New capability requires a genuinely public search provider or appropriate access authorization, and a working nested reply source. New tests must present actual returned rows and original URLs, not installation success or a generic HTTP 200 page.