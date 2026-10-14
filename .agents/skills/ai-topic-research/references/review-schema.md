# 选题审核输入模式（JSON）

```json
{
  "rejected": ["ai-summary-omissions"],
  "known_problem_keys": ["historical-topic-key"],
  "topics": [
    {
      "topic_id": "topic-01",
      "problem_key": "ai-real-work-time",
      "title": "把核对和返工算进去，AI工作省时间吗？",
      "audience": "办公室经常使用AI的人",
      "trigger": "工作投入AI后仍需审核",
      "job": "判断是否真的提效",
      "outcome": "一份可以复核的全流程工时计算",
      "value_type": "决策",
      "angle": "计入提示、核查和返工",
      "promise": "有证据的工时核算方法",
      "proof_plan": "记录同类任务人工与AI的全流程耗时",
      "competitor_gap": "同题已核查的内容多只比生成速度",
      "difference_rationale": "填补核对/返工成本",
      "source_limitations": "目前来自两个不同海外用户个案，不代表国内多数人",
      "requires_test": true,
      "test_gap": "尚无本号完整实际工时记录",
      "signals": [
        {"kind": "user_post", "url": "https://www.reddit.com/r/ChatGPT/comments/1x3rher/using_ai_at_work_is_like/", "quote": "用户反映AI操作增加管理工作量的准确摘录", "read_scope": "actually_read_public_post"},
        {"kind": "user_post", "url": "https://www.reddit.com/r/ChatGPT/comments/1wifev5/can_someone_explain_how_ai_actually_helps_them/", "quote": "用户质疑AI如何帮助办公的准确摘录", "read_scope": "actually_read_public_post"}
      ]
    }
  ]
}
```

必需真实原始来源。 `kind` 仅限 `user_post`、`user_comment`、`official_release`（需要 `claim`）、`original_case`（需要 `observed_result`）；`read_scope` 记录实际读到什么，`search_snippet_only`、`headline_only`、`unavailable`、`unknown` 不被视为可核验一手信号。作者未知同帖多评论只算一个语境。 `ratings` 可选，六个字段 demand/value/evidence/differentiation/audience_fit/feasibility 各为0–5分，只有人工显式给出才计算，不擅自推断。状态 blocked/ exploratory_only/ editorial_candidate 都不是发布批准。
