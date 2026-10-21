# 2026-10-21｜优先复用成熟工具补齐全渠道发现盲区（V3.2）

## 本次交付（影子模式）

1. **Horizon 已有的 Apify X Search 实现**：经核对 `Thysrael/Horizon/src/scrapers/twitter.py`，默认的 `altimis/scweet` 接收 `source_mode=search`、`search_query` 和 `search_sort` 等字段。我们新增 `horizon_apify_search_v3.py` 作为**独立的适配器**，没有拷贝安装整个 Horizon。严格按这三个条件才能实际发起任何计费请求：`X_SEARCH_PAID_APPROVED=1`、`X_SEARCH_APIFY_ENABLE=1`、设置 `APIFY_TOKEN` 且 `0 < X_SEARCH_MAX_RUN_USD <= 1.0`。每轮最多一组关键词、一次 Actor 运行，请求参数带 `maxTotalChargeUsd` 和 `maxItems`。正常 GitHub Actions 未接入任何 secret，始终只写 `not_configured` 证据。
2. **免费公开新闻索引补漏**：`indexed_social_discovery_v3.py` 尝试 Google News RSS 的 site 查询来发现已被索引的 X、小红书、抖音、TikTok、Instagram、YouTube 相关页面。候选明确标记仅是「索引标题及间接链接」，不当作目标平台原帖或站内热度，更不能因无结果判断该平台无相关内容。
3. **YouTube 官方视频搜索**：`youtube_official_search_v3.py` 用 YouTube Data API 官方 `search.list`＋`videos.list`，最多三组关键词＋一次视频指标查询。必须同时设置 `YOUTUBE_SEARCH_ENABLED=1` 和 `YOUTUBE_DATA_API_KEY`，默认不调用。播放、赞、评论均保留为 YouTube 原生数据，不得换算为 X 热度，视频画面及版权需另审。
4. **原候选与审计系统**：已将三种输入纳入 `unified_topic_intake.py`，并由 `channel_gap_audit_v3.py` 分别报告；代码路径不会使任一研究候选自动批准发布。

## 其他现成工具真实适用范围

| 工具 / 提供方 | 能做什么 | 采用结论 |
|---|---|---|
| Horizon / Apify Scweet | X 关键词与指定账号检索，Horizon 默认依赖 APIFY_TOKEN | 已接入**默认禁用**的适配器；待真实许可凭据与用户明确费用批准后才运行 |
| xAI 官方 X Search | 可以按关键词/语义实时搜索 X；2026-09-21 起按抓取帖子和用户计费，模型 tokens另计 | 备用研究/核验途径，不能在未提供 xAI Key 时声称接通 |
| TwitterAPI.io / 其它 X 非官方搜索数据商 | 有返回原帖 JSON 的商业搜索服务 | 候选备用。价格为提供商自报，需核合规、字段、实际成功率和费用，不直接上线 |
| NanmiCoder/MediaCrawler | 声称支持小红书、抖音、微博、B站、知乎、快手、贴吧等关键词/帖子搜索 | **不能直接加入商业生产流程**：README 明示“禁止用于商业用途”，同时多渠道需平台登录与合规访问。只能参考架构，在取得明确权利后另评 |
| Authurzk/mediacrawler | 面向图文运营，具小红书/B站采集与去重界面 | 自身 README 明示抖音尚受风控，真实采集需要 Cookie；缺少商业授权与环境稳定性证明，先不自动部署 |
| Firecrawl（当前可用的连接工具）| 网站公开网页正文提取和研究 | 作为单个选题项目的来源补全，不能冒充 X 或小红书原生热度 |
| Google News RSS 站点搜索 | 免费、可作为已收录公开链接的后备发现 | 已开发，但索引样本的成功率需看 Actions 实跑 |
| YouTube Data API 官方 | 跨频道最新/热门视频关键词和原生视频指标 | 已接入可选适配器，缺 API Key 则不会实际请求 |

## 必须保留的未完成项

- X 全局搜索：**适配器准备好≠实际已获取 X 搜索结果**，只有用户提供合规可用 Token、单次/总预算和明确启用时方能进行真实可用性测试。
- YouTube 官方 API：未配置 Key 时只记录 `not_configured`；不能冒充“已打通 YouTube 全站热榜”。
- 小红书/抖音/TikTok/Instagram：公开索引不是平台原生热门榜；合规登录、平台提供商或授权数据渠道仍需确认。
- 不得把账号 Cookie 直接提交到 GitHub 或复制在对话中；不允许借账号登录状态规避平台限制。
- GitHub Actions 成功或注册渠道数增长都不是高质量选题采纳率提高的证据。
- 已有每日巡检与七天效果验收仍有效；历史发布与互动只有权威 Google Sheets 提供的数据可当真实反馈。

## 可独立核对的依据

- Horizon Apify 代码：https://github.com/Thysrael/Horizon/blob/main/src/scrapers/twitter.py
- Horizon Playwright 局限：https://github.com/Thysrael/Horizon/blob/main/src/scrapers/twitter_playwright.py
- Apify Actor 实际主页与价格：https://apify.com/altimis/scweet
- Apify 运行费用上限说明：https://docs.apify.com/api/v2/actors-runs-post
- YouTube 官方搜索：https://developers.google.com/youtube/v3/docs/search/list
- YouTube 官方配额：https://developers.google.com/youtube/v3/determine_quota_cost
- MediaCrawler 许可声明：https://github.com/NanmiCoder/MediaCrawler/blob/main/README.md
- 小红书/B站开源运营版可用性：https://github.com/Authurzk/mediacrawler

> 以上是设计与代码接入的边界说明，不代表互联网各端点都在本次 CI 中可访问；必须以真实工作流 JSON 产物为准。
