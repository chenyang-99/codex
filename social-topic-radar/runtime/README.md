# 30天图文账号：Cloudflare 生产运行源码备份

本目录是**同一个** `social-topic-radar` 项目中的 Cloudflare 运行源码备份，**不是**新的雷达项目、同步代理或第二套生产服务。GitHub 保存经过核查的 CF 生产快照；目前由 Cloudflare 独立运行。修改 Cloudflare 后，必须再次获取**实际已部署**的代码并写入本目录核对。

## 快照

- 备份日期：2026-10-24
- Cloudflare Worker：`open-topic-radar-v01`
- 生产 deployment：`ef8ed58d-d679-45ff-842b-9f2817bd514a`
- 生产 Worker version：`c1dc6e2d-0801-4c1a-b6a7-1fb235133e1f`，100% 流量
- 代码：`entry.py`、`models.py`、`source_config.py`，从 Cloudflare 实际部署读取；均经过 GitHub 读取比对
- 运行配置：`wrangler.toml`，反映当次 compatibility flags 与 D1 绑定
- 数据库定义：`schema.sql`，仅建表、索引、触发器及视图；已省略平台内部 `_cf_KV` 表
- 来源范围：原 64 个注册来源（53 活跃 + 11 暂停）；本次未改动名单
- Cron：无；自动采集与推送仅为待办，未授权运行
- 本目录**不含** D1 记录、ADMIN_KEY、API 密钥、Cloudflare 凭据，也不承诺已做本地独立运行验收

## 在 Cloudflare 恢复

备份的是源码和架构配置。以下是恢复操作流程示例，**尚未在新 Cloudflare 账号执行端到端重建验收**：

1. 将原 GitHub 仓库克隆到受控环境，进入 `social-topic-radar/runtime`。
2. 在 Cloudflare 中创建 D1 数据库 `open-topic-radar-v01`，并把新 database_id 写入 `wrangler.toml`（如果原 D1 仍在，使用其现有绑定 ID）。
3. 在具备权限的环境执行 `npx wrangler d1 execute open-topic-radar-v01 --remote --file=./schema.sql`，恢复**空数据库结构**。在生产数据库执行前必须先确认目标数据库为空、核实 DDL 兼容。
4. 安全地执行 `npx wrangler secret put ADMIN_KEY`，并按需要在合规授权后配置其他密钥；不要将任何密钥写进 GitHub。
5. 在正确的 Cloudflare 账号执行 `npx wrangler deploy`，按需访问 `/health` 并执行只读/低风险冒烟验证；对照原有 53/11 范围验收。
6. D1 的历史运行数据和人工研究记录不是这些源码文件的一部分。要恢复过去的数据，需要**独立、加密的非公开 D1 导出备份**；GitHub 公共仓库不适合存放原始业务记录、授权令牌或用户数据。

## 以后每次变更的备份约定

Cloudflare 仍是当前生产运行端。每次成功修改、验证 CF 生产版本后，同一次任务：
- 从**实际部署**取回三个代码文件和最新 settings/schedules。
- 与本目录做差异核查，更新受影响文件、`wrangler.toml`、`schema.sql`（如 DDL 发生改变）及版本清单。
- 提交 GitHub，读取核对源码完整性；明确记录 Git commit 与 CF version。若提交失败，向用户明确说明，不得声称备份成功。
- 不上传密钥、D1 业务数据，不启动独立采集服务，不默认为 CF 开启 Cron。

旧 `social-topic-radar/*.py` 文件保留为原项目的历史代码与测试材料，不能用它们冒充当前 CF 生产源码，也不能将 GitHub 旧 Actions 的定时采集误称已经关闭。
