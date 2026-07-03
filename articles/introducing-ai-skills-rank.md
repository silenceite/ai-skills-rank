# 我搭了一个「AI Agent Skills 大众点评」：不只看 Star，更看安不安全

> 一句话：帮你从 GitHub 上 1400+ 个 AI Skills 里，快速找到**值得用、放心用、适合中文用户**的那一个。

---

## 01 为什么做这件事？

2026 年，AI Agent 的 "Skill 生态" 彻底爆发了。

Claude Code、OpenClaw、Cline、Cursor 这些工具都在推自己的 Agent Skill 格式。GitHub 上以 `claude-code-skills`、`openclaw-skills`、`agent-skills` 为标签的仓库已经**超过 1400 个**（数据来源：GitHub Topics 公开统计，2026-06）。

但问题也来了：

- **信息太散**：今天掘金一篇推荐，明天 Twitter 一个 thread，没有一个统一的索引。
- **Star 会骗人**：一个仓库 Star 高，可能只是早期宣传好，不代表它还在维护、没有安全坑。
- **中文用户断层**：大量 Skill 是纯英文，安装说明、触发词、示例全是英文，中文用户上手成本高。

所以，我搭了这个项目：**AI Skills Rank**。

---

## 02 我们想解决 3 个问题

1. **谁最火？** —— 不看单维 Star，而是看综合热度与增长。
2. **谁还在认真维护？** —— 维护频率、贡献者、Issue 响应都是硬指标。
3. **谁可以放心装？** —— 安全评级是我们最看重的差异化。

此外，针对中文生态，我们额外做了两个维度：

- **中文友好度**：有没有中文 README、中文示例、中文维护者。
- **国产创作**：中国开发者做出了哪些值得关注的 Skill。

---

## 03 五张榜单，每个月自动更新

