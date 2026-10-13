# 国内赛道热门内容与评论：开源采集器部署预检

## 目的
比较在合法授权范围内支持小红书/抖音关键词搜索、作品详情、评论及二级回复的现有源码。**这里部署的是无需账号的安装与 CLI 健康测试，不是声称已拿到真实两平台评论。**

## 候选方案与许可证

1. **MediaCrawler**: https://github.com/NanmiCoder/MediaCrawler — 一体支持 XHS、抖音、关键词、详情、主页、一级/二级评论；但使用登录态、浏览器，且 `NON-COMMERCIAL LEARNING LICENSE 1.1` 禁止未经许可的商业使用。不要直接投入商业选题监测；本仓库不复制或运行其爬虫代码。
2. **redbook-cli**: https://github.com/Youhai020616/xiaohongshu — MIT；小红书搜索（可按点赞排序）、笔记详情及评论；需要 MCP/浏览器扫码登录，CLI 本身不具备免登录抓取功能。
3. **douyin-cli**: https://github.com/Yht20927/douyin-cli — MIT；抖音关键词搜索、视频评论、楼中楼，但需要用户已经登录的浏览器、Tampermonkey 脚本和本地 Bridge 服务。项目设计主要用于自有账号运营，需要先评估使用条款与账号风险。

## GitHub Actions 云端能做什么

新增 `Domestic collector read-only preflight` 工作流：在临时的 GitHub Linux 运行器中拉取**固定提交版本**的两个 MIT 工具，安装依赖并执行 CLI 帮助/语法健康检查。没有平台登录、没有 Cookie、没有 GitHub Secrets、没有采集或发布操作。运行器结束后程序不会永久驻留。

**重要：** 此预检成功只代表工具能在临时云端安装并启动 CLI，并不说明小红书/抖音采集接口可用，也不表示存在已登录浏览器。

如果以后放宽“完全不登录”的条件，并确认实际用途符合平台规则，才可在授权的**独立、持久化主机**上配置浏览器登录及本地数据存储。不得把个人账户 Cookie 或评论明细提交到当前公开 GitHub 仓库。VPS/托管服务器不在此前连接的 GitHub Actions 资源中，也未购买或部署。

## 目标赛道和选题排序

`sector-watchlist.json` 列出了需按受众持续研究的赛道关键词、热门作品候选判定字段、真实评论中的需求痛点分类。它是配置模板，不会神奇开启受限制的平台 API。

每个真实作品需要 `platform,keyword,url,published_at,likes,comments_count,collects,shares`（只填写确实取得的字段）；根据作品发布时间做 7 天/30 天分组；避免将不同平台的绝对互动量直接比较。评论必须保留原帖 URL、样本数量和采集时间，匿名化处理个人信息。

## 现阶段运行方式

GitHub -> Actions -> `Domestic collector read-only preflight` -> Run workflow。查看 `xhs` 与 `douyin` 两个 Job 的运行日志；没有登录成功与评论实际返回的证据，不得宣传部署已打通。

若坚持**零平台账号登录、零额外付费**，目前没有在 GitHub 数据中心已实测通过的“任意关键词检索 + 全部评论”开源组合。已实际跑通的 B 站和 V2EX 评论仍由原选题雷达工作流负责。