# AI Agent Skills Rank

> The "Yelp" for AI Agent Skills — look beyond stars: evaluate activity, security, and community trust.

> [中文](./README.md) | English

---

## What Is This?

The AI Agent Skills ecosystem exploded in 2026 — over 1,400+ skill repositories on GitHub. But users face three pain points:

1. **Fragmented information**: Hard to know which skills are worth installing.
2. **The star trap**: High stars ≠ safe (26.1% contain vulnerabilities, 5.2% suspected malicious).
3. **Chinese user gap**: Pure English ecosystem creates high barriers for Chinese-speaking developers.

**AI Agent Skills Rank** answers four core questions through **6 ranking dimensions**:

- Who's the most popular?
- Who's trending right now?
- Who's still actively maintained?
- Who can I trust to install?

---

## Six Rankings

Six reports published on the 1st-5th and 28th of each month, covering the full lifecycle of skill evaluation:

| Date | Ranking | Top | Core Question | Scoring Dimensions |
|------|---------|-----|---------------|-------------------|
| 1st | Star Ranking | 50 | Who's popular? | GitHub Stars + growth rate |
| 2nd | Activity Ranking | 30 | Who's maintained? | commits + contributors + push recency |
| 3rd | Security Ranking | 30 | Who's trustworthy? | 6-dimension security assessment |
| 4th | CN-Friendly Ranking | 30 | Chinese-user friendly? | 5-dimension Chinese accessibility |
| 5th | CN-Made Ranking | 20 | Chinese developers? | 5-dimension domestic evaluation |
| 28th | 🚀 Trending | 30 | Who's blowing up? | GitHub Trending monthly star increase |

---

## Scoring Models

### Star Ranking

Ranked by GitHub Stars (descending), with 30-day star growth as a secondary metric. Compared month-over-month with NEW / RISING / DROPPED labels.

### Activity Ranking (5-dimension weighted)

| Dimension | Weight | Description |
|-----------|--------|-------------|
| Recent 30-day commits | 35% | Core maintenance frequency metric |
| Last push recency | 20% | 0 days = 100, 90+ days = 0 |
| Contributor count | 20% | Community engagement |
| Issues + PRs total | 15% | Real user feedback volume |
| Star growth rate | 10% | Momentum |

Status: 🟢 Active (< 30 days) / 🟡 Low-frequency (30-90 days) / 🔴 Possibly abandoned (90+ days)

### Security Ranking (6-dimension weighted)

| Dimension | Weight | Description |
|-----------|--------|-------------|
| Publisher credibility | 25% | Official / known org / individual / unknown |
| Executable script risk | 20% | No scripts / scripts no suspicious / external requests / high-risk functions |
| SKILL.md quality | 15% | Trigger conditions + constraints + examples |
| Maintenance activity | 15% | Days since last commit |
| Community scrutiny | 15% | Stars + Issues/PRs count |
| Known security record | 10% | Presence in ToxicSkills / ClawHavoc blocklists |

Security ratings:

| Grade | Score | Recommendation |
|-------|-------|----------------|
| S | 85-100 | Install confidently — official or equivalent trust |
| A | 70-84 | Safe to install — high credibility |
| B | 55-69 | Review before installing — moderate credibility |
| C | 40-54 | Requires careful audit — low credibility |
| D | 0-39 | Not recommended — high risk |

### CN-Friendly Ranking (5-dimension weighted)

| Dimension | Weight | Description |
|-----------|--------|-------------|
| Chinese documentation | 30% | Chinese README + SKILL.md + tutorials |
| Domestic community buzz | 25% | Juejin / Zhihu / CSDN / WeChat / V2EX |
| Chinese maintainers | 15% | Maintainers with Chinese social accounts |
| Domestic accessibility | 20% | Dependent on blocked services? |
| Chinese ecosystem adaptation | 10% | Supports domestic models / platforms |

Grades: Excellent (80+) / Good (60+) / Fair (40+) / Poor (20+) / Very Poor (<20)

### CN-Made Ranking (5-dimension weighted)

**Made-in-China identification criteria** (meet any one):

1. GitHub profile location set to China
2. GitHub profile name in Chinese
3. README in Chinese + maintainer has Chinese social accounts
4. Repository owned by a Chinese company / organization
5. README explicitly states "by Chinese developer"

| Dimension | Weight | Description |
|-----------|--------|-------------|
| Overall popularity | 25% | Stars + Forks + Watchers |
| Technical innovation | 25% | Solving unique Chinese / domestic ecosystem pain points |
| Maintenance activity | 20% | Recent commit frequency |
| Domestic influence | 20% | Discussion volume on Chinese platforms |
| Documentation & ecosystem | 10% | Chinese documentation completeness |

Grades: Star Project (80+) / Excellent (60+) / Potential (40+) / Early Stage (20+) / Observe (<20)

---

## Data Sources

