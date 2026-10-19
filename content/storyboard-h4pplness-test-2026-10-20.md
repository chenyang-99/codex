# H4pplness Storyboard Skill — 独立测试记录（2026-10-20）

原项目：https://github.com/H4pplness/storyboard-skill
已核上游版本：6c1b8976764824907c73d85d125a59f76c536218
本仓库接入：.agents/skills/storyboard-poster/SKILL.md → vendor/storyboard-skill/storyboard-skill-en.md
测试状态：提示词输出通过结构校验；角色参考图已生成；故事板视觉输出失败；尚无完整视频。

## 1. 测试方法与来源边界

- 确认用户此前选择的是第48轮第17号 H4pplness/storyboard-skill；不是 toyme 的同名仓库。
- 读取原作者的 storyboard-skill-en.md（Claude/Codex 文本版）和 storyboard-chacracter-ref-chatgpt-en.md（ChatGPT 生图版）。
- 按文本版要求生成默认的两块内容：16:9 Storyboard Poster Prompt + 25s Video Prompt。角色参考图 Prompt 仅在需要时提供；本次同时用 ChatGPT 图像工具尝试了另一条原项目生图路线。
- 未执行用户本机或远程 Codex 运行时的原生 Skill 自动发现：本聊天可写入 GitHub，不能把文件写入 GitHub 当成远程会话已经加载。
- 原仓库未见明确 LICENSE，采用 Git submodule 固定作者提交，而非复制、再发布原始完整源码或样图；不使用作者寿司案例的图片当作本次原创结果。

## 2. 统一输入

原创无对白短片《雨滴与幼苗》，25秒，6镜头。废弃屋顶温室、雨晨、固定机器人和一株枯萎幼苗。机器人发现破天窗滴落的雨水，用同一把钴蓝色浇水壶收集雨水，浇灌白色花盆，最后幼苗展开一片新叶。色彩：乳白、蓝灰、钴蓝、琥珀、少量嫩绿。

## 3. Storyboard Poster Prompt（文本版原定输出）

Create a crisp infographic storyboard poster.
Layout: wide 16:9, white background, thin black borders, bold black typography. One poster with a 3-column x 2-row six-panel grid.
Render style: original cinematic stylized 3D animation with gently weathered ceramic and metal surfaces. No franchise likeness or logos.

HEADER:
• RAIN AND SEEDLING
• TOTAL VIDEO TIME: 25 SECONDS
• 6 SHOTS · GENTLE · HOPEFUL · CINEMATIC
• Legend: ACTION · EMOTION · LOCATION · MOMENT

COMMON BRIEF:
• Character: a short off-white round-headed utility robot; one horizontal amber visor, orange worn mark on LEFT shoulder, yellow tie on LEFT wrist; small COBALT-BLUE watering can always operated with RIGHT hand.
• Setting: one abandoned rooftop glass greenhouse, broken skylight, rainy blue-gray dawn, one white ceramic pot with a wilted seedling on the workbench.
• Color palette: ivory, blue gray, cobalt blue, amber, muted orange, leaf green.
• Tone: lonely · attentive · hopeful.
• Arc: the robot notices a dying seedling → discovers a falling raindrop → catches rainwater → waters it → one fresh green leaf unfolds.
• Character consistency: every appearance has the same visor, shoulder mark, wrist tie, body proportions and watering can. Do not add people or second plants.

PANELS:
Shot 1 — Arrival: The robot enters the greenhouse from frame left holding the blue can in its RIGHT hand; distant wilted white pot on right bench; spacious, lonely opening. [SIDE]
Shot 2 — Wilted leaf: Robot examines drooping leaves and dry soil, LEFT hand touching a leaf, RIGHT hand retains blue can; worried pause. [CLOSE]
Shot 3 — Rain discovered: Robot tilts amber visor toward drops falling from a broken skylight; raises the blue can in its RIGHT hand; moment of hope. [LOW]
Shot 4 — Catching water: Clear rain drops fall into the SAME cobalt-blue can while the robot's RIGHT hand holds the handle; small precise turning point. [CLOSE]
Shot 5 — Watering ★: Robot carefully tips the SAME can from its RIGHT hand into the SAME white pot; transparent stream on dry soil; strongest visual beat. [SIDE]
Shot 6 — First leaf: One fresh green leaf unfolds from the previously wilted seedling; robot lowers the can in its RIGHT hand and looks on quietly. [CLOSE]

FOOTER:
• VIDEO FLOW: 6 shots (4+4+4+4+5+4 seconds) = 25 seconds; from concern to hope.
• CAMERA TIPS: side for geography and watering, low for discovery, close for emotional details.
• LIGHT & STYLE: blue-gray rainy dawn, warm light consistently enters from frame left; original 3D animated film stills.
• DIRECTOR NOTES: one robot, one can, one pot, one sunrise; no invented change of location, hand, or character identity.

## 4. Video Prompt（文本版原定输出）

VIDEO PROMPT — RAIN AND SEEDLING

CHARACTER NOTE: A short off-white round-headed utility robot with a single horizontal amber visor, orange wear mark on LEFT shoulder, yellow cloth tie at LEFT wrist, small COBALT-BLUE watering can held with RIGHT hand.

STYLE & SETTING:
Original cinematic stylized 3D animation inside one abandoned rooftop greenhouse with broken skylight. Blue-gray rainy dawn, warm sidelight from frame left, wet glass, restrained textures, one white ceramic pot with a wilted seedling.

