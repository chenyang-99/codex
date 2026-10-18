# AI选题审核输入模式（JSON，v1.1，2026-10-19）

## 人工研究档案示例（**虚构字段示范**，不代表真实已验证选题）

```json
{
  "rejected": ["previously-rejected-topic"],
  "known_problem_keys": ["historical-topic-key"],
  "topics": [{
    "topic_id": "topic-01",
    "problem_key": "ai-real-work-time",
    "title": "AI生成看似更快，核查和返工时间怎么算？",
    "audience": "用AI处理文档的普通职场人",
    "trigger": "生成完成后依旧要核验",
    "job": "判断一项任务是否真的节省工时",
    "outcome": "可复核的全流程工时记录表",
    "value_type": "决策",
    "angle": "加上提示、核查、返工三段",
    "promise": "完整工时核算思路与表格模板",
    "proof_plan": "实际做两次同类任务并保留计时记录",
    "competitor_gap": "竞品通常只比较生成耗时（待实际搜索验证）",
    "difference_rationale": "明确计入人为审核成本",
    "source_limitations": "公开讨论不代表所有职场用户",
    "requires_test": true,
    "test_gap": "本账号尚无对照工时实测",
    "four_values": {
      "attraction": "首屏展示生成速度与最终交付速度的反差；数据须实际测量",
      "save_asset": "可复制的三阶段任务工时记录模板",
      "learning_outcome": "学会计算人工、AI与核查返工的完整耗时，识别成本隐藏项",
      "spread_mechanism": "反常识的实际耗时对比与评论区复核需求；尚非已验证热度",
      "spread_class": "fresh_potential",
      "spread_source_url": "https://example.org/original-source",
      "original_published_at": "2026-10-19",
      "freshness_reason": "近期新示例，尚待从实际源文核验发布时间和增量"
    },
    "four_value_scores": {
      "attraction": 22,
      "save": 28,
      "learning": 23,
      "spread": 15
    },
    "signals": [
      {"kind": "user_post", "url": "https://example.org/post/1", "quote": "准确引用的用户原话", "read_scope": "actually_read_public_post"},
      {"kind": "official_release", "url": "https://example.org/official", "claim": "官方原始事实摘要", "read_scope": "actually_read_official"}
    ]
  }]
}
```

示例中 `example.org` 链接和评分均为演示，**不可作为真实选题直接入库或传播证据**。

## 四价值必填规则
- `four_values.attraction`: 为什么第一屏/前三秒值得停留；要具体而真实。
- `four_values.save_asset`: 读者能够实际保存的Prompt、模板、工具及适用限制、完整操作步骤或判断框架。泛泛说“干货”不合格。
- `four_values.learning_outcome`: 读者具体学会什么或能够做什么；不可只是“看看好看的图”。
- `four_values.spread_mechanism`: 可解释的传播机制，或真实热度证据的范围。
- `four_values.spread_class`: `verified_viral`（A类）或 `fresh_potential`（B类）；无可靠依据则 `unverified`，不可进入正式推荐。
- `four_values.spread_source_url`: 对应原作/原教程/同一社交帖的可回查来源。
- A类还需 `spread_metric`（明确平台、数值和指标）及 `spread_checked_at`（检查时间）；不得伪造，第三方统计要明示。
- B类还需 `original_published_at` 和 `freshness_reason`；老教程可作为有价值的学习资料，但不可假称本周新发布。
- `four_value_scores` 必须为**人工显式提供**的四个数：`attraction` 0–25、`save` 0–30、`learning` 0–25、`spread` 0–20。缺失或不完整者只作探索研究，不得进入正式编辑推荐。
- 正式推荐需要总分≥85，且四项分别≥20/24/20/14；评分只是内部编辑规则，不是被证实的流量预测。
- 不论评分多高，真实来源、版权合规、完整教程/方法可信度、用户历史否决和跨天去重均为独立门槛。
- AICG视觉精品还必须实际看见原作画面并通过另一个视觉维度硬门槛：视觉≥40/45、综合≥85/100；**四价值分和视觉分不可混算**。

## 原有研究字段及兼容性
- `signals[].kind` 仅支持 `user_post`、`user_comment`、`official_release`（需 `claim`）、`original_case`（需 `observed_result`）。
- `read_scope` 必须记录实际读到什么；`search_snippet_only`、`headline_only`、`unknown`、`unavailable` 不是一手验证。
- 一篇原帖下多条评论只能算一个语境，未知作者不可虚构人数。
- 旧 `ratings` 六维需求/价值/时效/差异化/受众/可行性仍可选，用于**研究排名辅助**，不替代四价值硬门槛。
- `blocked` / `exploratory_only` / `editorial_candidate` 均不是发布授权；所有自动采集永远不能自动批准成稿与发布。
