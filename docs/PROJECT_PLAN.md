# AI Skills Rank — 项目计划书

> **AI Agent Skills 多维评估榜单平台**
>
> 版本：v1.0 · 日期：2026-06-19 · 状态：规划中

---

## 一、项目概述

### 1.1 项目名称

**AI Skills Rank**（aiskillsrank.com）

### 1.2 一句话定位

AI Agent Skills 的"大众点评"——不只看 Star，更看活跃度、安全性和中文友好度。

### 1.3 项目背景

2026 年 AI Agent Skills 生态爆发式增长，GitHub 上相关仓库已超过 1,400 个。但存在三个核心痛点：

1. **信息碎片化**：用户找不到"哪些 skill 值得装"，散落在各种 awesome-list 和博客文章中
2. **Star 陷阱**：高 Star 不等于安全（NVIDIA 研究显示 26.1% 的 skill 含漏洞，5.2% 疑似恶意）
3. **中文用户断层**：中文用户面对纯英文生态，使用门槛高，国产创作者缺乏曝光渠道

现有方案（如 Agent-Leaderboard）仅按 Star 单一维度排名，无法满足用户"能不能放心装"的真实决策需求。

### 1.4 项目目标

构建一个多维度、持续更新的 AI Agent Skills 评估榜单平台，帮助用户回答三个核心问题：

- **谁最火？**（热度维度）
- **谁还在认真维护？**（活跃度维度）
- **谁可以放心装？**（安全维度）

同时服务中文用户群体，降低使用门槛，推广国产优秀创作。

---

## 二、五榜单体系

### 2.1 榜单总览

| 榜单 | 更新频率 | Top 数 | 排名维度 | 核心问题 | 输出 |
|------|---------|--------|---------|---------|------|
| Star 榜单 | 每月 1 号 | 50 | GitHub Star + 增速 | 谁最火 | HTML 报告 |
| 活跃度榜单 | 每月 2 号 | 30 | commit + 贡献者 + push 新近度 | 谁还在维护 | HTML 报告 |
| 安全分级榜单 | 每月 3 号 | 30 | 6 维安全评估 | 谁可以放心装 | HTML 报告 |
| 中文友好榜单 | 每月 4 号 | 30 | 5 维中文友好度 | 中文用户看得懂吗 | HTML 报告 |
| 国产创作榜单 | 每月 5 号 | 20 | 5 维国产评估 | 中国开发者做了什么 | HTML 报告 |

### 2.2 各榜单评分模型

#### 榜单 1：Star 榜单（热度维度）

- **排名依据**：GitHub Star 数（降序）
- **辅助指标**：近 30 天 Star 增速
- **数据来源**：GitHub API、GitHub Topics、OSSInsight
- **对比维度**：与上月对比（NEW / 涨幅 / 跌出）

#### 榜单 2：活跃度榜单（维护维度）

| 维度 | 权重 | 说明 |
|------|------|------|
| 最近 30 天 commit 数 | 35% | 维护频率核心指标 |
| 最近 push 新近度 | 20% | 0 天=100 分，90 天+=0 分 |
| 贡献者数量 | 20% | 社区参与度 |
| Issues + PR 总数 | 15% | 真实使用反馈量 |
| Star 增速 | 10% | 增长势头 |

维护状态标签：🟢 活跃（30 天内）/ 🟡 低频（30-90 天）/ 🔴 疑似停更（90 天+）

#### 榜单 3：安全分级榜单（安全维度）

| 维度 | 权重 | 说明 |
|------|------|------|
| 出品方可信度 | 25% | 官方/知名组织/个人/无名 |
| 可执行脚本风险 | 20% | 无脚本/有脚本无可疑/有外部请求/有高危函数 |
| SKILL.md 质量 | 15% | 触发条件+约束+示例 是否齐全 |
| 维护活跃度 | 15% | 最近 commit 距今天数 |
| 社区审查程度 | 15% | Star 数 + Issue/PR 总数 |
| 已知安全记录 | 10% | 是否在 ToxicSkills/ClawHavoc 恶意名单 |

安全等级：S 级(85+,闭眼装) / A 级(70+,放心装) / B 级(55+,看一眼) / C 级(40+,需审查) / D 级(<40,不建议装)

#### 榜单 4：中文友好榜单（中文用户体验维度）

| 维度 | 权重 | 说明 |
|------|------|------|
| 中文文档完整度 | 30% | 中文 README + SKILL.md + 教程 |
| 国内社区讨论度 | 25% | 掘金/知乎/CSDN/公众号/V2EX |
| 中文维护者 | 15% | 维护者是否有中文社交账号 |
| 国内可用性 | 20% | 是否依赖被墙服务 |
| 中文生态适配 | 10% | 是否支持国产模型/平台 |

等级：优(80+) / 良(60+) / 中(40+) / 差(20+) / 极差(<20)

#### 榜单 5：国产创作榜单（中国开发者生态维度）

