# Cloudflare操作与跨会话恢复手册（仅CF运行，GitHub备份）

**权威业务资料**：原Google Docs项目总控 https://docs.google.com/document/d/1Jw9zjaNnEy9ixfuNSinf7ZL3Zh72wF7otLPD3rdyGZc/edit 及原Google Sheets运营台账 https://docs.google.com/spreadsheets/d/1P9hGNDJmwil7KnWmUm7Y2IlPp1BRK3-erPdQ7fhHyQA/edit 。

## 每次执行和验收
先读业务权威文件；然后用已连接的Cloudflare只读查询当前D1运行库（不要按GitHub静态备份判断当日真实采集状态）。推荐SQL：

```sql
SELECT run_id,started_utc,finished_utc,status,feeds_checked,retrieved,new_entities,errors_json FROM runs ORDER BY started_utc DESC LIMIT 10;
SELECT source_id,name,kind,enabled,last_probe_status,last_probe_items,last_probe_error FROM cf_source_health_overview ORDER BY last_checked_utc DESC LIMIT 40;
SELECT entity_key,title,source_url,first_seen_utc,cross_source_count,editorial_state,mechanical_qa_state FROM cf_research_review_queue ORDER BY first_seen_utc DESC LIMIT 30;
```

D1中的研究线索与实时评分不是正式推荐，机器质量结构检查可能只告诉你字段是否完整。仍须核验原文/原图视频、适用受众、九大价值兑现、同平台热度及既有运营台账全量查重；用户认可后才能进入出稿阶段。ChatGPT调用原`ai-copy-production v3.1`和现有插件制作完整主稿并完成十项P0、平台规格、版权/广告说明及原稿保真，只有用户真实手动发布才记为published。

## 独立恢复步骤
1. 备份源码取`worker.js`，非敏感来源配置取`sources-registry.json`，D1结构取`schema.sql`，触发器取`wrangler.toml`。不得启用GitHub Actions，且不得将历史CF雷达旧源码当生产系统。
2. 在Cloudflare创建新D1，导入schema，按`sources-registry.json`写入来源元数据，重新绑定Worker `DB`，迁移完成才启用Cron。外部 HTTP不应暴露写接口。
3. 旧CF历史归档保持与新业务库独立；原数据库已删除。跨平台恢复分段文件位于Google Drive私有保全目录。按每段 `TABLE_PART_BEGIN ... sha256=... encoding=gzip_base64` 和 `TABLE_PART_END` 读取正文，解Base64再gzip解压，核对SHA256与记录行数。 `raw_payloads` 字段 `bytes_hex` 必须按 `original_type`（SQLite TEXT/BLOB）恢复。依历史 `SCHEMA_JSON_BEGIN` 的原始30项DDL恢复结构，不可只拿GitHub新系统的schema恢复旧历史数据。
4. GitHub仅定期备份非敏感部署代码与Schema，禁止上传D1业务数据、密钥、原始素材或发布账号凭据。当前安装插件保持不变。

## 费用/平台边界
免费公开RSS/API及Google News站点索引优先。遇403、404、429、503如实记录source-health，不使用隐身/代理或绕过授权，不默认开启Apify或其他付费服务。不自动发帖，不根据机器分数伪造播放量/粉丝/商业线索。