| 榜单 | 更新时间 | 解决什么问题 | 查看地址 |
|------|---------|------------|---------|
| 🔥 Star 榜单 | 每月 1 日 | 谁最火 | [链接](https://silenceite.github.io/ai-skills-rank/reports/2026-06/top50-ai-skills-2026-06.html) |
| ⚡ 活跃度榜单 | 每月 2 日 | 谁还在维护 | [链接](https://silenceite.github.io/ai-skills-rank/reports/2026-06/active-ai-skills-2026-06.html) |
| 🛡️ 安全分级榜单 | 每月 3 日 | 谁可以放心装 | [链接](https://silenceite.github.io/ai-skills-rank/reports/2026-06/secure-ai-skills-2026-06.html) |
| 🇨🇳 中文友好榜单 | 每月 4 日 | 中文用户看得懂吗 | [链接](https://silenceite.github.io/ai-skills-rank/reports/2026-06/cn-friendly-skills-2026-06.html) |
| 🚀 国产创作榜单 | 每月 5 日 | 中国开发者做了什么 | [链接](https://silenceite.github.io/ai-skills-rank/reports/2026-06/cn-made-skills-2026-06.html) |

整个站点托管在 **GitHub Pages**，完全免费、无服务器、无广告。

---

## 04 安全分级：我们最看重的差异化

为什么安全这么重要？

因为 AI Skill 和传统开源库不一样。一个 Skill 可能包含：

- 调用外部命令或脚本
- 读取你的文件系统
- 访问网络 API
- 在你的 Agent 会话里执行指令

如果你的 Agent 被装了一个不安全的 Skill，它可能在你不知情的情况下**删除文件、泄露敏感信息、调用恶意 API**。

OWASP 在 2026 年发布的 **Agentic Skills Top 10** 中，已经把 "不安全的 Skill 供应链" 列为重点风险之一（来源：OWASP Foundation, *Agentic Skills Top 10*, 2026）。

我们的安全分级从 6 个维度评估：

| 维度 | 权重 | 说明 |
|------|------|------|
| 出品方可信度 | 25% | 官方/知名组织/个人/无名 |
| 可执行脚本风险 | 20% | 是否包含高危函数、外部请求 |
| SKILL.md 质量 | 15% | 触发条件、约束、示例是否清晰 |
| 维护活跃度 | 15% | 最近是否在维护 |
| 社区审查程度 | 15% | Star / Issue / PR 反馈量 |
| 已知安全记录 | 10% | 是否有公开安全报告或社区警示 |

评级结果分为 S / A / B / C / D 五级：

- **S 级**：闭眼装，官方或高信誉团队出品，无高危脚本。
- **A 级**：放心装，维护活跃，社区审查充分。
- **B 级**：看一下 SKILL.md 再装。
- **C 级**：需要审查，谨慎安装。
- **D 级**：不建议安装。

> ⚠️ 安全评级**仅供参考**，不是绝对保证。具体使用请以官方说明为准。

---

## 05 数据怎么来的？

所有榜单都基于公开数据，每个月 1-5 日由 **GitHub Actions** 自动更新：

- **GitHub API**：仓库 Star、Fork、贡献者、最近提交、Issues、PR。
- **GitHub Topics**：发现 `claude-code-skills`、`openclaw-skills`、`agent-skills` 等标签下的仓库。
- **公开安全报告**：OWASP、NVIDIA SkillSpector、Snyk 等社区安全资源。
- **中文社区**：掘金、知乎、CSDN、V2EX、公众号等平台的讨论度。

我们没有人工干预排名，只按规则打分。规则全部开源在仓库里，欢迎审查。

---

## 06 项目怎么用？

**普通用户：**

直接打开首页，按你的需求选一个榜单：

👉 `https://silenceite.github.io/ai-skills-rank/`

- 想跟风装热门的 → 看 Star 榜单
- 想长期稳定使用的 → 看活跃度榜单
- 怕被坑的 → 看安全分级榜单
- 英文不好的 → 看中文友好榜单
- 想支持国产的 → 看国产创作榜单

**开发者/创作者：**

如果你做了 Skill 想被收录，欢迎在 GitHub 提交 Issue 推荐。收录标准是：**公开仓库、有完整的 SKILL.md、属于 AI Agent Skill 范畴**。

---

## 07 这项目现在是什么阶段？

目前是 **MVP 已上线，验证阶段**。

已完成：

- ✅ 五榜单体系与评分模型
- ✅ 5 个 Python 采集脚本
- ✅ 5 个 GitHub Actions 自动 workflow
- ✅ GitHub Pages 部署
- ✅ 首月（2026-06）报告上线
- ✅ 安全科普文档（含抖音图文版）

接下来 1-2 个月会重点做：

- 数据缓存，减少 GitHub API 调用
- 历史对比（NEW / 上升 / 下降 / 跌出）
- 安全扫描真实接入
- 社区贡献指南

3-6 个月考虑产品化：搜索、筛选、趋势图、独立域名。

---

## 08 写在最后

AI Agent 的 Skill 生态还在早期，现在正是建立"评估标准"的好时机。

我希望这个榜单能帮你：

- **少踩坑**：先看安全分级，再决定装不装。
- **省时间**：不用自己翻 GitHub 翻半天。
- **看到国产作品**：让更多中国开发者被看见。

如果你也觉得这件事有用，欢迎：

- 🌟 给仓库点个 Star：`https://github.com/silenceite/ai-skills-rank`
- 📝 转发给用 AI Agent 的朋友
- 🐛 在 GitHub Issue 里提交反馈或纠错

下个月 1-5 日，榜单会自动更新。到时候见。

---

## 参考链接

- 项目仓库：https://github.com/silenceite/ai-skills-rank
- 在线榜单：https://silenceite.github.io/ai-skills-rank/
- 安全科普：https://silenceite.github.io/ai-skills-rank/SECURITY_GUIDE.html
- OWASP Agentic Skills Top 10（2026）
- GitHub Topics: `claude-code-skills`, `openclaw-skills`, `agent-skills`

---

*作者：silenceite · 项目：AI Skills Rank · 更新时间：2026-06-19*