**国产识别标准**（满足任一）：
1. GitHub profile 显示所在地为中国
2. GitHub profile name 为中文名
3. README 含中文且维护者有中文社交账号
4. 仓库归属中国公司/组织
5. README 明确标注"中文开发者作品"

**排除标准**：仅因仓库名含拼音、fork 无实质改进、自动翻译文档

| 维度 | 权重 | 说明 |
|------|------|------|
| 综合热度 | 25% | Star + Fork + Watch |
| 技术创新度 | 25% | 是否解决中文/国产生态独特痛点 |
| 维护活跃度 | 20% | 最近 commit 频率 |
| 国内影响力 | 20% | 国内平台讨论度 |
| 文档与生态 | 10% | 中文文档完整度 |

等级：明星项目(80+) / 优秀项目(60+) / 潜力项目(40+) / 早期项目(20+) / 待观察(<20)

### 2.3 交叉价值

五个榜单组合形成 skill 的"全景画像"：

| 组合特征 | 判断 | 建议 |
|---------|------|------|
| 高 Star + 高活跃 + S 级安全 + 优级中文 + 国产 | 六边形战士 | 必装 |
| 高 Star + 低活跃 + D 级安全 | 曾经辉煌但危险 | 避坑 |
| 低 Star + 高活跃 + A 级安全 + 国产 | 潜力新星 | 关注 |
| 高 Star + 高活跃 + B 级安全 + 差级中文 | 好用但门槛高 | 需中文社区贡献 |

---

## 三、技术方案

### 3.1 技术架构（三阶段）

#### 第一阶段（MVP，1-2 周）

```
数据采集层          数据处理层          展示层
┌──────────┐      ┌──────────┐      ┌──────────┐
│ Python   │      │ Python   │      │ HTML +   │
│ 采集脚本  │ ──→  │ 评分引擎  │ ──→  │ Chart.js │
│ GitHub   │      │ 归一化    │      │ 静态页面  │
│ API      │      │ 加权计算  │      │          │
└──────────┘      └──────────┘      └──────────┘
     ↑                                    │
     │              GitHub Actions         │
     └──────── 每月 1-5 号定时执行 ────────┘
                    自动部署到
                 GitHub Pages
```

- **数据采集**：Python + GitHub REST API（公开端点，免费额度足够）
- **评分引擎**：Python 脚本，归一化 + 加权计算
- **展示**：纯 HTML + Chart.js，无需后端
- **部署**：GitHub Pages 免费托管
- **自动化**：GitHub Actions 定时执行

#### 第二阶段（流量增长期，1-2 个月）

- 加入 SkillSpector 安全扫描集成
- 加入历史趋势图（Star 走势、活跃度变化）
- 加入搜索和筛选功能
- 优化为 Vue/React 单页应用

#### 第三阶段（生态化，3-6 个月）

- 用户提交/投票机制
- 企业版（私有部署/定制扫描/合规报告）
- API 开放（供第三方集成）
- 多语言支持

### 3.2 数据采集策略

| 数据源 | 采集方式 | 频率 | 用途 |
|--------|---------|------|------|
| GitHub API | REST API（/repos, /commits, /contributors, /issues） | 每月 | 基础数据 |
| GitHub Topics | WebFetch + API | 每月 | 仓库发现 |
| GitHub Trending | WebFetch | 每月 | 新增仓库发现 |
| OSSInsight | WebFetch | 每月 | 交叉验证 |
| 掘金/知乎/CSDN | WebSearch | 每月 | 中文讨论度 |
| OWASP/Snyk/NVIDIA | WebSearch + WebFetch | 每月 | 安全记录 |

### 3.3 目录结构

```
ai-skills-rank/
├── README.md                    # 项目介绍
├── docs/                        # 文档
│   ├── PROJECT_PLAN.md          # 项目计划书
│   ├── SCORING_MODELS.md        # 评分模型详解
│   └── SECURITY_GUIDE.md        # 安全科普文档
├── scripts/                     # 采集与评分脚本
│   ├── collect_star.py          # Star 榜单采集
│   ├── collect_activity.py      # 活跃度榜单采集
│   ├── collect_security.py      # 安全榜单采集
│   ├── collect_cn_friendly.py   # 中文友好榜单采集
│   ├── collect_cn_made.py       # 国产创作榜单采集
│   ├── scoring.py               # 评分引擎
│   └── generate_report.py       # HTML 报告生成
├── reports/                     # 生成的报告
│   ├── 2026-07/
│   │   ├── top50-ai-skills-2026-07.html
│   │   ├── active-ai-skills-2026-07.html
│   │   ├── secure-ai-skills-2026-07.html
│   │   ├── cn-friendly-skills-2026-07.html
│   │   └── cn-made-skills-2026-07.html
│   └── 2026-08/
│       └── ...
├── templates/                   # HTML 报告模板
│   ├── star_template.html
│   ├── activity_template.html
│   ├── security_template.html
│   ├── cn_friendly_template.html
│   └── cn_made_template.html
├── data/                        # 历史数据（JSON）
│   ├── repos_cache.json         # 仓库信息缓存
│   └── history/                 # 历史快照
├── .github/
│   └── workflows/
│       ├── star-ranking.yml         # 每月1号
│       ├── activity-ranking.yml     # 每月2号
│       ├── security-ranking.yml     # 每月3号
│       ├── cn-friendly-ranking.yml  # 每月4号
│       └── cn-made-ranking.yml      # 每月5号
├── docs/                        # GitHub Pages 内容
│   └── index.html               # 榜单首页
└── LICENSE                      # 开源协议
```

