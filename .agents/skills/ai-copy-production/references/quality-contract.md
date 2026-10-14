# 出稿数据契约 · 文案门禁 v1

本 Skill 的门禁只是给“已写出且经过编辑申报的稿件”做保真、范围、可见事实边界检查；不替代人审，不核验互联网来源，不替用户定稿/制图/发布。运行环境可选，有可用工具时调用，否则由主编对同一清单逐条核查。

## 输入 JSON

```json
{
  "cases": [{
    "case_id": "demo-1",
    "edit_scope": "minimal",
    "platform": "xiaohongshu",
    "content_type": "tutorial",
    "audience": "有线上课程却一直没学完的人",
    "central_claim": "尝试把AI作为课程整理和复习助手",
    "headline_original": "原文标题",
    "headline_new": "原文标题",
    "original": "用户原文全文（不能补编）",
    "draft": "本次实际修订后的全文",
    "protected_phrases": ["用户要求完整保留的昵称", "用户原文中的真实动作", "用户原文中的幽默收尾"],
    "required_terms": ["用户明确要求写出的功能或关键术语"],
    "proof_plan": "哪些来源或本人操作可证明说法",
    "claims": [
      {"text": "用户真的做过的一次短视频分析", "evidence_status": "user_verified", "presented_as_tested": true},
      {"text": "尚未做完整验证的长课程学习", "evidence_status": "proposed", "presented_as_tested": false}
    ]
  }]
}
```

- edit_scope: `new_draft` / `review_only` / `title_only` / `opening_only` / `ending_only` / `minimal` / `substantive_rewrite`。review_only/title_only 不能修改正文；段落局部修改需要人工检查范围。
- evidence_status: `user_verified` 仅用户实际做过且提供足够明确的说明；`original_source`=已核原文；`third_party_claim`=外部作者声称；`proposed`=设想或准备测试；`unknown`=未知。
- 申报项目越真实越有用。**规则工具无法识别漏填了某项事实**。最终审核仍须人工对照项目总控、用户图片与文字、产品来源；本仓库不会保存私人稿件/用户敏感细节。
- `protected_phrases` 为编辑显式选择的代表性词句，不能当作只保护这些字、其他段落可以删。
- 实际修改超出用户授权，应先交代问题并请用户同意；事实错误优先修复。
- `requires_editorial_review` 不是 `pass` / `publishable`；不能把机器告警数量当真人感评分或成果预测。自动脚本只读取 JSON，输出 `copy-preflight-report.json`。
- 编辑无权将报告中的 `published=false` 改成 true；只有用户确认实际平台发布的作品 URL 或可靠回执才能更新运营台账。

## 必做回归任务

人工历史审稿特别检查四类问题：普通职场不能被程序员案例偷换；不使用AI的普通读者不能被评价；短图文必须提供超出空泛态度的内容；真实“安装夸克Skill并分析2分钟视频”不得被扩大成整套课程实测。豆包V4用户原文的昵称、可复制学习指令、操作过程与末尾玩笑必须保留，除非用户明确要求重写。

## 效果评价

合成单测只是**代码规则的通过率**，不是写作技术比较或平台转化验证。以后收集“已批准题目从零写”和“用户带初稿修稿”的实际样本，人工在不知分组的条件下看事实、意图保留、作者声音、具体增量以及每稿改动次数。原12案例36样稿是同模型同上下文的模拟压力测试，不能当独立A/B。之后只有用户审稿及真实发布表现可支持是否达到项目目标。

## 使用示例

```sh
python -m unittest discover -s .agents/skills/ai-copy-production/tests -v
python .agents/skills/ai-copy-production/scripts/copy_quality_gate.py --input dossier.json --output-dir output/copy
```
