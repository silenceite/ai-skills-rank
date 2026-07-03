# 给AI装个"技能包"：一文看懂AI Agent Skill到底是什么

> 你可能还在跟AI聊天，但有人已经给AI装上了"外挂"。

---

## 写在前面

2026年5月，Anthropic在GitHub上开源了官方Agent Skills仓库（`anthropics/skills`），短短3天斩获138k Star，登上GitHub Trending榜首。

这不是一个普通的开源项目。它标志着一件事：**AI助手正在从"聊天工具"变成"能干活的平台"**。

而这一切的核心，就是一个叫 **Agent Skill** 的东西。

今天这篇文章，我就来科普一下：Agent Skill到底是什么？它怎么工作的？为什么它可能改变你使用AI的方式？

---

## 01 先说结论：Agent Skill就是给AI装"技能包"

用一句话解释：

> **Agent Skill是一组文件夹，里面装着指令、脚本和资源，AI助手可以根据任务需要自动加载这些文件，从而获得新的能力。**

——来源：Anthropic官方工程博客，2025年10月16日，《Equipping agents for the real world with Agent Skills》

打个比方：

- 以前你用AI，像招了一个聪明但什么都不会的实习生——你得手把手教每件事
- 现在有了Skill，像给这个实习生发了一本《新员工入职手册》——他自己知道该怎么做了

Anthropic的工程团队是这么说的：

> "Building a skill for an agent is like putting together an onboarding guide for a new hire."
> （给Agent写一个Skill，就像给新员工准备一份入职指南。）

——来源：同上，作者 Barry Zhang、Keith Lazuka、Mahesh Murag

这个比喻很精准。Skill不是"插件"那种机械的代码扩展，而是把**人的经验和流程**打包成AI能理解的格式。

---

## 02 一个Skill长什么样？

一个完整的Skill，本质上就是一个文件夹：

```
my-skill/
├── SKILL.md          # 核心指令文件（必需）
├── scripts/          # 可执行脚本（可选）
│   └── helper.py
├── references/       # 参考文档（可选）
│   └── REFERENCE.md
└── assets/           # 模板、示例等资源（可选）
    └── template.json
```

其中，`SKILL.md` 是唯一必需的文件，也是整个Skill的大脑。

它的结构很简单，分两部分：

**第一部分：YAML前置元数据**（告诉AI"什么时候用我"）

```yaml
---
name: my-skill-name
description: 清晰描述这个技能做什么、什么时候该用
---
```

**第二部分：Markdown正文**（告诉AI"具体怎么做"）

```markdown
# My Skill Name

## When to use this skill
- 场景1
- 场景2

## Instructions
1. 第一步...
2. 第二步...

## Examples
- 示例1
- 示例2
```

就这么简单。没有复杂的API，没有SDK，没有编译步骤。

——来源：GitHub `anthropics/skills` 官方仓库 README；Build Fast with AI, "Claude Skills: The Complete 2026 Guide", 2026年5月13日

---

## 03 核心原理：渐进式披露（Progressive Disclosure）

这是Agent Skill最精妙的设计，也是它区别于传统"插件"的关键。

传统插件的痛点是：**装得越多，系统越慢**。因为所有插件都常驻内存。

Agent Skill用了完全不同的策略——**渐进式披露**，分三层加载：

### 第一层：发现（Discovery）

会话启动时，AI只读取每个Skill的 `name` 和 `description` 两个字段。

- 每个技能约消耗 **100 tokens**
- 你装50个Skill，启动成本才5000 tokens
- 这就是为什么"你可以安装50个技能却几乎注意不到开销"

——来源：Duet.so, "Claude Code Skills Complete Guide", 2026

### 第二层：激活（Activation）

当用户说了某句话，AI判断这句话跟某个Skill的 `description` 匹配，就会自动把完整的 `SKILL.md` 正文加载到上下文中。

- 加载量约 **1K-5K tokens**
- **不需要用户手动调用**——AI自己决定要不要用
- 这跟传统的"斜杠命令"完全不同

### 第三层：执行（Execution）

如果Skill还带了脚本和参考文件，AI会在需要时才读取它们。

- 脚本可以直接执行，不需要加载到上下文
- 参考文件按需读取，不用不读