---

## 四、里程碑计划

### M0：项目启动（第 0 周）

- [x] 确定五榜单体系和评分模型
- [x] 创建 WorkBuddy 自动化任务（月度五连发）
- [ ] 创建 GitHub 仓库
- [ ] 编写 README 和项目计划书

### M1：MVP 上线（第 1-2 周）

- [ ] 搭建项目目录结构
- [ ] 实现 5 个采集脚本（Python）
- [ ] 实现评分引擎
- [ ] 实现 HTML 报告生成
- [ ] 配置 GitHub Actions 自动化
- [ ] 部署到 GitHub Pages
- [ ] 首月五榜单报告上线

### M2：功能完善（第 3-6 周）

- [ ] 集成 SkillSpector 安全扫描
- [ ] 加入历史趋势图
- [ ] 加入搜索和筛选
- [ ] 优化移动端体验
- [ ] 加入 skill 提交入口

### M3：社区运营（第 7-12 周）

- [ ] 发布到掘金/知乎/V2EX 等社区
- [ ] 建立用户反馈渠道
- [ ] 招募贡献者
- [ ] 推出中文安全科普系列内容
- [ ] 月度榜单推送到公众号

### M4：商业化探索（第 13-24 周）

- [ ] 企业版需求调研
- [ ] API 开放
- [ ] 定制扫描服务
- [ ] 合规报告生成

---

## 五、风险与应对

| 风险 | 概率 | 影响 | 应对策略 |
|------|------|------|---------|
| Agent-Leaderboard 跟进多维评分 | 高 | 中 | 护城河在安全分级+中文社区，短期无法复制 |
| GitHub API 限流 | 中 | 高 | 合理使用缓存，控制请求频率，申请提升额度 |
| 数据采集偏差 | 中 | 中 | 多源交叉验证，标注数据来源和采集时间 |
| 安全评估误判 | 中 | 高 | 明确免责声明，标注"仅供参考，非安全建议" |
| 维护成本过高 | 中 | 中 | 先用 WorkBuddy 自动化跑，验证模式后再投入开发 |
| 中文社区冷启动 | 高 | 中 | 先在掘金/知乎发科普文章引流，再做社区 |

---

## 六、团队与资源

### 6.1 当前阶段

- **执行方式**：WorkBuddy 自动化任务（已配置 5 个）
- **人工投入**：每月约 2-4 小时（审查报告 + 社区运营）
- **成本**：零（GitHub Pages + Actions 免费额度）

### 6.2 扩展阶段需求

- Python 开发（采集脚本维护）：2-4 小时/周
- 前端开发（页面优化）：2-4 小时/周
- 内容运营（社区推广）：2-4 小时/周

---

## 七、成功指标

| 指标 | M1 目标 | M3 目标 | M6 目标 |
|------|---------|---------|---------|
| GitHub Star | 100+ | 1,000+ | 5,000+ |
| 月度访问量 | 500+ | 5,000+ | 20,000+ |
| 榜单收录 skill 数 | 100+ | 300+ | 500+ |
| 社区贡献者 | 1 | 5+ | 20+ |
| 公众号/知乎粉丝 | - | 500+ | 3,000+ |

---

## 八、附录

### 8.1 数据来源

- GitHub REST API（公开端点）
- GitHub Topics（claude-code-skills / openclaw-skills / agent-skills）
- OSSInsight（trending AI）
- 掘金 / 知乎 / CSDN / V2EX
- OWASP Agentic Skills Top 10
- NVIDIA SkillSpector
- Snyk AI Skills Security Audit

### 8.2 参考资料

- OWASP Foundation, "Agentic Skills Top 10 v0.5", 2026-06
- Liu et al., "Agent Skills in the Wild", 2026
- NVIDIA, "SkillSpector v2.0.0", 2026-06
- Snyk, "AI Agent Skills Security Audit", 2026-02
- Microsoft Security Blog, "When prompts become shells", 2026-05

### 8.3 开源协议

- 项目代码：MIT License
- 报告数据：CC BY-SA 4.0
- 安全科普文档：CC BY-SA 4.0

---

*AI Skills Rank · 让每一个 AI Agent Skill 都被看见、被评估、被信任*
