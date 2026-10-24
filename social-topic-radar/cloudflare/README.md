# 30天图文账号｜Cloudflare V3.2 运行与迁移验收

**架构**：Cloudflare 是唯一自动采集执行环境，GitHub 只备份源码/非敏感配置；ChatGPT 现装插件和 Google Docs/Sheets 仍承担编辑运营与唯一业务台账。原历史 GitHub 源码基线 `24a8413586fdc58276df2fb5e2b8a6b769161c3c`。**原系统全功能等价尚未完成，尤其是X原生、抖音/小红书原生以及人工视觉审核。**

## 实际部署（2026-10-25）

- Worker `ai30-original-radar-v32`：https://ai30-original-radar-v32.lc-20260909-edge.workers.dev
- D1运行库 `77385365-96d9-4ec6-94ff-66843638efd0`；每小时 `0 * * * *` UTC、`ENABLE_COLLECTION=true`、每次轮转最多4个公开来源；测试临时高频Cron已恢复。
- 82个来源：53个启用（包括原24条RSS但已暂停404的Anthropic RSS、11条补充公开API/订阅、6条免费Google News间接站点索引、3条HF官方AICG模型/Spaces流、10个AICG白名单公开站点），29个禁用（20个X AICG作者和8个不支持/未授权AICG站点等，以及坏RSS）。
- AICG公开站点首轮10个全部真实测试：Replicate Collections、Recraft Blog、Black Forest Labs Blog、Higgsfield Community、ComfyUI Workflows、Luma Learning Center有符合规则的项目页元数据；Krea Community Apps、Runway AI Festival、Google DeepMind Blog、Runway Academy未解析出合格独立项目页。Recraft大HTML通过限制前360KB读取后恢复。**这些只是来源详情元数据；图片和视频尚未观看，版权/审美/素材质量均未验证。**
- 6组站点搜索索引：X、Instagram、TikTok在真实运行曾返回；抖音索引为空；小红书、YouTube索引遇HTTP503。**间接搜索引擎结果不是原生平台热榜或帖子内容，不能称已打通抖音/小红书/X全域。**
- CF运行库于2026-10-24T18:23Z验收：17次运行记录、434条证据、421个去重研究实体（含跨来源合并），421个待审核。**自动发布=禁用，自动选题批准=禁用。**
- `/health`、`/coverage`、`/readiness`、`/self-test`、`/quality-self-test`、`/quality-contract` 外部只读；`/quality-self-test`5项正反合成契约检查通过。结构门槛与原 `topic_quality_gate.py` 关键条件对齐：九大读者价值一项主价值、四维总分≥85及分项阈值、原始证据、社媒原生说服、AICG作品未实看阻断、普通X短帖保守280权重。**不是所有原Python 119项测试的同环境回归，不保证视觉质量、内容真实或传播成绩。**
- GitHub所有9个旧Actions从main撤除；GitHub任何备份提交都不触发旧采集。每周日ChatGPT定期备份任务读实际CF代码和配置并仅在变化时更新GitHub；不保存token、用户D1业务数据。
- 当前实际 Worker 源码 `worker.js` 与 Cloudflare 部署字节 SHA(Git blob)逐字节一致。配置快照 `wrangler.toml`、`schema.sql`、`sources-registry.json`、`RUNBOOK.md` 随源归档。

## 清退前旧CF数据保全

旧 Worker `open-topic-radar-v01` 及其旧D1均已删除，旧D1的17表/1467行（313份原始内容）与30项DDL在删除前逐行逐定义复制核对；只读历史CF归档D1为 `ai30-legacy-data-archive-20261024`（`2f13e2a4-ccae-4d67-85c9-8a6b13f25fc1`），它不绑定运行Worker。旧数据另以私有 Google Drive gzip+Base64分页+SHA256归档： https://drive.google.com/drive/folders/1r5SFEMvDnUAr6IoDugE2GrQM2qvbxYg1 。跨平台备份条数已完整核对，抽样分页解压哈希验证通过，不是已自动转换为可直接导入的SQL文件。

## 尚未具备的功能（不可虚报为已完成）

1. X全域搜索、20位AICG创作者实际帖文及视频/图片原作读取；原第三方Python pinned reader在Workers未移植，需单独核实合法接入方式。
2. 抖音、小红书平台原生热门帖、评论/互动采集（Google News只返回公开间接索引）。
3. AICG原始图片或视频实看、主观画质40/45与≥85/100等门槛、版权和素材二次使用授权。
4. 原119项Python CI测试在Cloudflare上的完全等价执行；出稿V3.1十项P0终审仍由ChatGPT插件/主编在对话中完成，未移植成CF自动运行器。
5. 长时间稳定性/真实成本/运营实际采纳率验收；来源HTTP429/503/404必须原样记录，不绕过限制。

**真实发布仍由用户手动执行；没有提供数据的粉丝、传播和收入保持未知。** 详细状态及维护流程见 `RUNBOOK.md`。
