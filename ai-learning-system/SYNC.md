# 项目长期同步规程

## 当前实际架构
ChatGPT 项目「自由学习」 = 教学对话与可复用项目说明。
GitHub = 课程版本管理 + 可验证学习进度状态（未来应位于独立私有仓库）。
当前公开存储：`chenyang-99/codex/ai-learning-system/`，只存储通用课程基础设施、模板和匿名初始化状态。
**目前未部署自动双向同步器**；只有每次对话实际发出 GitHub 读写操作才会更新。ChatGPT 项目记忆不能替代状态文件。

## 公开到私有的迁移
1. 在 GitHub 建立新 PRIVATE 仓库，例如 `chenyang-99/ai-mastery-learning`。当前 GitHub 连接器没有“创建仓库”接口，需通过 GitHub UI 进行这一动作。
2. 确保 GitHub 应用对新仓库授权读写。
3. 复制本目录的课程文件与空白进度；把 PROGRESS.json 的 `privacy` 更新为 `PRIVATE`，`authoritative_private_progress_repo` 填新仓库全名。
4. 在 ChatGPT 项目指令里把权威读取路径更新为私有仓库。读取验证后，再开始保存个人学习结果。
5. 作品大文件可留在授权网盘，GitHub 只存受控链接、校验摘要和评审结果；避免将原始大视频直接推 Git 历史。

## 会话启动
- 读取 README、TEACHING-CONTRACT、PROGRESS、CURRICULUM 与当前课时。
- 检查字段 current_week/current_lesson/lesson_status、pending_review、last_verified_checkpoint；冲突时不要猜测。
- 如果私有仓库尚未设置，只能进行不含个人进度提交的试讲与资料准备。

## 结束一课
- 收集本课目标、来源审计、实物链接/文件、验证证据、评分及遗留问题。
- 只在用户确认个人隐私存储位置且已获得适当权限后写入私有库。
- 使用 fetch_file 获取进度最新 SHA；基于该版本更新文件。
- 再次 fetch_file 读回核对新 SHA/内容；失败时报告未同步，不得误报完成。
- 成功后总结下一节、复习计划、待办。记录日志包含日期与课程版本。

## 变化管理
- 遇到课程网站失效、模型功能更新，记录检查日期和状态。
- 若课表要改，先判断能力目标是否改变；版本更新与 CHANGELOG 同步。
- 不删除原始考核与进度的历史记录；通过 Git 提交保留追溯。

## 状态字段（建议扩展后只存在私有库）
`completed_lessons`, `completed_projects`, `current_lesson`, `lesson_status`, `pending_review`, `last_assessment`, `last_verified_checkpoint`，以及个人能力矩阵、证据索引和学习反馈。
