# YouTube 免费发现通道修复｜2026-10-21

## 已确认的故障
GitHub Actions `39545478821`：Fireship、Matt Wolfe、Two Minute Papers 三个 YouTube 官方 RSS 频道均 HTTP 404。已通过第三方频道资料交叉核对三者 Channel ID，**暂没有证据说明是 IDs 失效**。YouTube 2025-12—2026-10 官方社区报告活跃频道 RSS 有间歇性 404/500。修复重点是避免把网络间歇故障错误判成用户无视频。

## V3.3 第一项：官方优先、免费优先

1. **不需 Key 的 RSS 尽量恢复：**优先 `www.youtube.com/feeds/videos.xml?channel_id=...`；404/5xx 与网络超时才试 YouTube 同域官方 `/xml/feeds/videos.xml?channel_id=...`，然后原 URL 再试一次（有限等待）。403、401、其他权限失败不作重试或绕过。每条来源写出 `retrieval_path`；两个地址均失败则标 unavailable，不会记零帖子或假成功。备用地址是基于 Google YouTube Issue Tracker 2026-09-29 关于**推送订阅**的修复建议，不保证这个 GET 地址一定有效。
2. **官方 YouTube Data API作为可靠关键词入口：**仓库原 `youtube_official_search_v3.py` 已存在。每3小时最多3组，按时段轮换共9组 AI 视频/设计/实操搜索，日计划 8×3=24 次 `search.list`。官方2026-06以后默认独立额度100次search.list/天；`videos.list` 按50条视频每次分批查询全部统计数，不丢掉60条中最后10条。API项目额度以用户自己的 Cloud Console 为准，时区为Pacific Time重置；推送/开发变更可能消耗配额，因此最大使用量只是**正常8次定时运行的预测**，不是对任何账户承诺配额。
3. **绝不默认调用 API 或触发付费：**仅在用户自行启用 repo Actions variable `YOUTUBE_SEARCH_ENABLED=1`，并把合法获得的 `YOUTUBE_DATA_API_KEY` 作为 Actions secret 添加之后，**定时运行和明确触发的工作流**才会调用。PR/push构建永远跳过，默认 `not_configured`；不保存密钥到脚本、文档、Google Sheets或日志。项目不主动开通 Google Cloud Billing。
4. **领域价值保障：**API返回原创视频链接、标题、频道、发布时间、频道原生播放/赞/评论快照；它不是全站排名保证，且不证明我们看过整个视频。不能复制/下载创作者视频素材而忽视版权。关键词视频按主题轮换，一手原作和可执行内容需要随后人工核验。

## Google Cloud 管理者完成官方配额启用的步骤（需用户本人授权）
- 打开 [Google Cloud Console](https://console.cloud.google.com/apis/library/youtube.googleapis.com)，选自己的项目并启用 YouTube Data API v3，核查当前的免费配额和账号有无计费条件。
- 在 Google Cloud 的 Credentials 页面创建/限制 API key；最小权限尽可能限制 YouTube Data API，必要时限制调用来源。不要在聊天或版本控制中粘贴 key。
- 在 GitHub 仓库 Settings → Secrets and variables → Actions → repository secret，添加 `YOUTUBE_DATA_API_KEY`；在 Variables 新增 `YOUTUBE_SEARCH_ENABLED=1`。只在用户确认启用时设置。
- 运行后的渠道健康报告需要真正返回 `youtube_query:...` 条目才能算官方 API 来源可用；仅开关、Key或单测通过均不算实测。
- 如不想启用任何 API 配置，系统仍保留 RSS、公开索引和其他现有免费发现来源，继续报告 RSS 故障。

## 离线验收与现场验证
- RSS：404→官方备用地址200；403→不重试；两个地址与重试全部失败→unavailable。
- API：无Key/开关未启用→零网络调用；每次≤3关键词搜索；时间窗相对当前 UTC；每天计划≤24次（仅按每3h计划，不包括其他手动运行）；批次60条→两次videos.list且60条都有指标。
- GitHub PR CI全部通过、真实Actions RSS诊断保留；需要用户Key后再以合法真实API回传作为完整验收。

## 证据
- 官方search/list配额：https://developers.google.com/youtube/v3/docs/search/list
- 官方API overview：https://developers.google.com/youtube/data/getting-started
- 2026-06配额更新：https://developers.google.com/youtube/v3/revision_history
- RSS偶发404：https://discuss.ai.google.dev/t/youtube-rss-feed-endpoint-returns-404-errors/113379
- YouTube官方Issue Tracker推送订阅备用路径：https://issuetracker.google.com/issues/566069563
- 公开的开源 youtube-rss-server：https://github.com/telnet23/youtube-rss-server ；**同样要求官方API Key或应用凭证，并非免密无限抓取解法。**
