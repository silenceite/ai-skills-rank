# 给 AI 装技能，还是装间谍？

> **AI Agent Skills 安全科普指南**
>
> 2026 年 6 月 · 基于 OWASP Agentic Skills Top 10、NVIDIA SkillSpector 研究数据

---

## 一、先搞懂：什么是 AI Agent Skill？

你买了一部新手机，裸机能用，但想拍照得装相机 App，想导航得装地图 App。AI Agent 也一样——Claude Code、OpenClaw 这些 AI 助手出厂时是"裸"的，装上 Skill（技能）之后才能干特定的事。

比如：

- 装了「文档处理」skill，AI 就能帮你读写 Word/PDF/Excel
- 装了「前端设计」skill，AI 写出的网页就不再是千篇一律的 AI 风格
- 装了「代码审查」skill，AI 就能像资深工程师一样帮你检查代码质量

技术上，一个 Skill 本质上就是一个文件夹，核心是一个叫 **SKILL.md** 的 Markdown 文件，里面写着：什么时候触发、分几步执行、什么不能做、需要调用哪些工具。有些 skill 还会附带可执行脚本。

听起来很方便对吧？问题在于——**这个文件里写的自然语言指令，AI 会原封不动地执行**。如果指令是恶意的呢？

---

## 二、问题的本质：AI 信任了它不该信任的东西

> **核心安全漏洞**
>
> 当你安装一个 skill 时，它通常**和 AI 助手拥有相同的权限**——能读写你的文件、执行 shell 命令、发网络请求、访问环境变量里的 API 密钥。
>
> 安全模型更像浏览器扩展（能碰一切），而不是沙箱里的网页（被隔离）。但大多数用户以为它是后者。

这就好比你雇了一个保姆，你给了她你家钥匙、银行卡密码、快递柜权限。然后你在招聘网站上随便下载了一份"保姆工作手册"让她照着做——如果这份手册是坏人写的呢？她不会质疑，只会执行。

NVIDIA 在 2026 年 6 月发布了一项大规模研究，用自研的 SkillSpector 扫描器分析了 42,447 个公开 skill，结果令人不安：

| 指标 | 数值 |
|------|------|
| 含至少一个安全漏洞 | **26.1%** |
| 疑似恶意意图 | **5.2%** |
| 含可执行脚本的 skill 风险倍数 | **2.12 倍** |

翻译成大白话：**每 4 个 skill 就有 1 个有漏洞，每 20 个就有 1 个疑似故意使坏。** 含可执行脚本的 skill 风险更是翻倍。

> 数据来源：Liu et al., "Agent Skills in the Wild", 2026。扫描工具 NVIDIA SkillSpector v2.0.0，覆盖 64 种漏洞模式 × 16 个分类。

---

## 三、OWASP 官方：最严重的 10 种风险

OWASP（开放式 Web 应用程序安全项目，就是发布过著名的"Web 安全 Top 10"的那个国际组织）在 2026 年 6 月发布了专门针对 AI Agent Skills 的安全风险榜单——**Agentic Skills Top 10**。

下面按严重程度分三层解读，尽量说人话。

### 严重级（Critical）— 可以直接控制你的电脑

**AST01 恶意技能（Malicious Skills）**

- **什么意思：** 攻击者把窃取密钥的指令藏在 SKILL.md 的自然语言里。你装上去之后，AI 会忠实地执行——把你的 API 密钥、SSH 凭证、钱包私钥发到攻击者的服务器。
- **真实案例：** ClawHavoc 攻击一次性向注册表注入了 1,184 个恶意 skill。ToxicSkills 项目审计发现了 76 个恶意载荷。

**AST02 供应链妥协（Supply Chain Compromise）**

- **什么意思：** 不是 skill 本身有问题，而是"分发渠道"被攻击了。比如 skill 注册表被投毒，或者 skill 依赖的某个包被篡改。仓库级配置文件可以在你确认信任之前就触发远程代码执行。
- **真实案例：** ClawHub 注册表大规模中毒事件、Claude Code CVE-2025-59536 漏洞。

