# Cloudflare V3.2 迁移｜30天图文账号

> **已部署阶段二并启用受控、每小时公开来源采集；完整原系统功能等价尚未验收。** GitHub 仅负责非敏感源代码/结构备份，不再运行原 GitHub Actions。

## 当前基础设施（2026-10-24）

- 原项目基线：GitHub commit `24a8413586fdc58276df2fb5e2b8a6b769161c3c`，原 AI Topic Research v2.2、AI Copy Production v3.1、X 内容适配规则继续保留。
- Cloudflare 主执行 Worker：`ai30-original-radar-v32`，地址 https://ai30-original-radar-v32.lc-20260909-edge.workers.dev 。已实测 `/health`、`/readiness`、`/coverage`、`/self-test` HTTP 响应；静态 self-test 通过，不等于外部采集回归通过。
- 生产 D1：`ai30-original-radar-v32`，ID `77385365-96d9-4ec6-94ff-66843638efd0`。共 73 个注册来源：24 条停权前 RSS、11 个原脚本支持的免费公开 API/订阅入口（共 35 个启用）、20 个 X AICG 作者种子及 18 个 AICG 站点种子（共 38 个禁用，未经验证不冒充已采集）。
- 采集通过 CF Workers `scheduled` 执行：`0 * * * *`（每小时整点 UTC），绑定 `ENABLE_COLLECTION=true`；每次最多 4 个公开来源，轮转检查，保留每源 HTTP 失败和所见样本数，使用 D1 做跨运行实体去重。
- 自动选题/自动发布：始终为 **否**。九大读者价值仅初始化 `not_assessed`，不得把元数据标签或关键词归类当成人工审稿结论。用户自行复制发布。外部 HTTP 仅提供只读接口，不能触发采集和发帖。
- 当前**未通过完整业务回归**：X 全域关键词、AICG 作品实看/画质门槛、抖音/小红书真实原生采集、GitHub 原 119 项 Python 单测在 CF 上等价通过、完整审核和出稿串联。不得将 35 个启用来源报告为 35 个已采集成功。
- GitHub 主分支已移除全部 9 个旧 `.github/workflows` 执行定义。现役 CF Worker 实际源文件存于 `worker.js`；数据结构仅保留 `schema.sql`；配置记录 `wrangler.toml` 不含任何密钥。每周自动检查与备份由 ChatGPT 任务执行，不依靠 GitHub Actions。

## 旧 CF 系统清退与数据保全

- 旧 Worker `open-topic-radar-v01` **已删除**，旧 D1 `open-topic-radar-v01`（`f3d49164-48d0-49d4-8548-8df95bb3eaa2`）**已删除**。
- 删除前将全部 17 张业务表、10 个视图、2 个触发器、1 个独立索引及 1,467 条业务记录完整复制到不绑定任何运行 Worker 的 D1 历史归档库：`ai30-legacy-data-archive-20261024`（`2f13e2a4-ccae-4d67-85c9-8a6b13f25fc1`）。
- 原始采集记录 `raw_payloads` 313 行，包括 496,926 UTF-8 字节，BLOB/TEXT 类型逐行检验；全部 17 表的记录内容与原始库逐行相等，30 个非系统 DDL 定义相等后才删除原 D1。
- 归档库仍在 **同一 Cloudflare 账户**，不是跨账号/跨服务灾备。Cloudflare R2 当前未启用，无法直接完成可独立离线还原的 SQL 文件归档；历史档案不得误标为已做离线备份。
- 另外两个无关 Workers `aws-sub`、`edge-tunnel-main` 未动。

## 后续验收

1. 监控首次 CF Cron 真正执行、记录成功源/失败源和成本；运行前 35 个来源仍只有登记状态。
2. 在公共访问政策允许范围内完善多源采集，不绕过 X、抖音、小红书等平台权限。
3. 补齐原 `topic_quality_gate.py`、九大价值人工审稿、AICG 源图/视频检查，以及与当前已安装插件、原 Google Docs/Sheets 的衔接；正式可发选题不得由规则脚本自动批准。
4. 获取 CF 历史归档库**跨服务离线备份**，在此之前保留当前 CF 归档库。
5. 全部功能与源码/源数据可追溯性验收成功后才能称作完整生产迁移。

业务数据的唯一权威入口仍是原 Google Docs 项目总控与原 Google Sheets 运营台账；本 GitHub 目录不存储密钥、D1 业务记录和真实运营私密数据。
