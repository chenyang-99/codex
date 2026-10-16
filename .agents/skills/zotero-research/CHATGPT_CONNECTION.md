# 在 ChatGPT 对话中使用 Zotero — 连接方案与当前状态

> 当前文件用于区别「GitHub 中安装 Skill」与「在 ChatGPT 当前对话读取真实 Zotero 文献」。两者不是同一件事。

## 已经部署

- `.agents/skills/zotero-research/SKILL.md`：综述与精读操作规范
- `.agents/skills/zotero-research/scripts/zotero_cloud.py`：Zotero Web API v3 只读读取工具，支持公开用户库（不需要 API Key）与私有用户库（运行时安全凭据）
- 原版 ZotPilot MCP 服务的 STDIO 握手曾在 GitHub Actions 测试成功；这不表示已在 ChatGPT 运行。
- 本仓库**不托管**持续运行的 HTTP MCP 服务，也**不连接**任何具体 Zotero 用户账号。

## 方案 A：当前普通对话，公开 Zotero 文献库

如果 Zotero 用户资料、个人馆藏或群组馆藏是**公开可访问的**，用户提供对应 Zotero 公共链接或数字 library ID 即可：
1. ChatGPT 可经 Zotero 的公开 Web API 读取分类与文献条目。
2. 对公开的索引全文执行可用性检查；对于无法取回的 PDF，诚实标记「没有全文」。
3. 用 `zotero-research/SKILL.md` 的规范生成证据卡片、覆盖情况、对比表与综述。

**注意：**GitHub 仓库无需存放任何用户凭据。公开馆藏不一定公开所有 PDF 或全文。请勿把私有文献为了方便访问而贸然设为公开。

本仓库辅助脚本（在有网络的运行环境内）：

```bash
ZOTERO_USER_ID=475425 python3 .agents/skills/zotero-research/scripts/zotero_cloud.py collections
# 475425 仅为 Zotero API 文档公开示例 ID，不是本用户 ID
```

## 方案 B：私有 Zotero 文献库 + 当前 ChatGPT 对话

私有数据访问需经过**经授权的连接器**，不可以让用户在聊天、GitHub 文件、Issue 或公开 GitHub Actions 日志里粘贴密钥。

要建立真正可在 ChatGPT 中反复调用的连接，一般需要：
1. 使用 Zotero Web API v3 / ZotPilot 构建**鉴权的远程 MCP 服务**，或使用官方 Secure MCP Tunnel 接入局域网中的 MCP 服务。
2. 如果采用公网服务，部署到有持续运行环境及 HTTPS 的主机，服务器单独保管 Zotero API 凭据，建议只读权限与访问限制。GitHub 仓库本身只是源码托管，不是持续运行服务。
3. 按账户/工作区实际权限，通过 ChatGPT 的 **Plugins → + → Add custom MCP server** 连接**真实的 HTTPS MCP URL 或 Tunnel ID**，完成鉴权并安装插件。
4. 根据 ChatGPT 官方流程在可用的聊天或 Work 会话中用 `@` 选择该插件后调用工具。支持范围受套餐/工作区授权限制；不能保证所有普通聊天账号都提供此入口。

官方最新文档：
- https://help.openai.com/en/articles/12584461-connecting-custom-mcp-servers-in-chatgpt
- https://developers.openai.com/plugins/quickstart
- https://www.zotero.org/support/dev/web_api/v3/basics
- https://www.zotero.org/support/dev/web_api/v3/fulltext_content

## 方案 C：私有库、但没有自定义连接器权限

可在 Zotero 本地导出指定分类的 RIS/BibTeX/CSV，或上传相关 PDF 文件到 ChatGPT 对话；按文献集合和全文覆盖率执行相同的综述/精读流程。这不是实时同步，不应称为「已经连接 Zotero」。

## 验收规则

- [ ] 真实 Zotero 用户信息已授权并且能读取
- [ ] 能正确列出用户指定分类，分类名称和数量经用户核验
- [ ] 能列出分类里的论文，保留 Zotero item key / DOI
- [ ] 能统计可读取全文与仅摘要的篇数
- [ ] 可以逐条核验实验结论与实际来源
- [ ] 可以输出综述、方法对比表和精读报告

只有以上项目完成，才能宣称「已可在对话中操作 Zotero 文献库」。

## 安全约束

绝不可把 Zotero API Key、论文 PDF、私有书目或同步的全文内容提交到公开 GitHub 仓库。生成科研内容时始终区分 metadata 与全文证据。所有修改 Zotero 文献库的动作都必须另外得到用户明确授权。
