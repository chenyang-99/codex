# 国内采集工具严格免登录审查（2026-10-13）

**强制约束**：不登录小红书/抖音账号、不扫码、不读取/导入个人或访客 Cookie/Token、不调用收费第三方 API、不绕过登录/验证码/访问限制。目标：搜索关键词、赛道热门作品、实际一级与二级评论。

## 对候选项目的源码级结论

| 项目 | 开源源码 | 零账号登录 | 零 Cookie/Token | 关键词搜索与评论 |
|---|---|---|---|---|
| [MediaCrawler](https://github.com/NanmiCoder/MediaCrawler) | 是，非商用学习许可证 | 否，使用浏览器登录态 | 否 | 声明支持，但不符合本项目 |
| [redbook-cli](https://github.com/Youhai020616/xiaohongshu) | 是，MIT | 否，需扫码登录 | 否 | 声明支持，但不符合本项目 |
| [douyin-cli](https://github.com/Yht20927/douyin-cli) | 是，MIT | 否，需登录浏览器及 Bridge | 否 | 声明支持，但不符合本项目 |
| [feedgrab](https://github.com/iBigQiang/feedgrab) | 是 | README 称 xhs-so 无需登录 | **否**：`feedgrab/fetchers/xhs_api.py` 的 `is_api_available()` 依赖 `sessions/xhs.json`；`_extract_cookies_from_session()` 要求 `a1`，缺失则提示 `feedgrab login xhs` | 不得将 README 宣称解释为真正零会话验证 |
| [xhshow](https://github.com/Cloxl/xhshow) | 是 | 文档示例可生成游客标识 | **否**：签名仍需要 `a1` 等 Cookie | 不是完整独立爬虫 |
| [XHS-Downloader](https://github.com/JoeanAmier/XHS-Downloader) | 是 | 部分作品解析可能不登录 | 可选 Cookie，但功能有局限 | 不是已验证的免登录全站搜索+评论 |
| [Douyin_TikTok_Download_API](https://github.com/Evil0ctal/Douyin_TikTok_Download_API) | 是 | 官方文档说游客身份无需个人账号 | **否**：游客身份池依赖 `ttwid` 等 Cookie；且浏览器/代理/独立服务可能需要成本 | 不满足本次严格条件 |

**现场采集证据**：此前 GitHub Actions 匿名小红书信息流返回 `-101`，没有任何笔记；抖音匿名热榜成功获取 12 条，但不等于关键词搜索与评论；四种搜索索引 16 组测试未取得有效帖子；B 站和 V2EX 可取得真实公开评论，来源不能冒充小红书/抖音。

## 实际部署状态

**未部署、不自动启动**任何要求登录、个人 Cookie 或游客 Cookie 的 XHS/抖音爬虫。没有新建“已安装两个 CLI”的 workflow；本目录是源码审查而非虚构完成安装。继续运行旧版 `anonymous-social-probe.yml` 进行已验证的公开数据源监测与诊断。

## 严格验收门槛

任何新候选必须同时做到：① 无账号登录、验证码/风控绕行、个人或游客 Cookie/Token；② 不依赖收费 API；③ GitHub 云端实际返回指定 AI 关键词的作品及可核对发布时间/热度；④ 实际获取这些作品的公开一级评论和部分二级回复；⑤ 清楚记录来源、取得条数和不能获取的部分；⑥ 适用许可证容许预期用途。

没有符合门槛的实测结果，就不能声称全链路成功。

如果用户之后**明确允许仅限临时匿名访客 Cookie**，可以单独重新评估不绑定真实账号的方案；这与本次严格“无 Cookie”条件不同，不可擅自放宽。

## 2026-10-13 用户新增授权：允许临时游客会话

用户已明确允许程序自行生成、随任务销毁的游客 Cookie，但仍不允许登录其本人小红书/抖音账号、不使用个人 Cookie、不购买额外服务。此前要求的严格「零 Cookie」已相应放宽，仅限临时游客身份。

### 新增独立预检

工作流 [guest-only-domestic-evaluation.yml](../../.github/workflows/guest-only-domestic-evaluation.yml) 已写入仓库，当前仅支持在 GitHub Actions 手动启动：
- 小红书使用此前的 `xhs_public.py` 项目现成游客信息流探针，不创建持久化个人会话，不尝试登录；它此前在 GitHub 数据中心返回过要求登录的 `-101`。
- 抖音读取官方开源项目 [Evil0ctal/Douyin_TikTok_Download_API](https://github.com/Evil0ctal/Douyin_TikTok_Download_API) 固定提交，进行 Docker Compose 配置静态检查；**不启动数据库、浏览器或评论爬虫**，所以不能证明搜索及评论采集成功。

当前状态是**手动运行测试工作流已部署，尚未执行这一轮测试**。这不是一台已经安装并运行的常驻 VPS。抖音完整游客服务需要独立 Linux 主机，并按项目文档配置持久存储；GitHub Actions 临时运行器不适合作为其长期部署环境。

本次没有任何真实小红书或抖音评论被新组件验证获取；不得把旧的 B 站 / V2EX 评论列成两平台的评论数据。


## 2026-10-13 二次筛选补充

- [why20261/xiaohongshu-keyword-search](https://github.com/why20261/xiaohongshu-keyword-search) 和 [why20261/douyin-datas-insight](https://github.com/why20261/douyin-datas-insight)：仓库标题和 README 均声称“免登录、支持搜索、评论、热门”；但实际需要向 guaikei.com 申请 `GUAIKEI_API_TOKEN`，调用的是第三方托管 API。此服务不是免费的自托管爬虫，不自动申请/开通，也不能把“免平台账号”误称为“完全无外部依赖”。
- [LIghtJUNction/douyin](https://github.com/LIghtJUNction/douyin)：公开 README 明确要求已登录浏览器 Cookie 才能执行网页搜索和评论；OpenAPI 需要 OAuth 授权，不符合。
- [Johnserf-Seed/f2](https://github.com/Johnserf-Seed/f2)：FAQ 明确说明游客 Cookie 不稳定，遇到返回空可能仍需网页登录态，不能当作无需认证的稳定保证。
- [jackwener/xiaohongshu-cli](https://github.com/jackwener/xiaohongshu-cli) 和 [lucasygu/redbook](https://github.com/lucasygu/redbook)：可实现搜索和评论，但前者文档要求浏览器 Cookie / 扫码登录，后者需独立核实登录依赖；尚无 GitHub 云端游客登录状态下同时取回关键词笔记和实际评论的证据。
- 增加 `guest_visible_browser.py`，基于 Chromium 真实渲染公开搜索页面，独立验证是否有可见作品链接；2026-10-13 第一次两平台均返回 HTTP 200，但可识别作品直达链接为 0 条，评论为 0 条，不计入成功。

自动执行记录：https://github.com/chenyang-99/codex/actions/runs/38327327305；6 小时周期的持续攻关由 ChatGPT 定时任务负责，只有实际检验的新能力才报告突破。遭遇明确访问限制的入口不能反复刷新或尝试绕过。
