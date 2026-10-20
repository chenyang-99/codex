# AI选题研究审核 JSON · v1.2（2026-10-19用户纠偏）

## 基本原则
- **硬门槛只有两项：吸引力 + 传播潜力**（均须清楚可核验的理由）。
- 收藏、学习、认知、决策、情绪、娱乐等是**可替代或组合的读者价值**，不强迫每条文章有Prompt或教程。
- 仍要求明确读者回报、原始证据、差异化、诚信与平台规则；“传播潜力”是编辑评估，不保证播放。
- 正式推荐总分≥85，且分项≥20/23/21/10（分别对应吸引力25、传播30、读者回报30、可信与原创15）；未人工评分只能探索。
- 顶级AICG作品另有视觉审查门槛，作品没Prompt依然可能合格，只要真实画面达标且传播理由充分。

## 人工研究档案 JSON 示例（模拟数据，不可直接当真实稿件或热度证据）

```json
{
  "rejected": ["old-rejected-topic"],
  "known_problem_keys": ["old-topic-key"],
  "topics": [
    {
      "topic_id": "example-01",
      "problem_key": "story-about-ai-creator",
      "title": "一位创作者为什么放弃看似完美的AI画面？",
      "audience": "AICG创作者与普通观众",
      "trigger": "专业创作者公开解释一个不寻常的创作决定",
      "job": "理解为什么风格选择能够影响故事",
      "outcome": "一则能引发讨论且经过核实的独到分析",
      "value_type": "认知",
      "angle": "从观众情绪而不是技术参数拆解",
      "promise": "解释创作者选择及可查事实",
      "proof_plan": "阅读原作者完整说明并核对影片画面",
      "competitor_gap": "仅展示美图、缺乏艺术决策分析（待查）",
      "difference_rationale": "有原作者解释及客观对照",
      "source_limitations": "未代表全体创作者；热度未知",
      "requires_test": true,
      "test_gap": "尚未实际观看完整作品",
      "content_values": {
        "attraction": "开头呈现完美与不完美画面的鲜明对比（需要真实画面）",
        "spread_mechanism": "艺术设计取舍引发有证据的立场讨论",
        "payoff_type": "insight",
        "payoff_description": "读者理解审美选择并获得独立判断",
        "spread_class": "fresh_potential",
        "spread_source_url": "https://example.org/creator-work",
        "original_published_at": "2026-10-19",
        "freshness_reason": "最新原作者公开说明（样例字段，待真实核验）"
      },
      "value_scan": {
        "utility":"not_applicable","learning":"not_applicable",
        "save":"not_applicable","decision":"not_applicable",
        "insight":"primary","information":"not_applicable",
        "emotion":"secondary","entertainment":"not_applicable",
        "social_expression":"not_applicable"
      },
      "value_proof": {
        "source_url":"https://example.org/creator-work",
        "source_access":"original_viewed",
        "evidence_status":"source_reviewed",
        "observed_material":"已查看原作者的两段对照镜头（模拟样本）",
        "reader_deliverable":"一个可根据画面反差检验的审美选择解释",
        "verification_check":"对照原视频画面及原作者文字说明",
        "limitations":"示范字段；不得当作真实观看和核实记录",
        "category_evidence":{
          "prior_understanding":"原先认为最佳画面只取决于清晰度",
          "new_interpretation":"镜头表达可能优先于单纯细节丰富度",
          "supporting_observation":"需从实际可观看的片段中引用一个具体例子"
        }
      },
      "social_pitch": {
        "platform": "x",
        "first_screen": "原作品中的两幅真实对照画面，须获合法展示来源（样例）",
        "proof_object": "原作者可回查的原创视频和逐镜头说明（样例）",
        "why_share_or_save": "创作者可收藏本次镜头取舍和具体对比（样例）",
        "account_fit": "对照本账号AI漫画资源帖正向表现，此处仅为示范，不代表同题流量（样例）",
        "support_type": "original_work",
        "support_url": "https://example.org/creator-work",
        "support_observation": "已读原作并看到视觉差异（样例数据非真实核查）",
        "original_published_at": "2026-10-19",
        "editorial_hypothesis": "如果同题内容目前缺原始视觉对照，可能有收藏价值（仅假说）"
      },
      "score_evidence": {
        "attraction": "能在第一屏展示原作对照，仍需合法素材验证（样例）",
        "spread": "创作者会围绕视觉取舍讨论，未实测传播（样例）",
        "payoff": "可以带走一套具体镜头判断方式（样例）",
        "credibility": "有原作者一手资料，未完成独立复现（样例）"
      },
      "content_scores": {
        "attraction": 23,
        "spread": 26,
        "payoff": 27,
        "credibility": 12
      },
      "signals": [
        {"kind":"original_case","url":"https://example.org/creator-work","observed_result":"原作者完整说明","read_scope":"actually_read_original"}
      ]
    }
  ]
}
```

