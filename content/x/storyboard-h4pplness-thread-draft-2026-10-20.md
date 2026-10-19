# X 串推草稿 V2｜Storyboard Skill 已真实生图

日期：2026-10-20，待用户审核，未发布。

**发布素材：** 本次聊天实际生成的 `storyboard-skill-rain-seedling-v1.png` 和 `storyboard-skill-rain-seedling-v2.png`；建议首条配 V1 六格分镜海报。两张图片保存在会话附件中，尚未上传 GitHub。任何推文“使用Skill”仅指遵循上游技能文档执行，不宣称Codex CLI自动加载。

## 1/3

我用开源 Storyboard Skill，把一段25秒的机器人短片做成了6格分镜海报。实际生成了两版图，却发现一个很典型的问题：脚本明明指定“白色花盆”，画面还是把植物种进了地里。

完整实测和结果在下面。🧵

---

## 2/3

我用的是 H4pplness 的原始 Storyboard Skill：先整理镜头海报Prompt和分场视频Prompt，再按它的 ChatGPT 生图流程生成故事板。两版图都出现了6个镜头，时长相加是25秒，机器人和蓝色水壶也基本连贯。但第二版还改变了原定的动作顺序。

---

## 3/3

所以结论不是“一键生成视频”，而是：Skill能让分镜规划更清楚，图像模型仍可能漏道具、改动作。现在已经有两张真实分镜图，但还没生成视频，也没有验证Codex原生自动加载。

项目：https://github.com/H4pplness/storyboard-skill
完整测试：https://github.com/chenyang-99/codex/blob/feature/h4pplness-storyboard-poster-20261020/content/storyboard-h4pplness-test-2026-10-20.md

## 发布前事实门禁

- 两次生成都得到同题材六格海报；白色盆栽缺失，严格连续性不通过。
- 尚未生成完整短视频，GitHub PR #6 待合并，Codex 运行时自动调用未验证。
- 图片属于AI生成，按发布平台要求标识；手动审稿后才能发布，不把草稿记录为已发布。
