# 国内平台公开搜索与评论：当前能力与官方授权路线

最后核验日期：2026-10-13。

## 已确认的匿名数据入口

- 抖音公开热榜：在 GitHub 云端取得过 12 条热榜项目，但不是任意视频或评论。
- 小红书：匿名 CLI 在 GitHub 云端返回 -101，需登录；未取得公开笔记正文或评论。
- Bing/Google News RSS/DuckDuckGo/Mojeek/Sogou：公开索引尝试未取得可验证的单作品链接；索引并非平台原生搜索。
- TinyFish Search：在 ChatGPT 中按需搜索过抖音链接，但部分链接跳到推荐页/404；不代表原作品可打开，也不能让 GitHub CI 无凭证直接调用 ChatGPT 的连接器。
- B 站、V2EX：已实际取得公开评论，可作为中文 AI 需求信号；不能冒充小红书/抖音评论。
- 新增文件 domestic-index-seeds.json 和 domestic_permalink_verification.py：持续检查索引中的链接是否真的返回原作品的专属元数据。

## 抖音官方路径

关键词视频管理 https://open.douyin.com/platform/resource/docs/ability/search-management/video/
该接口可查看指定业务关键词的视频及评论，但需要申请特殊权限、用户授权，且关键词必须与申请者自身品牌/业务直接相关；不可申请通用品类或竞品品牌词，仅覆盖最近一天。不可当作任意 AI 视频搜索与评论 API。
通用视频搜索实验能力 https://partner.open-douyin.com/docs/resource/zh-CN/dop/ability/search-management/item-search 在官方文档中为暂不对外开放。
视频评论管理 https://open.douyin.com/platform/resource/docs/ability/interaction-management/video-comment-management-solution 也需要相应权限/授权。

## 小红书官方路径

权限说明 https://openaccount.xiaohongshu.com/docs/scope 首期仅开放 basic_info，read_notes 等仍在规划，并无公开匿名全站搜索与评论接口。

## 数据证据等级

1. 实际拿到原始公开评论：必须附评论文本、原帖链接、采样数量和来源。
2. 验证到作品专属元数据：不代表已取得全文/评论。
3. 搜索索引标题与摘要：仅作线索，不代表原帖仍存在。
4. 登录要求/404/跳转推荐页/限流：必须标为受限或未验证，不能推测没有评论。

## 可执行策略

保持零账号登录及零额外付费时，以 B 站、V2EX、GitHub 公开讨论作中文需求研究主来源；第三方公开索引作小红书/抖音竞品线索。真正需要原生评论数据时，只能申请/取得合适的授权或使用被明确许可的数据服务。用户并未同意新增付款或登录其主账号。不得绕过验证码、登录、限流或平台风控。

当前报告在 GitHub Actions Artifacts 保留 14 天；ChatGPT 连接器并不会自动变成 GitHub Actions 可调用的 API。