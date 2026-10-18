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
