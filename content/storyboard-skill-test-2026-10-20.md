# Storyboard Skill｜原创六镜头工作流测试

日期：2026-10-20
源项目：https://github.com/toyme/storyboard-skill （MIT；公开基线 v0.1.0）
安装候选：chenyang-99/codex/.agents/skills/storyboard-skill

**测试范围：按上游 SKILL.md 和 references/prompt-patterns.md 手动执行文本技能流程，完成分镜、提示词、连续性复核和局部修正。未验证 Codex 运行时自动发现，也未实际调用图片/视频模型。**

## 输入

原创故事《雨滴与幼苗》：25秒，无对白，9:16。黎明雨天，一台机器人在废弃温室发现枯苗，利用破天窗滴落雨水给它浇水，最终幼苗长出一片嫩绿新叶。要求6镜、每镜独立提示词、统一道具和光线。

## 角色 / 视觉 Bible

- Character: robot_m1_v1，乳白圆头维修机器人，水平琥珀眼带，左肩橙色划痕，左腕黄色布带。
- Prop: watering_can_01，一把钴蓝色小浇水壶，始终右手操作；唯一花盆是白色陶盆。
- Location: greenhouse_01，楼顶破损玻璃温室；蓝灰雨晨，左侧暖色天光。
- Style: stylized 3D animated-film still, 9:16, restrained texture, no text/logos.
- Continuity: 第1—5镜枯苗，只有第6镜长出一片新叶；角色、衣饰、手持道具、地点不变。

## 输出：6镜完整结构化提示词

### scene_01_shot_001

[SHOT ID] scene_01_shot_001

[PURPOSE] 建立世界和目标

[CHARACTER] robot_m1_v1：乳白色圆头机器人、琥珀眼带、左肩橙色划痕、左腕黄色布带、右手钴蓝水壶

[CAMERA] 28mm wide establishing, eye level

[LIGHTING] 蓝灰雨晨；暖侧光固定画面左侧

[EMOTION] 孤独、关切

[COMPOSITION] 机器人从左边进入温室；白盆枯苗在远处右侧工作台

[ENVIRONMENT] 同一处废弃屋顶玻璃温室、破损天窗、工作台、唯一白盆枯苗

[CONTINUITY] 第1/6镜；机器人外观、右手蓝壶、左腕布带、白盆和地点始终一致；植物直到第6镜才出现嫩绿新叶

[NEGATIVE CONSTRAINTS] 不换装、不得更换水壶颜色/左右手、不得增加其他人物/盆栽、文字或商标

[IMAGE PROMPT] Original stylized 3D animation film still, vertical 9:16, blue-gray rainy dawn, gentle warm sidelight from camera-left. A fictional off-white utility robot: spherical head, single horizontal amber-eye visor, orange scratch on LEFT shoulder, yellow cloth tie on LEFT wrist. Same abandoned rooftop greenhouse, broken skylight, same white ceramic pot with a wilted seedling, same small COBALT-BLUE watering can held with robot's RIGHT hand. No extra people, no lettering, no brand marks. Frame-specific direction: robot enters from frame left with the blue watering can low in the right hand; the wilted seedling in a white pot sits far right on the table; broken skylight overhead. Camera: 28mm wide establishing, eye level. Keep the seedling wilted until final frame six.

---

### scene_01_shot_002

[SHOT ID] scene_01_shot_002

[PURPOSE] 说明枯苗需要水

[CHARACTER] robot_m1_v1：乳白色圆头机器人、琥珀眼带、左肩橙色划痕、左腕黄色布带、右手钴蓝水壶

[CAMERA] 50mm close-up, plant foreground, robot behind

[LIGHTING] 蓝灰雨晨；暖侧光固定画面左侧

[EMOTION] 忧虑

[COMPOSITION] 左手轻触枯叶，右手握蓝壶；植物仍枯萎

[ENVIRONMENT] 同一处废弃屋顶玻璃温室、破损天窗、工作台、唯一白盆枯苗

[CONTINUITY] 第2/6镜；机器人外观、右手蓝壶、左腕布带、白盆和地点始终一致；植物直到第6镜才出现嫩绿新叶

[NEGATIVE CONSTRAINTS] 不换装、不得更换水壶颜色/左右手、不得增加其他人物/盆栽、文字或商标

[IMAGE PROMPT] Original stylized 3D animation film still, vertical 9:16, blue-gray rainy dawn, gentle warm sidelight from camera-left. A fictional off-white utility robot: spherical head, single horizontal amber-eye visor, orange scratch on LEFT shoulder, yellow cloth tie on LEFT wrist. Same abandoned rooftop greenhouse, broken skylight, same white ceramic pot with a wilted seedling, same small COBALT-BLUE watering can held with robot's RIGHT hand. No extra people, no lettering, no brand marks. Frame-specific direction: the wilted leaf and dry soil in the same white pot fill the foreground; robot gently touches a leaf with LEFT hand while RIGHT hand holds the cobalt-blue can. Camera: 50mm close-up, plant foreground, robot behind. Keep the seedling wilted until final frame six.