## 与出稿系统v2.6的价值标签兼容（2026-10-19）

选题与出稿两套机械检查现在采用同一组 `content_values.payoff_type` / `value_delivery.primary_payoff_type` 代码：
`utility`（实用）、`learning`（学习）、`save`（收藏资料）、`insight`（认知）、`decision`（决策）、`information`（信息发现）、`emotion`（情绪）、`entertainment`（审美娱乐）、`social_expression`（社交表达）。允许仅选择**一项**强主导价值，不强制收藏或教程。选题档案兼容旧版 `value_type` 中文标签，并增加“学习、收藏、信息、审美娱乐、社交表达”；旧数据无需批量修改。

更新的是**类型兼容性**，不是评分豁免：吸引力、传播潜力、读者回报、来源可信与原创增量分项及总分硬门槛一律保留；机器不验证一条新闻的时效真实性，也不证明审美效果。所有价值仍须以原始证据和人审说明具体兑现内容。

## 2026-10-20｜V2.1.6 社媒原生审核的新增硬字段

`topic_quality_gate.py review` 现在要求 `social_pitch` 和四维 `score_evidence`。它们是申请进入“元数据过关的编辑候选”的前置条件，不替代真人判断或用户批准。

- `social_pitch.platform` 必须为 `x`、`xiaohongshu`、`douyin` 之一（先明确首发平台）。
- `first_screen` 必须给出真实而具体的第一屏内容；`proof_object` 是可见的原始实物/作品/对照或足够扎实的短论证，不能仅填“新品介绍”。
- `why_share_or_save` 指向哪类实际受众为什么愿意收藏、转述或评论；`account_fit` 说明与本账号样本的适配证据或其局限；`support_observation` 说明原材料里具体观察到什么。
- `support_type=own_post` 或 `same_platform_post` 时要求 `support_url`、`support_metric`、`support_checked_at`；只有来源数据符合平台/时间口径才能作为社媒验证。
- `support_type=original_work` 时要求 `support_url`、`original_published_at`、`editorial_hypothesis`；只表示存在可核原作和编辑预测，不等于已在平台表现突出。
- `score_evidence` 中 `attraction`、`spread`、`payoff`、`credibility` 的逐项依据均不能为空；旧 `content_scores` 总分高也不能跳过。
- `review_one` 返回的 `human_editorial_approval=false` 与 `social_native_verdict=manual_content_review_required` 提醒：机器通过≠真人内容审核通过≠正式发布许可。

本附录是格式样例，示例 `example.org` 与假设场景没有平台热度、真实采集或人工实操证明，不得直接以此示例申报选题。

## 字段与边界

`content_values.attraction`（必填）：第一屏/前三秒真实而具体的看点，不能空喊爆炸。

`content_values.spread_mechanism`（必填）：具体哪类观众为什么会转发/讨论/共鸣。

`content_values.payoff_type`（必填、选最主要）：`save`、`learning`、`insight`、`decision`、`emotion`、`entertainment`；其他维度可在正文自然兼有，不设排他性强制。

`content_values.payoff_description`（必填）：观众看完实际得到什么。收藏类可给保存材料；观点可给判断；故事可给情绪体验。可选 `save_asset` 和 `learning_outcome`，**不存在时不作缺项处罚**。

`content_values.spread_class`：A=`verified_viral`，必须同时附 `spread_metric`（平台＋真实指标）和 `spread_checked_at`（核验时间）；B=`fresh_potential` 必须附 `original_published_at` 和 `freshness_reason`。无可靠依据则C=`unverified`，不得进入正式选题。

`content_values.spread_source_url`：同一原始来源的可回查深链。引用第三方统计注明渠道并区分官方数据。