### 高危级（High）— 可能泄露你的数据

**AST03 过度授权（Over-Privileged Skills）**

- **什么意思：** 一个只需要"读取文件"的 skill，实际上被赋予了网络完全开放、文件系统完全访问的权限。就像你只想让保姆帮你取快递，却把整个家的钥匙都给了她。
- **真实案例：** Snyk 在 2026 年 2 月发现了 280+ 个存在凭证泄露的 skill。

**AST04 不安全元数据（Insecure Metadata）**

- **什么意思：** 攻击者伪造 skill 的元数据，冒充知名品牌。比如在 ClawHub 上发布一个名叫"Google 搜索"的 skill，用户以为是 Google 官方出品就装了。
- **真实案例：** ClawHub 上的假冒"Google"技能仿冒事件。

**AST05 不安全反序列化（Unsafe Deserialization）**

- **什么意思：** SKILL.md 里的 YAML 配置如果用不安全的解析器处理，攻击者可以嵌入恶意代码。OWASP 测试发现，**仅 3 行 Markdown 就能实现从配置文件到 Shell 访问的完整攻击链**。

**AST06 弱隔离（Weak Isolation）**

- **什么意思：** AI skill 在你的电脑上运行时隔离不充分。攻击者可以利用这个弱点在你电脑上横向移动、窃取更多凭证、安装持久化后门。
- **真实案例：** OpenClaw 主机模式执行，超过 135,000 个暴露实例被发现。

### 中危级（Medium）— 不直接攻击但放大风险

**AST07 更新漂移（Update Drift）**

- **什么意思：** 你今天装的是安全 skill，明天作者仓库被劫持或被卖掉，下次更新时恶意代码就跟着进来了。也可以通过暴力破解本地 WebSocket 连接劫持你的 AI 助手。
- **真实案例：** ClawJacked（CVE-2026-28363，CVSS 评分 9.9 / 10）。

**AST08 扫描不足（Poor Scanning）**

- **什么意思：** 很多平台用简单的关键词匹配来检查 skill 是否安全，但恶意指令是用自然语言写的，模式匹配根本检测不到。这给用户造成虚假的安全感。

**AST09 缺乏治理（No Governance）**

- **什么意思：** 很多组织对自己部署了哪些 AI skill 毫无清单，安全运营中心完全看不到。超过 53,000 个暴露实例没有任何安全监控覆盖，"影子 AI"泛滥。

**AST10 跨平台复用（Cross-Platform Reuse）**

- **什么意思：** 同一个恶意 skill 可以被移植到不同平台（OpenClaw、Claude Code、Cursor、VS Code），因为各平台格式不统一，安全元数据在迁移过程中丢失或削弱，相当于"换了个马甲"重新流通。

> **一个关键发现：** OWASP 明确指出，这 10 个风险影响**所有平台**——不区分 Claude Code、OpenClaw、Cursor、Codex 还是 Gemini CLI。这是一个跨生态的系统性安全问题，没有任何平台能独善其身。

---

## 四、普通用户怎么办：4 步识别法

你不需要懂代码，也不需要会做安全审计。以下 4 步每步只需 30 秒到 1 分钟，能帮你过滤掉 90% 的风险。

### 第 1 步：看出身（30 秒）

看这个 skill 是谁做的：

| 出身 | 可信度 | 说明 |
|------|--------|------|
| Anthropic / OpenAI / Vercel / NVIDIA 官方 | 最高 | 闭眼装 |
| 知名组织（Composio、Trail of Bits、科大讯飞） | 高 | 放心装 |
| Star 10K+ 且运营 6 个月以上 | 中高 | 看一眼再装 |
| 个人开发者、Star < 1K、创建不到 3 个月 | 中低 | 必须审查 |
| 无 README、无 commit 历史、批量生成 | 低 | 不装 |

### 第 2 步：看 SKILL.md 是否"说人话"（1 分钟）