用一个流程图来理解：

```
用户打开AI助手
    ↓
AI扫描所有已安装Skill的 name + description（~100 tokens/个）
    ↓
用户说："帮我填一下这个PDF表格"
    ↓
AI匹配到 PDF Skill 的 description
    ↓
AI自动加载 pdf/SKILL.md 完整内容（~3K tokens）
    ↓
AI发现需要填表单，再读取 forms.md 参考文件
    ↓
AI执行 scripts/extract_fields.py 提取表单字段
    ↓
AI按照Skill中的指令填写表单
    ↓
完成！用户全程不需要说"使用PDF技能"
```

Anthropic官方对此的解释是：

> "Progressive disclosure is the core design principle that makes Agent Skills flexible and scalable. Like a well-organized manual that starts with a table of contents, then specific chapters, and finally a detailed appendix, skills let Claude load information only as needed."
> （渐进式披露是Agent Skills的核心设计原则。就像一本组织良好的手册——先有目录，再有章节，最后是附录——Skills让AI按需加载信息。）

——来源：Anthropic工程博客，2025年10月16日

---

## 04 最关键的一个字段：description

如果你要自己写Skill，记住一句话：

**description不是文档，是触发器。**

AI就是靠 `description` 这个字段来决定"现在要不要加载这个Skill"。

写得好，Skill能在对的时刻自动激活；写得差，要么永远不触发，要么在不该触发的时候乱触发。

Anthropic官方推荐的描述公式：

> **做什么 + 什么时候用 + 产出什么**

举个例子：

❌ 差的描述：
```yaml
description: PDF处理工具
```

✅ 好的描述：
```yaml
description: 提取PDF表单字段并自动填写。当用户需要处理PDF表单、填写申请表或提取表单数据时使用此技能。
```

Build Fast with AI 的指南中有一句话总结得很到位：

> "Most skill failures are description failures, not instruction failures."
> （大多数Skill失败是描述失败，不是指令失败。）

——来源：Build Fast with AI, "Claude Skills: The Complete 2026 Guide", 2026年5月13日

---

## 05 为什么这是一件大事？

### 第一，它是一个开放标准

2025年12月18日，Anthropic把Agent Skills格式发布为**开放标准**，站点在 `agentskills.io`。

这意味着什么？

同一个 `SKILL.md` 文件，可以在多个AI工具上运行：

| 工具 | 支持情况 |
|------|---------|
| Claude Code | 完整支持（含高级功能） |
| OpenAI Codex CLI | 支持核心格式 |
| Cursor | 支持核心格式 |
| Gemini CLI | 支持核心格式 |
| GitHub Copilot | 支持核心格式 |

——来源：Build Fast with AI, 2026；agentskills.io

换句话说：**你写一个Skill，五大AI工具都能用**。这在AI工具历史上是第一次。

### 第二，生态爆发式增长

一组数据感受一下：

- 2025年10月：Anthropic发布Agent Skills
- 2025年12月：开源为开放标准
- 2026年5月：官方仓库3天138k Star
- 2026年6月：社区技能总数超过 **120万**（跨市场索引）

——来源：GitHub `anthropics/skills`；Build Fast with AI, 2026；aitoollab.cn, 2026

其中，最受欢迎的 `frontend-design` 技能安装量超过 **27.7万次**。

### 第三，Skills vs MCP vs Subagents

很多人分不清Skills、MCP和Subagents的区别。Anthropic给了一个清晰的判断框架：

| 特性 | Skills | MCP Servers | Subagents |
|------|--------|-------------|-----------|
| 功能 | 教AI**怎么做** | 连接AI到**外部系统** | 在**独立上下文**中运行专门工作 |
| 上下文成本 | 空闲~100 tokens，激活~5K | 每个服务器1万+ tokens（常驻） | 独立上下文窗口 |
| 调用者 | AI自动调用 | AI按需调用 | 你或AI委派 |
| 最适合 | 流程知识、团队规范 | API、数据库、文件系统 | 异步工作、长研究 |

一个典型的生产环境配置：
- 5-10个Skills（团队工作流）
- 3-5个MCP Servers（外部系统连接）
- 2-4个Subagents（委派任务）

