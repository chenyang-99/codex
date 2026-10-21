# V3.1 全渠道选题发现：质量与覆盖率审计

更新时间：2026-10-21。重点为运行证据与漏检风险，而非声称全网抓取完成。

## 新增
- Product Hunt 官方 `/feed`：新品发布线索；不是投票热榜；无需调用有商业使用限制的 GraphQL API。
- Lobsters `/hottest.rss`：编程社区热门讨论。
- GitHub Trending 第三方日榜 JSON：与“近14日高 Star 新仓库搜索”互补；非 GitHub 官方榜单 API，时间戳需核对。
- 保留原官方 RSS、X 策展 Quote、固定作者、AICG、HN、V2EX、Bilibili、GitHub 搜索、Reddit（部分）、DEV、HuggingFace 等来源。

## 数据正确性修复
- Hacker News `/item?id=1` 不再和 `?id=2` 混为一个实体；YouTube `watch?v=` 亦然。
- GitHub 原始 issue/PR/discussion 链接保留其路径；但**经确证的仓库项目实体**仍按 owner/repo 归并。
- 一篇引用 7 或 25 个工具的合集不会因为第一条 GitHub 链接而被当成单项目。
- 不同同源转发/同一个平台作者不是两个独立平台；保留每条可追溯原帖。
- 兼容平台原生分数、媒体元数据和抓取时间；不把 Product Hunt、HN、GitHub 和 X 的分数相互换算。

## 执行流
1. 原免费、公开数据采集器按旧配置执行。
2. `trend_feeds_v3.py` 从新增公开源获取**可读的发布/热门线索**，写 `external-discovery-hot-extra.json`。
3. `unified_topic_intake.py` 将新旧全部已取到的记录合入同一候选池，执行候选身份去重，仍无候选自动进入“可发”。
4. `reader_value_triage_v3.py` 按演示、教程、资源合集、项目、原生社媒书签信号为研究优先级分流，不自动完成九大价值人工审稿。
5. `channel_gap_audit_v3.py` 读取**实际 provider-status**，输出各来源返回/失败/缺失、X关键词空白和待接入优先级。

## 仍不等于完成
- 全 X 广域搜索因匿名第三方接口不可用，必须区分“引用网络可读”和“关键词搜索可用”。
- 抖音、小红书、TikTok、Instagram、Threads、YouTube完整热门榜与评论仍缺权限/稳定访问；不能绕过平台访问限制。
- 现有历史缓存来自 GitHub Actions，不等于永久数据库或 Google Sheet 最新正式发布状态。
- “累计发现量”与“用户认可合格选题量”没有直接因果关系；需至少七天并行比较。
- 不启动付费 Apify、不访问私有账户、不自动发布、不抓取并重新上传授权不明确的媒体。

## 验证
GitHub PR 必须先通过 `python -m unittest discover -s social-topic-radar/tests -v`，且真实 Actions 步骤产生 `channel-gap-audit-v3.json/.md`、`research-opportunity-v3.json` 和原平台健康报告，再考虑合并。新源失败将明确列为 unavailable，而不是记成成功或0个有效作品。

## 公开参考
- Product Hunt RSS: https://help.producthunt.com/en/articles/484970-does-product-hunt-have-an-rss-feed
- Product Hunt 官方 GraphQL 使用边界: https://www.producthunt.com/v2/docs
- Lobsters 官方 RSS: https://lobste.rs/hottest.rss
- Github Trending 第三方镜像项目: https://github.com/hanishrao/trending-collection

