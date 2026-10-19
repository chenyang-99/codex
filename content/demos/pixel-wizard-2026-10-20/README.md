# 像素魔法师｜同 Prompt 独立实现（2026-10-20）

> **状态**：实测通过 / X 推文待审 / **不是 Claude Opus 5.5 模型 A/B 比较**。

## 来源

- 原作者：[@zacxbt](https://x.com/zacxbt/status/2103808699466944604)
- [完整原始 Prompt](https://github.com/yihui-dev/awesome-opus5-5-videos/blob/main/prompts/zacxbt-944604.md)
- [Skillry 原作及第三方复刻对照](https://skillry.dev/ai-videos/opus-5-5/zacxbt-944604)
- 资源合集 [awesome-opus5-5-videos](https://github.com/yihui-dev/awesome-opus5-5-videos)

## 本次真实操作

1. 读取公开 Prompt，使用 **ChatGPT GPT-6** 编写了单文件原生 HTML/Canvas 2D 动画；**未调用 Opus 5.5**。
2. 本地 Chromium 运行和四种动作状态截图检查：**待机、蓄力、施法、恢复**。
3. Playwright 驱动渲染并由 FFmpeg 输出 1024×768、30fps、165 帧、5.5 秒 MP4（当前 MP4 在项目聊天交付包中，不在本 GitHub PR）。
4. 固定 128×96 逻辑分辨率、24 色固定调色板；测试时无浏览器脚本异常和外部请求。
5. 330 个固定时间步（5.5 秒）后对应截图一致，作为循环完整性的单点测试。

## 已知限制

- 原作对照页面标示 19 秒；这里仅为 **5.5 秒** 独立短循环，不能当成同等时长或严格逐帧复刻。
- 本实现只验证了主要技术要求；没有客观视觉相似度评分、跨设备持续 60fps 测试或 Opus 调用成本。
- **代码的固定 60Hz 更新机制**与**导出的 30fps MP4**是不同指标；不能把更新频率说成已测的播放帧率。
- 这里给出可运行 HTML 供读者自己检查。**未在 X 发布**，任何浏览量与互动数据未知。

## 使用方式

下载本目录的 `pixel_wizard.html` 并用现代浏览器直接打开。无需 npm、登录、外部资产或网络。页面会自动循环播放。

## 版权与署名

概念/任务源于 @zacxbt 的公开提示词，原帖及完整 Prompt 见上方；本目录 HTML 是后续独立创作的技术实现，未复制原作者的动画视频。