打开仓库，找到 `SKILL.md`，快速扫一遍：

- **好的 skill：** 清楚定义触发条件、输入输出、约束规则，有示例
- **危险信号：** description 写成营销文案（"最强""终极""神器"）、没有约束规则、文件超过 500 行（说明职责不单一，可能藏了不该藏的东西）

### 第 3 步：看有没有可执行脚本（30 秒）

NVIDIA 数据显示含可执行脚本的 skill 风险高 2.12 倍。如果 skill 只有 Markdown 指令没有可执行脚本，风险大幅降低。

如果有 `scripts/` 目录，点进去看一眼。哪怕你看不懂代码，至少搜索一下有没有 `curl`、`wget`、`requests.post` 这些往外部发数据的关键词——如果有，而且你不是技术用户，建议不装。

### 第 4 步：看更新频率（30 秒）

看仓库最近一次提交是什么时候。超过 3 个月没更新的 skill，很可能已经和当前版本的 AI 助手不兼容了——不兼容不是安全问题，但可能导致不可预期的行为。

---

## 五、GitHub 高星 Skill 安全分级

以下是截至 2026 年 6 月 GitHub Star 最高的 AI Agent Skill，按安全可信度分三档。

### 闭眼装（官方或知名组织出品）

| Skill 名称 | Star | 安全理由 |
|-----------|------|---------|
| anthropics/skills | 148K | Anthropic 官方技能库，生态标准参考实现 |
| openai/skills | 20K | OpenAI Codex 官方技能目录 |
| vercel-labs/agent-skills | 27K | Vercel 官方技能包（web-design-guidelines） |
| vercel-labs/skills | 20K | Vercel 官方 CLI 工具链（npx skills） |
| trailofbits/skills | 5K | 顶级安全公司 Trail of Bits 出品，自带安全审计 |
| iflytek/skillhub | 4K | 科大讯飞出品，企业级技能注册中心 |
| remotion-dev/skills | 3K | Remotion 官方视频制作技能包 |

### 放心装（高 Star + 长期维护 + 社区验证）

| Skill 名称 | Star | 安全理由 |
|-----------|------|---------|
| affaan-m/everything-claude-code | 212K | 最多人用的全能框架，内置 AgentShield 安全审计 |
| obra/superpowers | 200K | 社区公认第一开发方法论，680K+ 安装量 |
| ComposioHQ/awesome-claude-skills | 64K | Composio 团队维护，集成平台背景 |
| shanraisshan/claude-code-best-practice | 58K | 长期维护的最佳实践指南 |
| hesreallyhim/awesome-claude-code | 41K | 仅收录 1K+ star 项目，有筛选门槛 |
| K-Dense-AI/claude-scientific-skills | 25K | 科研领域垂直，用户群体明确 |
| OthmanAdi/planning-with-files | 22K | 纯 Markdown 无脚本，零安全风险 |

### 需要看一眼再装

| Skill 名称 | Star | 注意事项 |
|-----------|------|---------|
| sickn33/antigravity-awesome-skills | 35K | 大合集（1,340+ skill），子 skill 未逐个审查 |
| VoltAgent/awesome-openclaw-skills | 50K | 5,400+ skill 大合集，同上 |
| alirezarezvani/claude-skills | 19K | 个人开发者，329 个 skill 需抽查 |
| anbeime/skill | 2K | 自动抓取 GitHub 的聚合商店，来源混杂 |

---

## 六、如果只装 3 个

这三个加起来覆盖了 80% 的日常需求，且全部无可执行脚本或来自官方，风险最低：

**1. anthropics/skills 的 frontend-design** — Anthropic 官方出品，让 AI 写出的界面有设计感，不再是千篇一律的 AI 风格。周安装量超过 564K。

**2. obra/superpowers 的 brainstorming（单独装这一个就行）** — 强制 AI 先想清楚再动手。没有这个 skill，AI 拿到需求就直接开写，常常方向偏了才发现；装了之后，它会先做需求分析、方案设计，确认无误后才动手。和资深工程师的工作方式一模一样。