---

### scene_01_shot_003

[SHOT ID] scene_01_shot_003

[PURPOSE] 发现天窗雨滴作为水源

[CHARACTER] robot_m1_v1：乳白色圆头机器人、琥珀眼带、左肩橙色划痕、左腕黄色布带、右手钴蓝水壶

[CAMERA] 35mm medium shot, slight low angle

[LIGHTING] 蓝灰雨晨；暖侧光固定画面左侧

[EMOTION] 希望

[COMPOSITION] 抬头看从破窗滴下的雨；举起右手蓝壶

[ENVIRONMENT] 同一处废弃屋顶玻璃温室、破损天窗、工作台、唯一白盆枯苗

[CONTINUITY] 第3/6镜；机器人外观、右手蓝壶、左腕布带、白盆和地点始终一致；植物直到第6镜才出现嫩绿新叶

[NEGATIVE CONSTRAINTS] 不换装、不得更换水壶颜色/左右手、不得增加其他人物/盆栽、文字或商标

[IMAGE PROMPT] Original stylized 3D animation film still, vertical 9:16, blue-gray rainy dawn, gentle warm sidelight from camera-left. A fictional off-white utility robot: spherical head, single horizontal amber-eye visor, orange scratch on LEFT shoulder, yellow cloth tie on LEFT wrist. Same abandoned rooftop greenhouse, broken skylight, same white ceramic pot with a wilted seedling, same small COBALT-BLUE watering can held with robot's RIGHT hand. No extra people, no lettering, no brand marks. Frame-specific direction: the robot looks up at a thin stream dripping from the broken skylight and raises the same cobalt-blue watering can in its RIGHT hand beneath the drops. Camera: 35mm medium shot, slight low angle. Keep the seedling wilted until final frame six.

---

### scene_01_shot_004

[SHOT ID] scene_01_shot_004

[PURPOSE] 展现接水动作的因果

[CHARACTER] robot_m1_v1：乳白色圆头机器人、琥珀眼带、左肩橙色划痕、左腕黄色布带、右手钴蓝水壶

[CAMERA] 85mm insert close-up

[LIGHTING] 蓝灰雨晨；暖侧光固定画面左侧

[EMOTION] 安静、专注

[COMPOSITION] 雨滴准确落入同一把钴蓝水壶，右手扶壶柄

[ENVIRONMENT] 同一处废弃屋顶玻璃温室、破损天窗、工作台、唯一白盆枯苗

[CONTINUITY] 第4/6镜；机器人外观、右手蓝壶、左腕布带、白盆和地点始终一致；植物直到第6镜才出现嫩绿新叶

[NEGATIVE CONSTRAINTS] 不换装、不得更换水壶颜色/左右手、不得增加其他人物/盆栽、文字或商标

[IMAGE PROMPT] Original stylized 3D animation film still, vertical 9:16, blue-gray rainy dawn, gentle warm sidelight from camera-left. A fictional off-white utility robot: spherical head, single horizontal amber-eye visor, orange scratch on LEFT shoulder, yellow cloth tie on LEFT wrist. Same abandoned rooftop greenhouse, broken skylight, same white ceramic pot with a wilted seedling, same small COBALT-BLUE watering can held with robot's RIGHT hand. No extra people, no lettering, no brand marks. Frame-specific direction: clear raindrops fall into the open top of the same cobalt-blue can, robot's RIGHT hand gripping its handle, skylight softly blurred behind. Camera: 85mm insert close-up. Keep the seedling wilted until final frame six.

---

### scene_01_shot_005

[SHOT ID] scene_01_shot_005

[PURPOSE] 用接到的雨水浇枯苗

[CHARACTER] robot_m1_v1：乳白色圆头机器人、琥珀眼带、左肩橙色划痕、左腕黄色布带、右手钴蓝水壶

[CAMERA] 50mm medium side view

[LIGHTING] 蓝灰雨晨；暖侧光固定画面左侧

[EMOTION] 温柔、耐心

[COMPOSITION] 右手倾壶，水流入白盆；枯苗此时尚未复苏

[ENVIRONMENT] 同一处废弃屋顶玻璃温室、破损天窗、工作台、唯一白盆枯苗

[CONTINUITY] 第5/6镜；机器人外观、右手蓝壶、左腕布带、白盆和地点始终一致；植物直到第6镜才出现嫩绿新叶

[NEGATIVE CONSTRAINTS] 不换装、不得更换水壶颜色/左右手、不得增加其他人物/盆栽、文字或商标

