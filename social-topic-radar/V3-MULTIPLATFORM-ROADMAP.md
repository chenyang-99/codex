# Multi-platform topic discovery V3 — shadow implementation

Status: first-phase code on a feature branch, dated 2026-10-21. Existing collectors, nine-value verification, human review and copy-production stay unchanged. This code neither logs in to any platform nor pays for APIs nor publishes.

## Discovery scope

The system must scan five classes of material rather than just new products and X hot posts:

1. New releases: original websites, open-source repositories, model catalogs and official feeds.
2. Multi-platform popular material: posts, image compilations, demonstrations, practical guides and resource lists.
3. Creators and curators: original authors, verified quotes, public referrals and discoverable networks.
4. Demand evidence: community problems, questions, constraints and reusable solutions.
5. Creative works: AICG images, video cases, visual design, animation and workflows.

The source_coverage_v3.json directory lists 34 overseas, Chinese and cross-platform channels, including source-specific coverage and access restrictions. A listed channel is NOT proof that we capture it automatically. Add other platforms as discovered, and review real health weekly.

## Actually implemented in this first phase

- public_hot_discovery_v3.py attempts read-only public charts/sources: Hacker News top and Show HN, V2EX hot, newly created GitHub repositories sorted by cumulative stars (not true Trending growth), Reddit top RSS, and Bilibili popular videos. 403/empty/error are independently recorded rather than called zero demand.
- unified_topic_intake.py unifies existing RSS, X creator samples, AICG source/work candidates, public-platform data, additional public hot feeds, and curated user seeds. It outputs unified-topic-candidates-v3.json and platform-coverage-v3.json.
- seed_x_curator_v3.json contains 20 user-submitted originals from @ianlacerda quote/follow observation plus four independently verified quote messages; the first twenty are explicitly NOT automatically labeled verified quotes.
- Normalization preserves the original post URL, author, publication time, evidence scope, native metrics and collection time; combines items by exact original post URL or explicit GitHub/project link, not similar titles.
- Cross-platform popularity is NOT represented as one universal numerical score: GitHub stars, HN points, X bookmarks and Bilibili favorites have different meanings and cannot be directly summed.
- Workflow anonymous-social-probe.yml runs V3 as a parallel SHADOW artifact; original editorial-shortlist.json, production ranking, historical Sheet entries and publication requirements are unchanged.
- Both collectors and normalizer have offline regression tests under social-topic-radar/tests.

## Still missing or requiring a separate authorization

- X global recent-high-engagement search, per-creator baselines, automatic quote/repost graph; fixed-account discovery alone is insufficient. Horizon's third-party Apify dependency remains subject to cost/permission/reliability testing.
- Native full-content popular-note/video/comment collection for Xiaohongshu, Douyin, TikTok, Instagram, Threads, LinkedIn, Jike, and Kuaishou. Public search-index clues do not count as proven accessible content.
- Weibo, Zhihu, WeChat official accounts, Telegram public channels, Pinterest/Behance/Dribbble, Product Hunt and several other entries are currently registry/on-demand/planned, NOT functioning automated platform-wide collectors.
- Published-image/video rights, actual demonstration claims, complete tutorials and trustworthiness must still be checked.
- Cross-run permanent de-duplication and automatic Google Sheet sync. A --history parameter can flag old entity keys if a file is provided, but the GitHub read-only Action does not persist state.
- Improvement in editorial acceptance or our account's engagement has not been demonstrated.

## Integration contract

Add a new platform to source_coverage_v3.json first, with an honest status. Use an official or lawfully available public API/RSS/index or a consented app; do not bypass restrictions. Add an adapter that emits sanitized records to external-discovery.json: url, source/platform, title, published_utc, project_url if original verified, platform_native_metrics, metrics_checked_at, read_scope. Ensure source failure and zero matches are separate states. Verify with offline tests, then include its results in V3 shadow outputs.

No record without an original permalink becomes a candidate. No automated candidate becomes a publishable topic without independent review.

## Acceptance

Run old and new systems side by side for seven days. Compare: unique relevant projects, independent popular-content discoveries outside X, source availability, accessible original demonstration media, duplicate rate, user selection rate, study time, API cost, and eventual actual on-account results (where available). Do not replace production just because V3 collected more URLs.
