# X 运营指标字典、实验与复盘

## 0. 假设与限制
- 公共 X 主页可以获取不等于当前工具能访问；私有 X Creator Studio 无连接时不可读取，必须依赖用户自愿提供截图/导出数据。
- 不同数据来源有不同定义、更新延迟。用户自报/第三方快照/官方后台不混做时间序列，不用0表示缺失；标“unknown”。
- 稳定口径先于计算，先量一条作品发布后 24 小时及 7 天；不同窗口不得直接比较“谁更好”。
- 这是内容与增长诊断，不是破解 X 算法或用户级 A/B 实验。

## 1. 最小数据契约（与现有 Sheets 共存）
【作品表】post_url、posted_at_timezone、status（仅用户确认可标已发布）、content_pillar、post_format、primary_reader_payoff、original_contribution、source_type、study_window（24h/7d/更长）、snapshot_at、organic_or_paid（有证据才标）、public_views、dashboard_impressions（若可得）、likes、reposts、bookmarks、replies、profile_visits、follows（可得）、reader_questions、time_cost_minutes（若用户给出）、data_source、confidence_note。
【账号日/周快照】snapshot_at、date_range、rolling_90d_verified_home_impressions（用户 Creator Studio 对应具体名称）、verified_followers、total_followers、premium_tier、profile_visits、net_follower_gain、user_reported_workload、source及相应截图/导出证据。
注意：Creator Studio 门槛项与内容奖励“qualified impressions”官方措辞可能并非完全同一指标；不在字段未确认时硬合并。90 天滚动净变化 = 新进入区间的合格曝光 - 90天以前滚出的旧曝光（也可有平台重新调整），不能精确归因到本周某条帖子。
【实验表】hypothesis、audience、format/subject_changed、comparison_group、precommitted_primary_metric、baseline_window、test_window、sample_count、confounders、result、decision、reason、next_check、approved_by_user。
优先复用项目现有内容数据和“决策与交接”；确实缺时间序列时在用户批准后增设单独“X账号快照”标签页，不清理或覆盖原表。不上传私密截图到公开 GitHub。

## 2. 四层指标
1) 北极星：官方后台近90天可计入申请的 verified Home Timeline impressions（准确字段待确认）。
2) 资格门槛：500 verified followers + 支持的付费会员层级/年龄/地区/账号状况（均需验证）。
3) 内容及受众：同窗口普通曝光、每千次普通浏览的收藏和转发、资料链接点击/主页访问/净增关注（有则用），评论中的真实问题与重复需求。
4) 可持续性：每周实际“审定与发布原创”作品数、平均单篇耗时、未审核稿件积压、违规则数。总普通曝光是诊断，不可独立代表合格曝光。
未见用户数据不允许编造曝光/粉丝或估算有效曝光转化率。

## 3. 派生指标（仅辅助）
- bookmark_per_1k_public_views = bookmarks / public_views * 1000；
- repost_per_1k_public_views = reposts / public_views * 1000；
- likes_per_1k_public_views = likes / public_views * 1000；
- profile_visit_rate = profile_visits / dashboard_impressions（仅后台同窗口且两个字段同口径；否则不用）。
浏览数小于100的样本、仅发布不足24h、来自非等长窗口、爆款由外部大号引用的标“低稳定性/不可直接比较”；分母0或未知则指标未知。请保留分子、分母、采集时间和来源。
不要把高每千次收藏=导致算法推荐；被吸引的受众和流量来源本身可同时影响指标。

## 4. 评估方法
- 探索诊断：以最近至少6–12条同窗口原创帖作为初步参考；不足时仅做逐帖定性分析，不假装稳定中位数或“行业标准”。6–12只是运营启动工作量，不是统计检验样本量保证。
- 内容归类：同主题功能（工具决策、真实示例、技术解释、观点）与形式是两个变量；二者共同变化时无法识别哪一个造成结果。
- 每次做一项可辨别的实验假设，尽可能保持受众、素材质量、时间窗和制作投入相近；如条件允许按顺序交替类似题材的两个形式，避免一次发帖直接下结论。
- 实验前写明“原假设/如何保留或淘汰”，且不能修改数据口径追求漂亮结果。样本少时只能作方向性判断；不可标“显著提升”“已验证提升x%”。
- 异常侦测：零曝光、异常转推、版权/社区注释、帖子被限制传播等先检查账号状况、数据延迟、截取窗口和外部事件，不直接宣称被限流。
- 停止准则：内容质量被用户否决、出现版权/自动化风险、耗时明显不合理但未产生读者价值 → 立即停止或退回研究；连续足够样本表现差时再减配比。

## 5. 每周“运营官决策单”
**目标状态**：90天后台资格曝光、认证粉丝及最新来源，未知项列明。
**实际发布**：帖子数、URL、内容功能、内容格式、用户劳动量（如可得）。
**获益与问题**：至少一个有源依据的正向信号+一项不奏效/信息不足。引用具体帖而非“账号被算法惩罚”。
**本周最关键判断**：继续/调整/停止哪一个策略，置信度：高/中/低，为什么。
**下一周唯一可检实验**：何种对比、谁来审稿/发布、多久复核、哪个指标算结果。
**阻塞**：所需后台图片/API权限/版权素材；不能因缺数据就宣称自动化已配置。

## 6. 以现有账号开始的例子（仅提出假设）
2026-10-18 “7个AI漫画Github资源”第三方快照：9,685浏览、352收藏→每千浏览收藏约36.3，注意采集时长和来源。
另一个AI短片幕后曾自报早期30浏览，不能与上帖不同发布后时长直接比较，也不据此否定视觉内容。
实验候选：以“资源+原创用途决策”为既有正向候选，再和另一种真实AI演示/案例讲解做4–8条方向性比较，必须统一观察窗口，记录作品来源与用户实际审稿投入。该数量非统计显著保证。
优先申请资格页面截图验证自报7.7K字段名与500认证粉丝，而不是向用户建议盲目冲总浏览。