**3. OthmanAdi/planning-with-files** — 把计划从聊天记录里提取出来，变成可 diff、可 review、可交接的文件。纯 Markdown 无脚本，零安全风险。支持 17+ IDE 和 AI 助手。

---

## 七、给技术用户的额外建议

如果你有一定技术背景，还可以做这些：

**用 git worktree 隔离测试：** 不要直接在主项目里装 skill。创建一个独立的 worktree，在里面测试通过后再迁移到主项目。

**跑一遍 SkillSpector：** NVIDIA 开源的安全扫描器，可以检测 64 种漏洞模式。

```bash
pip install skillspector
skillspector scan ./my-skill/ --no-llm
```

评分标准：

| 分数 | 严重程度 | 建议 |
|------|---------|------|
| 0–20 | LOW | 可以安装 |
| 21–50 | MEDIUM | 需审查 |
| 51–80 | HIGH | 不建议安装 |
| 81–100 | CRITICAL | 禁止安装 |

**用 .env 隔离敏感变量：** 不要让 AI 助手能访问到你的生产环境 API 密钥。为 AI 助手创建一个独立的 .env 文件，只放必要的、低权限的 key。

**锁定 skill 版本：** 不要用自动更新。锁定到经过审查的特定版本，更新时手动检查 diff。

---

## 八、结语

AI Agent Skills 生态让人想到 2015 年的浏览器扩展市场——早期、混乱、但充满可能性。它正在从"Claude 专属外挂"演化成"AI Agent 通用能力模块"，未来你写的一个 skill 可能同时跑在 Claude、Copilot、Cursor、Gemini 上。

但工具再多，核心问题不变：**你要解决什么问题？** 先想清楚需求，再去找对应的 skill，而不是反过来被工具推着走。

同时记住一个基本判断：**Star 数高说明用的人多，但不等于安全**。4 步识别法（看出身、看 SKILL.md、看脚本、看更新频率）只需 2 分钟，能帮你避开绝大多数坑。

> **最后一句话**
>
> 给 AI 装技能本身是对的——它让 AI 从"通用助手"变成"专业工匠"。但请像安装手机 App 一样保持警惕：看开发者、看权限、看评价。AI 行业的"App Store 审核"还在建设中，在那之前，你自己就是最后一道防线。

---

## 数据来源与参考文献

1. OWASP Foundation, "Agentic Skills Top 10 v0.5", 2026年6月, https://owasp.org/www-project-agentic-skills-top-10/
2. Liu et al., "Agent Skills in the Wild", 2026（NVIDIA SkillSpector 研究基础，扫描 42,447 个 skills）
3. NVIDIA, "SkillSpector: Security Scanner for AI Agent Skills v2.0.0", 2026年6月, https://github.com/NVIDIA/SkillSpector （Apache 2.0）
4. Snyk, "AI Agent Skills Security Audit", 2026年2月（发现 280+ 凭证泄露技能）
5. Microsoft Security Blog, "When prompts become shells: RCE vulnerabilities in AI agent frameworks", 2026年5月7日
6. Anthropic, "anthropics/skills 官方技能仓库", 2026年5月17日开源, https://github.com/anthropics/skills
7. arXiv:2601.17548, "Prompt Injection Attacks on Agentic Coding Assistants: A SoK", 2026年1月24日
8. GitHub Topics: claude-code-skills / openclaw-skills（Star 数据快照，2026年5-6月）

> **免责声明：** 本文 Star 数据为 2026 年 5-6 月多源快照，不同来源存在差异，实时数据以 GitHub 页面为准。安全风险分类基于 OWASP 和 NVIDIA 研究报告，具体 skill 的安全性以最新审计结果为准。本文不构成安全建议，仅供参考。

---

*AI Agent Skills 安全科普指南 · 2026 年 6 月 · 共建安全的 AI 生态*
