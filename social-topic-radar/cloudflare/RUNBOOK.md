# Cloudflare AI30｜执行与审计操作手册

原项目总控： https://docs.google.com/document/d/1Jw9zjaNnEy9ixfuNSinf7ZL3Zh72wF7otLPD3rdyGZc/edit

原运营台账： https://docs.google.com/spreadsheets/d/1P9hGNDJmwil7KnWmUm7Y2IlPp1BRK3-erPdQ7fhHyQA/edit

唯一自动采集环境是Cloudflare Worker `ai30-original-radar-v32` 与独立D1 `77385365-96d9-4ec6-94ff-66843638efd0`。Cron `0 * * * *` UTC、`ENABLE_COLLECTION=true`、每轮最多4源。GitHub只备份，不启用任何GitHub Actions；ChatGPT现装插件保持不变。

## 每次读取实时状态（只读）
```sql
SELECT started_utc,finished_utc,status,feeds_checked,retrieved,new_entities,errors_json FROM runs ORDER BY started_utc DESC LIMIT 10;
SELECT source_id,name,kind,enabled,last_probe_status,last_probe_items,last_probe_error FROM cf_source_health_overview ORDER BY last_checked_utc DESC LIMIT 50;
SELECT entity_key,title,source_url,cross_source_count,editorial_state,mechanical_qa_state FROM cf_research_review_queue ORDER BY first_seen_utc DESC LIMIT 40;
```

`sources-registry.json`仅是某次公开来源配置快照，不代表所有源实际可访问，`indexed_rss`不是原生平台热度。候选永远先做历史台账全量查重、原始来源核实、九价值兑现、人审+事实/版权/视觉核查；未人工完成前只叫研究线索。批准选题进入ChatGPT原 `ai-copy-production v3.1` 十项P0验收；用户自己复制/发布。任何部署步骤不得把历史pending改成published。

## 代码恢复与数据恢复
`worker.js`是Cloudflare实部署源码、`schema.sql`是生产D1 schema、`sources-registry.json`是来源配置、`wrangler.toml`是非敏感Cron/绑定声明。需要重建时在Cloudflare新建D1、应用结构、导入来源配置、配置DB绑定，然后先只读健康测试再打开Cron；不要在GitHub创建动作运行器。部署前请核对Worker绑定和所有付费源默认关闭。旧CF原数据库已经删除，历史资料独立保存在无Worker绑定的D1 `2f13e2a4-ccae-4d67-85c9-8a6b13f25fc1`，与私有Google Drive备份 https://drive.google.com/drive/folders/1r5SFEMvDnUAr6IoDugE2GrQM2qvbxYg1 。历史逻辑归档需要按每段Base64解码、gzip解压、SHA256与行数校验；raw_payloads的bytes_hex须保留原sqlite_type。原30项DDL位于私有Docs备份，而不是此生产schema。

零默认付费，不启用Apify等未批准服务；平台403/429不绕过，AICG未看真实作品不能打高分。只有用户实际完成发布才能记published。
