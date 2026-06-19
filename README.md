# AI Skills Rank

> AI Agent Skills 的"大众点评" — 不只看 Star，更看活跃度、安全性和中文友好度。
>
> English | [中文](./README_CN.md)

---

## 这是什么？

AI Agent Skills 生态在 2026 年爆发——GitHub 上已有 1,400+ 个 skill 仓库。但用户面临三个痛点：

1. **信息碎片化**：不知道哪些 skill 值得装
2. **Star 陷阱**：高 Star ≠ 安全（26.1% 含漏洞，5.2% 疑似恶意）
3. **中文用户断层**：纯英文生态使用门槛高

**AI Skills Rank** 通过 **5 个维度的月度榜单**，帮助用户回答三个核心问题：

- 谁最火？
- 谁还在认真维护？
- 谁可以放心装？

---

## 五榜单体系

每月 1-5 号连续发布 5 份报告，覆盖 skill 评估的全生命周期：

| 日期 | 榜单 | Top | 核心问题 | 评分维度 |
|------|------|-----|---------|---------|
| 1 号 | Star 榜单 | 50 | 谁最火 | GitHub Star + 增速 |
| 2 号 | 活跃度榜单 | 30 | 谁还在维护 | commit + 贡献者 + push 新近度 |
| 3 号 | 安全分级榜单 | 30 | 谁可以放心装 | 6 维安全评估 |
| 4 号 | 中文友好榜单 | 30 | 中文用户看得懂吗 | 5 维中文友好度 |
| 5 号 | 国产创作榜单 | 20 | 中国开发者做了什么 | 5 维国产评估 |

---

## 评分模型

### Star 榜单

按 GitHub Star 数降序排列，辅助指标为近 30 天 Star 增速。与上月对比标注 NEW / 涨幅 / 跌出。

### 活跃度榜单（5 维加权）

| 维度 | 权重 | 说明 |
|------|------|------|
| 最近 30 天 commit 数 | 35% | 维护频率核心指标 |
| 最近 push 新近度 | 20% | 0 天=满分，90 天+=0 分 |
| 贡献者数量 | 20% | 社区参与度 |
| Issues + PR 总数 | 15% | 真实使用反馈量 |
| Star 增速 | 10% | 增长势头 |

维护状态：🟢 活跃（30 天内）/ 🟡 低频（30-90 天）/ 🔴 疑似停更（90 天+）

### 安全分级榜单（6 维加权）

| 维度 | 权重 | 说明 |
|------|------|------|
| 出品方可信度 | 25% | 官方 / 知名组织 / 个人 / 无名 |
| 可执行脚本风险 | 20% | 无脚本 / 有脚本无可疑 / 有外部请求 / 有高危函数 |
| SKILL.md 质量 | 15% | 触发条件 + 约束 + 示例 是否齐全 |
| 维护活跃度 | 15% | 最近 commit 距今天数 |
| 社区审查程度 | 15% | Star 数 + Issue/PR 总数 |
| 已知安全记录 | 10% | 是否在 ToxicSkills / ClawHavoc 恶意名单 |

安全等级：

| 等级 | 评分 | 建议 |
|------|------|------|
| S 级 | 85-100 | 闭眼装，官方或等效可信 |
| A 级 | 70-84 | 放心装，高可信 |
| B 级 | 55-69 | 看一眼再装，中等可信 |
| C 级 | 40-54 | 需仔细审查，低可信 |
| D 级 | 0-39 | 不建议装，高风险 |

### 中文友好榜单（5 维加权）

| 维度 | 权重 | 说明 |
|------|------|------|
| 中文文档完整度 | 30% | 中文 README + SKILL.md + 教程 |
| 国内社区讨论度 | 25% | 掘金 / 知乎 / CSDN / 公众号 / V2EX |
| 中文维护者 | 15% | 维护者是否有中文社交账号 |
| 国内可用性 | 20% | 是否依赖被墙服务 |
| 中文生态适配 | 10% | 是否支持国产模型 / 平台 |

等级：优(80+) / 良(60+) / 中(40+) / 差(20+) / 极差(<20)

### 国产创作榜单（5 维加权）

**国产识别标准**（满足任一）：
1. GitHub profile 显示所在地为中国
2. GitHub profile name 为中文名
3. README 含中文且维护者有中文社交账号
4. 仓库归属中国公司 / 组织
5. README 明确标注"中文开发者作品"

| 维度 | 权重 | 说明 |
|------|------|------|
| 综合热度 | 25% | Star + Fork + Watch |
| 技术创新度 | 25% | 是否解决中文 / 国产生态独特痛点 |
| 维护活跃度 | 20% | 最近 commit 频率 |
| 国内影响力 | 20% | 国内平台讨论度 |
| 文档与生态 | 10% | 中文文档完整度 |

等级：明星项目(80+) / 优秀项目(60+) / 潜力项目(40+) / 早期项目(20+) / 待观察(<20)

---

## 数据来源