[IMAGE PROMPT] Original stylized 3D animation film still, vertical 9:16, blue-gray rainy dawn, gentle warm sidelight from camera-left. A fictional off-white utility robot: spherical head, single horizontal amber-eye visor, orange scratch on LEFT shoulder, yellow cloth tie on LEFT wrist. Same abandoned rooftop greenhouse, broken skylight, same white ceramic pot with a wilted seedling, same small COBALT-BLUE watering can held with robot's RIGHT hand. No extra people, no lettering, no brand marks. Frame-specific direction: robot tilts the same cobalt-blue can with its RIGHT hand and pours a modest stream onto dry soil in the same white pot; leaves remain wilted. Camera: 50mm medium side view. Keep the seedling wilted until final frame six.

---

### scene_01_shot_006

[SHOT ID] scene_01_shot_006

[PURPOSE] 交代结局和视觉回报

[CHARACTER] robot_m1_v1：乳白色圆头机器人、琥珀眼带、左肩橙色划痕、左腕黄色布带、右手钴蓝水壶

[CAMERA] 50mm medium close-up, static

[LIGHTING] 蓝灰雨晨；暖侧光固定画面左侧

[EMOTION] 欣慰

[COMPOSITION] 幼苗长出仅一片嫩绿新叶；右手蓝壶放低

[ENVIRONMENT] 同一处废弃屋顶玻璃温室、破损天窗、工作台、唯一白盆枯苗

[CONTINUITY] 第6/6镜；机器人外观、右手蓝壶、左腕布带、白盆和地点始终一致；植物直到第6镜才出现嫩绿新叶

[NEGATIVE CONSTRAINTS] 不换装、不得更换水壶颜色/左右手、不得增加其他人物/盆栽、文字或商标

[IMAGE PROMPT] Original stylized 3D animation film still, vertical 9:16, blue-gray rainy dawn, gentle warm sidelight from camera-left. A fictional off-white utility robot: spherical head, single horizontal amber-eye visor, orange scratch on LEFT shoulder, yellow cloth tie on LEFT wrist. Same abandoned rooftop greenhouse, broken skylight, same white ceramic pot with a wilted seedling, same small COBALT-BLUE watering can held with robot's RIGHT hand. No extra people, no lettering, no brand marks. Frame-specific direction: a single small fresh green leaf unfolds from the recognizable seedling in the same white pot; robot watches from the right, holding the same cobalt-blue can lowered in its RIGHT hand. Camera: 50mm medium close-up, static. Keep the seedling wilted until final frame six.


## 连续性文字审查

| Shot | 状态 | 依据 |
|---|---|---|
| scene_01_shot_001 | PASS: 文本设定一致 | 未见道具颜色、角色、场景前后自相矛盾 |
| scene_01_shot_002 | PASS: 文本设定一致 | 未见道具颜色、角色、场景前后自相矛盾 |
| scene_01_shot_003 | PASS: 文本设定一致 | 未见道具颜色、角色、场景前后自相矛盾 |
| scene_01_shot_004 | PASS: 文本设定一致 | 未见道具颜色、角色、场景前后自相矛盾 |
| scene_01_shot_005 | PASS: 文本设定一致 | 未见道具颜色、角色、场景前后自相矛盾 |
| scene_01_shot_006 | PASS: 文本设定一致 | 未见道具颜色、角色、场景前后自相矛盾 |

人为注入负向测试：将第4镜里的 **COBALT-BLUE watering can** 改写成 **RED watering can**，与角色/道具 Bible 冲突；审核应标记 REVISE。上面已修回蓝色；这不是图片实际生成缺陷。

### 定向修正提示词

Preserve: robot's RIGHT-hand grip, can shape, raindrops, 85mm insert, original lighting, composition, greenhouse setting and stylized 3D style.

Change only: recolor the mistakenly red watering can to the established cobalt blue.

Do not change: hand anatomy, robot visor, wardrobe, background, camera, framing, aspect ratio or rain.

Output: the same frame with exactly one cobalt-blue watering can and no other changes.

### 安全复核

原创虚构机器人，没有真实人物肖像、未成年人、裸露、暴力血腥、商标、敏感资料或可识别版权角色；提示词文字层面低风险，真实画面仍须另审。

## 验收结果和限制

- 共6个唯一镜号，6份可独立用于生图的提示词；每镜具备11个标准字段。
- 产生1份角色/风格简版 Bible、1次6镜连续性审查、1次人为注入的道具错误检查和1条局部修正 Prompt。
- 能确认：使用 Skill 的文本格式可以将角色、色彩、场景和改图约束显式记录。
- 不能确认：Codex 原生自动加载成功、图像模型实际人物一致性、视频连续性提升、生成速度/成本/平台数据。不能对外宣称“一键出视频”。

下一步严格视觉对照实验：同一模型/预算分别使用自由文本和此6镜 Prompt 出图，再盲评同一人物、道具和光照；目前未做。
