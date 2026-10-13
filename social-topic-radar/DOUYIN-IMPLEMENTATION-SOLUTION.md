# 抖音 AI 赛道采集解决方案（2026-10-13）

## 验收目标与硬性限制

- 目标：关键词发现热门 AI 视频，读取视频详情/互动、一级评论与尽可能完整的二级回复，并自动形成可追溯的用户需求报告。
- 用户不提供抖音个人账户、不扫码、不导出个人 Cookie，允许临时游客会话；不增加费用；不得绕过访问控制、验证码、明确的风控与限流。
- 仅实际从作品接口和评论接口返回的正文与指标算数据。搜索索引摘要不算原始作品正文或评论。

## 根因（已由源码和实际日志确认）

### 搜索不是参数错误，而是实现缺失

- 已用免费演示 OpenAPI 及开源源码确认：在 Evil0ctal/Douyin_TikTok_Download_API v5 中，VIDEO_SEARCH / GENERAL_SEARCH 只是保留的 URL 常量，未注册为对外读取能力；MCP 把 ResourceKind.SEARCH 列入 _UNFETCHABLE。
- 参考日志：https://github.com/chenyang-99/codex/actions/runs/38379040099
- 独立免登录搜索工具 tamnd/douyin-cli 提供 search 命令，但其 README 明确说明数据中心及非中国 IP 的搜索/视频/评论会触发反自动化验证，不能把它误认为 GitHub 数据中心可用的解决方案。

### 二级回复被上游风控拒绝，但内嵌预览可读

- 异步任务真实错误码 UPSTREAM_RISK_CONTROL，endpoint=douyin.comment_replies，任务状态 failed。它代表免费服务判定平台拒绝当前游客身份；并非缺少 comment_id、父评论无回复或单纯客户端请求超时。
- 参考日志：https://github.com/chenyang-99/codex/actions/runs/38386812067
- 开源源码 src/dtk/platforms/douyin/parser.py 含 parse_reply_previews()，明确从一级评论原始 reply_comment 字段提取楼中楼预览。
- 已用 include_raw=true 的正常一级评论请求验证：16 条实际一级评论、4 条有回复计数的父评论、3 条真实内嵌回复文本，未请求独立回复接口。
- 参考日志：https://github.com/chenyang-99/codex/actions/runs/38387300258
- **3 条是一级响应内嵌回复预览，绝非完整楼中楼分页；完整楼中楼仍待获授权入口。**

## 已部署可执行链路

1. `douyin_creator_discovery.py`：3 条公共视频种子（用户可扩展），验证其视频详情，去重创作者，读取近期 5 条作品并以实际互动指标在**样本内**排序。
2. 同一采集程序对至多 2 条视频调用正常公开一级评论接口，使用 include_raw=true，提取顶层评论及在其中附带的 reply_comment 预览（不调用风控拒绝的 replies 接口）。
3. `social-topic-radar/domestic_painpoints.py`：把已取得的一级评论与二级回复预览分别标注 provenance 与级别，过滤表情、引流等低信息样本。
4. `social-topic-radar/editorial.py`：汇总 AI 视频原帖 URL、互动指标、可核查评论样本及未覆盖边界。
5. `.github/workflows/anonymous-social-probe.yml`：每日云端自动运行。GitHub Actions 是定时临时运行器，不是持久 VPS；免费 demo 可能限制、不可用，不能保证平台范围全量。

## 尚需独立解决的功能及路线

### 全站关键词搜索

- 当前 GitHub 条件下，改用**多来源关键词候选发现**而非宣称原生全站搜索：免费公开热榜 → AI 关键词过滤；公开搜索引擎/原始视频链接 → 原帖二次验证；已核实 AI 创作者作品列表 → 互动数据样本内排名。
- 每个来源增加字段 discovery_surface 与 coverage。只允许实测确有有效作品的入口进入长期定时采集；Google/Bing RSS 等此前实际失败的入口不应标为已解决。
- 外部公共搜索或定向发现无法保证覆盖抖音全站，需要标记为“已发现范围内候选”而不是“全站热搜第一”。
- 抖音官方 video.search / video.search.comment 的特殊权限只允许与申请方自身品牌/业务有关的关键词，最近一天，不适合任意泛 AI 赛道与竞争品牌全站搜索；用户没有授权官方应用。

### 完整楼中楼回复

- 现有上游 replies 接口返回 UPSTREAM_RISK_CONTROL，不再在任务中频繁触发；继续使用一级响应自带的**真实回复预览**作为可用子集。
- 只有在获得合法开放的、可读取完整楼中楼的另一授权服务后，才开启独立二级分页；目前仍是未解决项。

## 成功标准

- 作品搜索：真实返回对应 AI 关键词的不同创作者作品 URL，采样时间和数据范围明确；无结果标明来源受限。
- 互动榜单：只比较具有相同采样范围/时窗的指标；不得把自己的小样本误称抖音全站热门。
- 一级评论：保留真实文本、原视频 URL、返回样本数。
- 二级预览：保留 parent_comment_id、真实回复文本和 `is_full_thread=false`，单独计数。
- 完整楼中楼：实际通过获许可的专用回复分页取得正文和 has_more/cursor 等页码信息，才视为解决。
- 无人值守：程序按 GitHub 定时运行，并在来源故障时降级、写清原因；不得宣称永久稳定。

## 必须诚实说明

目前**有条件实现的免费能力**为：多个种子创作者作品、实际互动数据、部分真实一级评论、部分真实内嵌二级回复。**仍不能承诺**同一免费 GitHub 云端做到任意关键词的全站完整搜索＋所有二级回复。

相关上游源码：https://github.com/Evil0ctal/Douyin_TikTok_Download_API
开源备选搜索工具：https://github.com/tamnd/douyin-cli
抖音官方关键词视频管理：https://open.douyin.com/platform/resource/docs/ability/search-management/video/