# Social Topic Radar (anonymous read-only probe)

This isolated folder checks what a free, **no-social-account / no-cookie** pipeline can actually retrieve from public X, Xiaohongshu, and Douyin URLs.

**Important:** GitHub Actions is an ephemeral test runner, not a permanently running scraper. The report must never claim whole-platform coverage. A valid HTML response does **not** mean comments or complete media have been retrieved.

- X: use the reviewed, pinned open-source [X-Aggregate-Data](https://github.com/qianyubtc/X-Aggregate-Data) read-only CLI through public FxTwitter endpoints. Test post content, replies, and keyword search separately.
- Xiaohongshu: check whether an anonymous public note URL exposes recognizable post metadata. No anonymous full-comment method is assumed.
- Douyin: check whether an anonymous public share URL exposes recognizable video metadata. The full comment API is **not** deployed at this stage (its separate Docker stack needs an isolated review).
- No platform login, cookies, browser profiles, proxies, anti-captcha measures, posting actions, paid API keys, or GitHub Actions write permissions.

## Run

Open this repository's **Actions** tab, select **Anonymous social content probe**, and click **Run workflow**. It also runs on the daily schedule and on changes in this directory. Open each run's **Artifacts → anonymous-probe-report** to inspect \`report.json\` and \`report.md\`.

Tests are honest capability checks, not demonstrations of "fetch all content". \`verified\` means concrete fields were actually parsed; \`partial\` means the source was reachable but content or scope was incomplete; \`blocked\`/ \`error\` means it could not be verified; \`not_supported\` means this project has no verified anonymous adapter for that surface.

GitHub-hosted public-repo standard runners can run without additional Actions billing, subject to GitHub policies. A GitHub schedule is best effort; it is not real-time or continuously online. Results are temporary Actions artifacts, not a persistent database.

Samples include one X URL previously supplied by the user and example links from public open-source project documentation. The report identifies a stale/deleted sample as a test failure, not as evidence that an entire platform is inaccessible.

## Data and safety

This project stores **only public-data diagnostics** and a bounded excerpt of public content. No credentials are configured, no secrets required, no third-party code is allowed write access to this repo. Respect platform terms and applicable law; stop on access restrictions rather than bypassing them.