# Cloudflare 迁移｜30天图文账号 V3.2

> **状态：隔离部署已上线，但完整迁移未通过验收。** 本目录保存 Cloudflare 实际运行代码及非敏感配置，以便 GitHub 只做源码备份。

- 封号前源码基线：`24a8413586fdc58276df2fb5e2b8a6b769161c3c`（2026-10-21）。
- Cloudflare staging Worker：`ai30-original-radar-v32`，GET `/health` 与 GET `/readiness` 已从外部请求验证。
- 运行地址：`https://ai30-original-radar-v32.lc-20260909-edge.workers.dev`。
- D1：`ai30-original-radar-v32`，ID `77385365-96d9-4ec6-94ff-66843638efd0`，已导入原24条RSS来源与源自原代码的数据库模式。
- 已部署源码：`worker.js` 从 Cloudflare 实际已部署版本重新获取，并已对照；`schema.sql` 从新 D1 实际表定义重新读取。
- 旧 Cloudflare Worker `open-topic-radar-v01` **已经删除**；另外两个无关 Worker `aws-sub` 与 `edge-tunnel-main` 未动。
- 旧 D1 `open-topic-radar-v01` ID `f3d49164-48d0-49d4-8548-8df95bb3eaa2` **保留为历史数据隔离档案**，其SQL导出在CF侧生成，但尚未取得独立长期可恢复的数据文件，所以**不得删除旧D1**。
- CF Cron：**空**；`ENABLE_COLLECTION` 未配置，任何外部HTTP均不能触发采集或发帖。
- GitHub：`.github/workflows/` 下全部9条旧Actions定义已从main撤除；仓库不再执行采集、测试或发布。历史工作流保留在归档分支供阅读。
- 备份：已配置ChatGPT每周检查Cloudflare生产Worker源文件、schema及部署清单，仅有变化才写GitHub；从不上传密钥及业务数据。

## 未完成的完整迁移项目

1. 将原 `social-topic-radar` 下跨平台采集、AICG、X策展、国内公开渠道、V3合并去重、渠道健康与证据追溯、九大价值审核和自动化机械回归实现为Cloudflare运行路径，真实对照源程序输出。
2. 对每个已移植的公开来源实际采样，保留403/429/错误的真实失败状态；不能把RSS数量冒充多平台已覆盖。
3. 与恢复后的Google Docs及Google Sheets原始业务主控联通，保持ChatGPT/编辑的人审和人工发布边界。
4. 首次全链路实测后再评估成本、权限、频率，决定是否启用Cloudflare Cron。**不能因为Worker部署成功就宣称旧Github运行功能全部迁移。**
5. 对旧D1获得独立长期备份（包括数据和schema）并校验后，才可根据需要销毁隔离库。

## 恢复与安全

代码库历史快照：`archive/2026-10-24-before-full-restore` 含旧Cloudflare R84源码；`restore/2026-10-21-pre-suspension` 固定原GitHub停权前提交。即使GitHub只作为备份，也不在该仓库执行任何任务。