`content_scores`：人工显式输入 attraction 0—25、spread 0—30、payoff 0—30、credibility 0—15，总分≥85且单项≥20/23/21/10。无 `content_scores` 为探索；旧版 `four_values` / `four_value_scores` 并非v1.2有效完整档案，需按类型重新审核，不要自动继承旧分。

真实来源 `signals[].kind` 限 `user_post`、`user_comment`、`official_release`（有claim）、`original_case`（有observed_result）；搜索摘要和无法打开的素材仅是线索。用户否定、跨天重复、IP/肖像/商标版权、安全合规及未经验证的本人亲测仍可一票否决。

`editorial_candidate` 仅代表机械资料门槛通过，不表示内容已复刻成功、用户审稿通过或已发布。

## 2026-10-20｜九大价值兑现证据门禁（本分支升级草案）

原有九类 `payoff_type` 保持不变。**逐条扫描九类，不表示九种价值必须同时具备。** 每条只允许一个 `primary`，可有 `secondary`，其余标 `not_applicable`。中文 `value_type` 必须与主导的英文 `payoff_type` 一致。不能拿高的四维 `content_scores` 绕过这道证据门禁。

**新增 `value_scan`**：键固定为 `utility,learning,save,decision,insight,information,emotion,entertainment,social_expression` 九项，值只能是 `primary/secondary/not_applicable`。各项只表示是否适合素材；无需九项都高分，不规定每批配比。

**新增 `value_proof`**：

- `source_url` 必须是 `signals[].url` 中记录的原始材料 URL，不能凭空造一个可点链接。若尚未读取材料，就标研究线索，**不要伪造 `source_reviewed`**。
- `source_access`：`original_read`、`original_viewed`、`official_document_read`、`independently_tested`；审美娱乐作品必须是后两种中的 `original_viewed` 或 `independently_tested`。
- `evidence_status` 仅在确已完成上述查阅时填 `source_reviewed`，真的独立执行过才用 `independently_tested`；未核实应填 `pending`，会阻断正式候选。
- `observed_material`：真正看到/读到的具体片段、数据或成品；`reader_deliverable`：读者实际拿到的内容/体验；`verification_check`：如何检查是否兑现；`limitations`：范围、成本、设备、授权及误差边界。
- `category_evidence` 必须包含与主价值对应的以下**三个专用字段**，并填入与原始材料相关的实质内容：

| 主导价值 | 必需证据字段 | 不能仅靠什么充数 |
|---|---|---|
| 实用 `utility` | `task_input`、`deliverable_example`、`success_check` | “这个工具可能方便” |
| 学习 `learning` | `teachable_skill`、`steps_and_prerequisites`、`learner_verification` | “教你掌握 AI” |
| 收藏 `save` | `reusable_asset`、`access_conditions`、`reuse_scenario` | 只有资源名称、没有真实入口 |
| 决策 `decision` | `options_compared`、`tradeoffs`、`decision_rule` | 一方厂商宣称降价 |
| 认知 `insight` | `prior_understanding`、`new_interpretation`、`supporting_observation` | 给新闻加“反直觉”标题 |
| 信息 `information` | `new_fact`、`event_date`、`reader_impact` | “某公司又发布新模型” |
| 情绪 `emotion` | `specific_story`、`emotional_turn`、`audience_connection` | “令人感动”的空洞评价 |
| 审美娱乐 `entertainment` | `actually_viewed_work`、`standout_moment`、`experience_reason` | 未实际观看的媒体标题/缩略图 |
| 社交表达 `social_expression` | `discussion_question`、`grounded_positions`、`reason_to_express` | 制造没有事实基础的争议 |

**流程与诚实边界**：九价值审查应位于产品/热点发现之后、四维排名之前，由人审先选定主价值、检查原始材料和可兑现内容；字段不齐时审核器返回 `blocked`，无法自行把研究线索升为精选。机器可以验证类型、字段、URL是否与来源登记一致及部分口径逻辑，**不能自动判定文案深度、画质、情绪、真实读者需求或数据真假**。机械候选仍返回 `human_editorial_approval=false`、`value_proof_verdict=manual_value_review_required`。

旧档案不批量重写：再次推荐前补齐 `value_scan` 和 `value_proof`。对已经明确否决的题仍执行历史阻断；不因改标题或换价值标签绕过。经过真人精选以后才提交最多3条带首屏与证据材料的候选，不足可报0条。用户同意研究并不等于批准出稿，更不是已发布。