| Source | Purpose |
|--------|---------|
| GitHub REST API | Base data (Stars / commits / contributors / Issues) |
| GitHub Topics | Repository discovery (claude-code-skills / openclaw-skills / agent-skills) |
| OSSInsight | Cross-validation |
| Juejin / Zhihu / CSDN / V2EX | Chinese community discussion volume |
| OWASP Agentic Skills Top 10 | Security standard reference |
| NVIDIA SkillSpector | Security scanning reference (26.1% with vulnerabilities, 5.2% suspected malicious) |
| Snyk AI Skills Security Audit | Known vulnerability records |

---

## Project Structure

```
ai-skills-rank/
├── README.md                    # Project introduction (Chinese)
├── README_EN.md                 # Project introduction (English)
├── docs/
│   ├── index.html               # GitHub Pages homepage
│   ├── PROJECT_PLAN.md          # Project plan
│   ├── SECURITY_GUIDE.md        # Security guide
│   └── reports/                 # Synced reports for Pages
├── scripts/                     # Collection & scoring scripts
│   ├── collect_star.py
│   ├── collect_activity.py
│   ├── collect_security.py
│   ├── collect_cn_friendly.py
│   ├── collect_cn_made.py
│   ├── collect_trending.py      # Trending ranking (28th each month)
│   ├── scoring.py
│   └── generate_report.py
├── reports/                     # Monthly reports (archived by year-month)
├── templates/                   # HTML report templates
├── data/                        # Historical data
├── .github/workflows/           # GitHub Actions automation
└── LICENSE
```

---

## Usage

### View Latest Rankings

Visit the GitHub Pages site: `https://silenceite.github.io/ai-skills-rank/`

### Run Locally

```bash
# Clone the repository
git clone git@github.com:silenceite/ai-skills-rank.git
cd ai-skills-rank

# Install dependencies
pip install -r requirements.txt

# Run collector (GitHub Token optional)
export GITHUB_TOKEN=your_token_here
python scripts/collect_star.py

# Generate reports
python scripts/generate_report.py
```

### Automated Execution

The project is configured with 6 GitHub Actions workflows:

- 1st 10:00 UTC — Star Ranking
- 2nd 10:00 UTC — Activity Ranking
- 3rd 10:00 UTC — Security Ranking
- 4th 10:00 UTC — CN-Friendly Ranking
- 5th 10:00 UTC — CN-Made Ranking
- 28th 12:00 UTC — 🚀 Trending Ranking

---

## Security Disclaimer

- Security assessments are based on public information and **cannot replace professional security audits**.
- Scores are for reference only and **do not constitute security advice**.
- "No known vulnerabilities" **does not equal** "absolutely safe".
- Always review code before enabling any skill.

For detailed security guidance, see [SECURITY_GUIDE.md](./docs/SECURITY_GUIDE.md)

---

## Contributing

Contributions are welcome through:

1. **Submit new skills**: Found a missing skill repository? Submit via Issue.
2. **Report data errors**: Found scoring inaccuracies? Report via Issue.
3. **Improve scoring models**: Propose scoring dimension improvements via PR.
4. **Translate documentation**: Help translate to other languages.
5. **Share rankings**: Share monthly reports in your community.

### Contribution Workflow

```bash
# Fork the repository
# Create a branch
git checkout -b feature/new-skill-submission

# Commit changes
git commit -m "Add: new skill recommendation"

# Push and create PR
git push origin feature/new-skill-submission
```

---

## Roadmap

- [x] **M0** — Six-ranking system and scoring models defined
- [x] **M0** — WorkBuddy automation configured
- [ ] **M1** — MVP launch (collectors + GitHub Actions + Pages)
- [ ] **M2** — SkillSpector integration + trend charts + search/filter
- [ ] **M3** — Community growth + user submission mechanism
- [ ] **M4** — Enterprise edition + public API

---

## Tech Stack

- **Data collection**: Python 3.11+ / GitHub REST API
- **Scoring engine**: Python
- **Report generation**: HTML + Chart.js
- **Automation**: GitHub Actions
- **Deployment**: GitHub Pages

---

## License

- Project code: [MIT License](./LICENSE)
- Report data: CC BY-SA 4.0
- Security documentation: CC BY-SA 4.0

---

## Acknowledgments

- [OWASP Foundation](https://owasp.org/) — Agentic Skills Top 10 security standard
- [NVIDIA](https://github.com/NVIDIA/SkillSpector) — SkillSpector security scanner
- [Snyk](https://snyk.io/) — AI Skills security audit
- [Agent-Leaderboard](https://github.com/jaychempan/Agent-Leaderboard) — Star ranking reference
- All AI Agent Skills developers and maintainers

---

## Contact

- **GitHub Issues**: [Submit issues or suggestions](https://github.com/silenceite/ai-skills-rank/issues)
- **Email**: jien-2009@163.com

---

*AI Agent Skills Rank · Every AI Agent Skill deserves to be seen, evaluated, and trusted*
