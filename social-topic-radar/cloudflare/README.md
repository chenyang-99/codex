# 30天AI图文账号｜Cloudflare V3.2 运行系统

## 当前部署验收（2026-10-25）

**Cloudflare为唯一自动采集执行环境，GitHub只保留源码与配置备份。迁移范围尚未达到原Python执行环境的全部功能等价。**

- 原项目源码基线：`24a8413586fdc58276df2fb5e2b8a6b769161c3c`（2026-10-21封号前）。
- 当前 Worker：`ai30-original-radar-v32` — https://ai30-original-radar-v32.lc-20260909-edge.workers.dev
- D1 正式运行库：`77385365-96d9-4ec6-94ff-66843638efd0`。公开 GET `/health`、`/coverage`、`/readiness`、`/self-test`、`/quality-self-test`、`/quality-contract` 可访问，不提供公开写入/发帖接口。
- Cron：`0 * * * *`（UTC每小时整点），`ENABLE_COLLECTION=true`。每轮最多检查4个公开源，真实运行数据写D1；测试用的临时高频Cron已恢复。
- CF注册82源，43个启用、39个禁用。其中停权前24个RSS（Anthropic旧RSS经404验证暂停）、11个原创免费公开API/订阅入口、6组Google News免费站点间接索引、3组Hugging Face AICG官方模型/Spaces元数据；另有38个AICG/X创作者与站点只登记种子不自动抓取。
- Google News六组与原`indexed_social_discovery_v3.py`一致：X、抖音、小红书、TikTok、YouTube、Instagram。**站点索引不是平台原生搜索，也不是同平台热度。** 2026-10-24 18:00Z左右真实检查：X/Instagram/TikTok索引返回可读线索，抖音索引为空，小红书和YouTube遇HTTP503；任何后续状态以D1`cf_source_health_overview`为准。
- Hugging Face图片模型、视频模型、新建视觉Spaces三组一手公开API实际返回；**图像、视频原作尚未观看，不能判审美精品或复制发布。**
- 2026-10-24 18:04Z时：D1记录378条证据、367个独立研究实体，发现11个跨来源重复实体；这些都待实际事实审核，已被CF私有视图`cf_research_review_queue`隔离。所有记录默认`pending`，没有自动批准。
- 原`topic_quality_gate.py`的一部分**结构性阻断**已迁到CF：九大价值只准一个主价值、对应的来源和专类兑现证据、原生社交提案、四维评分上限25/30/30/15、下限20/23/21/10、总分至少85、原始证据以及X普通短帖保守280权重。新增五项合成回归已真实通过（缺证阻断、完整结构只进入人工复核、低分阻断、未看作品阻断、X权重长度）。**这不是Python历史119测试完整复现，不证明真实内容质量，更不构成用户发布授权。**
- 原v3.1出稿十项P0审稿由现有ChatGPT插件与`.agents/skills/ai-copy-production`、`scripts/delivery_release_gate.py`承接；原稿的最终审核与人工发布由用户操作。CF不登录平台、不自动发布。

## 旧Cloudflare系统清退

- 原 Worker `open-topic-radar-v01` 和原D1 `f3d49164-48d0-49d4-8548-8df95bb3eaa2` 均已删除。
- 删除前完整复制17张表、1467条记录（313条原始采集记录，496926字节）和30项索引/视图/触发器/表定义；与原数据库逐行比对成功。非运行CF归档D1：`ai30-legacy-data-archive-20261024`，ID `2f13e2a4-ccae-4d67-85c9-8a6b13f25fc1`。
- 旧数据库另以gzip+Base64和每分页SHA256存储于私有Google Drive恢复保全子文件夹： https://drive.google.com/drive/folders/1r5SFEMvDnUAr6IoDugE2GrQM2qvbxYg1 。两份归档包括16表1154行以及原始内容313行，已全部读回核数，并抽样完成真正gzip解压及SHA256验证。不是自动可导入SQL文件，也不是每一段逐一重算SHA256。
- 其它Cloudflare Worker `aws-sub`、`edge-tunnel-main` 无关，未动；Cloudflare R2尚未启用。

## 未完成及不允许虚报

- 原X全域关键词检索和20位AICG作者的第三方Python读取器，尚无等价的无凭证Cloudflare入口；未取得合法授权不得绕过平台权限。
- 抖音、小红书原生热榜、作品和评论采集尚未完成；可得的Google News索引线索不代表原生覆盖。
- 原AICG十处公开站点的具体作品发现、媒体实看、画质与版权审核、原119项Python代码测试并未完成CF等价验收。
- 出稿十项P0完整机器验收未在CF执行，仍由ChatGPT现有技能/编辑实际完成；原始发布数据只来自用户。
- 仍需要对更多来源与长时间稳定性、额度、业务选题通过率持续验证，不能因Worker健康页正常就声称全套完成。

恢复和使用流程参考 `RUNBOOK.md`。 `schema.sql`、`sources-registry.json`、`worker.js`、`wrangler.toml`为备份配置，不包含密钥、私人素材和用户业务数据。