——来源：Duet.so, "Claude Code Skills Complete Guide", 2026

Anthropic团队有一句很精辟的总结：

> "If you've got more skills than MCP servers, you're probably doing it right."
> （如果你的Skills比MCP服务器多，你可能做对了。）

---

## 06 安全：这是必须说的事

Skill能干什么？它能**在你的环境里执行代码**。

> "Skills can execute arbitrary code in Claude's environment."
> （Skills可以在Claude的环境中执行任意代码。）

——来源：Build Fast with AI, 2026

这意味着，一个恶意的Skill可以：
- 读取你的文件系统
- 向外部服务器发送数据
- 执行危险命令
- 在AI会话中注入恶意指令

Anthropic官方的安全建议是：

> "We recommend installing skills only from trusted sources. When installing a skill from a less-trusted source, thoroughly audit it before use."
> （我们建议只从可信来源安装Skills。从不太可信的来源安装时，使用前要彻底审计。）

——来源：Anthropic工程博客，2025年10月16日

OWASP也在2026年发布了《Agentic Skills Top 10》，将"不安全的Skill供应链"列为重点风险。

——来源：OWASP Foundation, *Agentic Skills Top 10*, 2026

**普通用户的自查清单：**

1. ✅ 只装官方或高信誉来源的Skill
2. ✅ 安装前看一眼 `SKILL.md` 内容
3. ✅ 重点检查 `scripts/` 目录有没有可疑代码
4. ✅ 注意有没有外部网络请求
5. ✅ 不需要的Skill及时卸载

---

## 07 怎么开始用？

### 如果你用 Claude.ai（网页版）

付费计划用户已经内置了官方Skills，直接用就行。比如让Claude创建PDF、PPTX、DOCX文件时，它会自动调用对应的文档技能。

### 如果你用 Claude Code（开发者）

在终端里运行：

```bash
/plugin marketplace add anthropics/skills
/plugin install example-skills@anthropic-agent-skills
```

安装后直接跟Claude说你要做什么，它会自动匹配技能。

### 如果你想自己写Skill

1. 创建一个文件夹（名字用小写加横线，如 `my-skill`）
2. 在里面创建 `SKILL.md` 文件
3. 写上 `name` 和 `description`
4. 写上指令正文
5. 放到 `~/.claude/skills/` 目录下

就这样。不需要注册，不需要发布，不需要审核。

Anthropic官方仓库里有一个 `template` 文件夹，可以直接复制来改。

——来源：GitHub `anthropics/skills` 官方仓库

---

## 08 写在最后

Agent Skill的本质，是把**人的经验**变成**AI的能力**。

以前，AI的聪明程度取决于模型有多大。
现在，AI的能干程度取决于你给它装了多少Skill。

这跟手机的发展路径很像：
- 2007年iPhone发布 → 有了"应用"的概念
- 2008年App Store上线 → 生态爆发
- 2025年Agent Skills发布 → AI有了"技能"的概念
- 2026年生态爆发 → 120万+技能

我们正在见证一个新的"App Store时刻"——只不过这次，"应用商店"里的商品不是给人用的，而是给AI用的。

如果你也想了解哪些Agent Skill值得装、哪些安全、哪些适合中文用户，可以看看我做的项目：

🔗 **AI Skills Rank**：`https://silenceite.github.io/ai-skills-rank/`

每月自动更新五个榜单：Star排名、活跃度、安全分级、中文友好、国产创作。

---

## 参考来源

1. Anthropic工程博客，"Equipping agents for the real world with Agent Skills"，2025年10月16日，作者 Barry Zhang / Keith Lazuka / Mahesh Murag
2. Agent Skills 开放标准，`agentskills.io`，2025年12月18日发布
3. GitHub `anthropics/skills` 官方仓库，`https://github.com/anthropics/skills`
4. Build Fast with AI, "Claude Skills: The Complete 2026 Guide", 2026年5月13日
5. Duet.so, "Claude Code Skills Complete Guide: SKILL.md, MCP, Subagents & Teams", 2026
6. OWASP Foundation, *Agentic Skills Top 10*, 2026

---

*作者：silenceite · 更新时间：2026-06-20*
*本文首发于公众号，转载请注明出处。*