SCENES:
Scene 1 — Arrival (~4s):
Camera: eye-level side wide shot, slow push-in.
Character: cautious, notices the dying plant.
Action: Robot enters frame from the left and stops near the workbench, holding the blue can in its right hand.

Scene 2 — Wilted leaf (~4s):
Camera: close-up side angle, slow tilt toward the pot.
Character: concerned, leaning forward.
Action: Robot brushes a drooping leaf with its left fingers while keeping the watering can in its right hand.

Scene 3 — Rain discovered (~4s):
Camera: low angle medium shot, slow tilt upward.
Character: attentive, expression shifts to hope.
Action: Robot follows a raindrop to the broken skylight and raises its can under the falling water.

Scene 4 — Catching water (~4s):
Camera: tight insert close-up, static.
Character: robot's right hand remains visible on the handle.
Action: Drops strike the inside of the same cobalt-blue watering can.

Scene 5 — Watering (~5s):
Camera: side medium shot, slow push-in.
Character: gentle and concentrated.
Action: Robot tilts the can with its right hand and pours collected rainwater onto the seedling's dry soil.

Scene 6 — First leaf (~4s):
Camera: close-up eye-level, slow pull-back.
Character: calm, relieved.
Action: One fresh green leaf unfolds; robot lowers the can and watches it quietly.

## 5. 结构验收

| 测项 | 实际结果 |
|---|---|
| 正确源仓库与提交 | 已核查，固定到 H4pplness 提交 6c1b897 |
| GitHub 代码接入 | Git submodule、.gitmodules、入口符号链接、安装校验脚本已写入测试分支并经 API 回读 |
| Codex 原生自动识别 | 未验证（无可用的原生运行环境） |
| 分镜海报 Prompt | 通过：6镜、16:9、角色环境、镜号/机位、高潮★、页眉与页脚 |
| 视频 Prompt | 通过：6场、每场 Camera 与 Action，且 4+4+4+4+5+4 = 25s |
| 角色参考图 | 在本聊天图像工具中生成了 1 张原创角色设定图 |
| 6格分镜实际图片 | 不通过：两次后续生图均偏离既定机器人/温室主题，出现无关主题及未经核实的安装代码，因此不可作为该Skill成功案例 |
| 完整视频 | 未调用视频生成模型，也未生成完整视频 |
| 版权与授权 | 作者公开仓库未见 LICENSE；本仓库用子模块引用，未再发布作者原图 |

## 6. 可复现的失败边界

- 文字提示词结构完整，不等于后续图像模型会按指定的镜号、主体与角色出图。本次图像侧并未达标。
- 图片生成偏离在当前对话/工具组合下发生；不能据此证明原作者在其推荐环境下不可用。
- 不得凭此宣传“一键做视频”“人物保证一致”或“节省xx%时间”。
- 如果想发表视觉成功案例，应先用严格参照同一角色设定图的6格故事板再次出图、验收，再交给视频模型做真正视频。这个条件当前未满足。


## 7. 后续直接执行原始 Skill 图片工作流（第二次实测）

本项发生在以上首次失败之后，按 H4pplness 原始 `storyboard-chacracter-ref-chatgpt-en.md` 的“生成分镜海报图像”阶段重新调用 ChatGPT 内生图工具，采用同一个原创 25 秒/6 镜机器人题材。

- **图片版本 V1：** `storyboard-skill-rain-seedling-v1.png`，1536 × 1024，明确展示“发现→观察→发现雨滴→接水→浇灌→新叶”的 6 格真实分镜、镜头编号、时长分别 4/4/4/4/5/4 秒（合计 25 秒）；有蓝色水壶和较一致的机器人主体。但缺失设定的白色花盆，角色左肩划痕、左腕布带的跨镜可见度不足，局部晨光/雨景不一致。**生成成功，严格连续性不通过。**
- **图片版本 V2：** `storyboard-skill-rain-seedling-v2.png`，1536 × 1024，再次呈现完整 6 格机器人温室分镜，并带双语镜头说明与视觉元素缩略图。仍缺失白色陶盆，且行动节拍发生变化（第 4 镜浇水、第 5 镜植物生长，而原始脚本第 5 镜浇水、第 6 镜见证新叶）；左腕黄色布带未稳定出现。**生成成功，严格脚本一致性不通过。**
- 两个 PNG 为本次聊天实际生成文件，聊天附件与本报告同时提供；二进制文件并未上传至 GitHub 仓库，不能声称 GitHub 已保存这两张图。
- 这是 **从官方 Skill 原始文本触发生成**，不等于 GitHub PR #6 已合并，也不等于独立 Codex CLI/Claude Code 运行时已经自动发现并调用仓库技能。本环境无可用的原生 Codex/Claude CLI。
- 没有使用视频合成模型；25 秒仅为分镜时长与视频 Prompt 规格，并非已生成 25 秒视频。

**本次最终验收：** 已真实使用技能说明生成两张对应六镜头的故事板图，文本结构通过；视觉连续性存在明确缺陷，不能宣称无偏差的“角色一致”或“一键成片”。如发布推文，应展示实际图像并说明局限。

**额外尺寸检查：** 两张实际海报均为 1536×1024，长宽比 3:2，并非 Skill 目标 16:9。此前报告中的 16:9 仅指文本 Prompt 规格，不能声称最终图片比例达标。完整图像验收为「主题与6格结构通过；比例、白色花盆与部分连续性不通过」。
