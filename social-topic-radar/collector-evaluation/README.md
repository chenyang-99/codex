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