| 数据源 | 用途 |
|--------|------|
| GitHub REST API | 基础数据（Star / commit / 贡献者 / Issue） |
| GitHub Topics | 仓库发现（claude-code-skills / openclaw-skills / agent-skills） |
| OSSInsight | 交叉验证 |
| 掘金 / 知乎 / CSDN / V2EX | 中文讨论度 |
| OWASP Agentic Skills Top 10 | 安全标准参考 |
| NVIDIA SkillSpector | 安全扫描参考（26.1% 含漏洞，5.2% 疑似恶意） |
| Snyk AI Skills Security Audit | 已知漏洞记录 |

---

## 项目结构

```
ai-skills-rank/
├── README.md                    # 项目介绍（本文件）
├── docs/
│   ├── PROJECT_PLAN.md          # 项目计划书
│   ├── SCORING_MODELS.md        # 评分模型详解
│   └── SECURITY_GUIDE.md        # 安全科普文档
├── scripts/                     # 采集与评分脚本
│   ├── collect_star.py
│   ├── collect_activity.py
│   ├── collect_security.py
│   ├── collect_cn_friendly.py
│   ├── collect_cn_made.py
│   ├── scoring.py
│   └── generate_report.py
├── reports/                     # 月度报告（按年月归档）
│   └── 2026-07/
├── templates/                   # HTML 报告模板
├── data/                        # 历史数据
├── .github/workflows/           # GitHub Actions 自动化
└── LICENSE
```

---

## 使用方法

### 查看最新榜单

访问 GitHub Pages 站点（部署后更新链接），或直接浏览 `reports/` 目录下的最新月度报告。

### 本地运行

```bash
# 克隆仓库
git clone https://github.com/your-username/ai-skills-rank.git
cd ai-skills-rank

# 安装依赖
pip install -r requirements.txt

# 运行采集脚本（需要 GitHub Token，可选）
export GITHUB_TOKEN=your_token_here
python scripts/collect_star.py

# 生成报告
python scripts/generate_report.py
```

### 自动化运行

项目已配置 GitHub Actions，每月 1-5 号自动执行采集和报告生成：

- 1 号 10:00 UTC — Star 榜单
- 2 号 10:00 UTC — 活跃度榜单
- 3 号 10:00 UTC — 安全分级榜单
- 4 号 10:00 UTC — 中文友好榜单
- 5 号 10:00 UTC — 国产创作榜单

---

## 安全声明

- 安全评估基于公开信息，**无法替代专业安全审计**
- 评分仅供参考，**不构成安全建议**
- "无已知漏洞"**不等于**"绝对安全"
- 安装任何 skill 前，建议先 code review 再启用

详细安全科普请阅读 [SECURITY_GUIDE.md](./docs/SECURITY_GUIDE.md)

---

## 贡献指南

欢迎通过以下方式贡献：

1. **提交新 skill**：发现遗漏的 skill 仓库，通过 Issue 提交
2. **报告数据错误**：发现评分有误，通过 Issue 反馈
3. **改进评分模型**：通过 PR 提出评分维度优化建议
4. **翻译文档**：帮助翻译为其他语言
5. **分享榜单**：在社区分享月度报告

### 贡献流程

```bash
# Fork 仓库
# 创建分支
git checkout -b feature/new-skill-submission

# 提交更改
git commit -m "Add: new skill recommendation"

# 推送并创建 PR
git push origin feature/new-skill-submission
```

---

## 路线图

- [x] **M0** — 五榜单体系和评分模型确定
- [x] **M0** — WorkBuddy 自动化任务配置
- [ ] **M1** — MVP 上线（采集脚本 + GitHub Actions + Pages）
- [ ] **M2** — 集成 SkillSpector + 历史趋势图 + 搜索筛选
- [ ] **M3** — 社区运营 + 用户提交机制
- [ ] **M4** — 企业版 + API 开放

---

## 技术栈

- **数据采集**：Python 3.11+ / GitHub REST API
- **评分引擎**：Python
- **报告生成**：HTML + Chart.js
- **自动化**：GitHub Actions
- **部署**：GitHub Pages

---

## 开源协议

- 项目代码：[MIT License](./LICENSE)
- 报告数据：CC BY-SA 4.0
- 安全科普文档：CC BY-SA 4.0

---

## 致谢

- [OWASP Foundation](https://owasp.org/) — Agentic Skills Top 10 安全标准
- [NVIDIA](https://github.com/NVIDIA/SkillSpector) — SkillSpector 安全扫描器
- [Snyk](https://snyk.io/) — AI Skills 安全审计
- [Agent-Leaderboard](https://github.com/jaychempan/Agent-Leaderboard) — Star 排名参考
- 所有 AI Agent Skills 的开发者和维护者

---

## 联系方式

- **GitHub Issues**：[提交问题或建议](https://github.com/silenceite/ai-skills-rank/issues)
- **邮箱**：jien-2009@163.com

---

*AI Skills Rank · 让每一个 AI Agent Skill 都被看见、被评估、被信任*
# ai-skills-rank
AI Agent Skills 多维评估榜单 — 不只看 Star，更看活跃度、安全性和中文友好度

