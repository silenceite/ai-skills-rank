#!/usr/bin/env python3
"""Build enhanced Star ranking HTML with month-over-month comparison and security warnings."""

import json, os, sys
from datetime import datetime
from html import escape
from pathlib import Path

# ── Config ──
MONTH = "2026-07"
PREV_MONTH = "2026-06"
OUTPUT_PATH = f"reports/{MONTH}/top50-ai-skills-{MONTH}.html"
DOCS_COPY = f"docs/reports/{MONTH}/top50-ai-skills-{MONTH}.html"
NOW = datetime.now().strftime("%Y-%m-%d %H:%M")

# ── Current data (from API run) ──
current = [
    ("anthropics/skills", 157879, "Public repository for Agent Skills", "通用", "S","闭眼装","#E1F5EE","#0F6E56"),
    ("nexu-io/open-design", 74559, "The Vibe Design Workspace & open-source Claude Design alternative. Local-first desktop app.", "跨平台", "A","放心装","#EEEDFE","#534AB7"),
    ("DietrichGebert/ponytail", 72427, "Makes your AI agent think like the laziest senior dev. The best code is the code you never wrote.", "Claude", "A","放心装","#EEEDFE","#534AB7"),
    ("addyosmani/agent-skills", 68691, "Production-grade engineering skills for AI coding agents.", "Cursor", "A","放心装","#EEEDFE","#534AB7"),
    ("ComposioHQ/awesome-claude-skills", 66699, "A curated list of awesome Claude Skills, resources, and tools.", "跨平台", "A","放心装","#EEEDFE","#534AB7"),
    ("shanraisshan/claude-code-best-practice", 61898, "From vibe coding to agentic engineering - practice makes claude perfect", "Claude", "A","放心装","#EEEDFE","#534AB7"),
    ("VoltAgent/awesome-openclaw-skills", 50892, "5,400+ OpenClaw skills filtered and categorized from the official registry.", "OpenClaw", "A","放心装","#EEEDFE","#534AB7"),
    ("CherryHQ/cherry-studio", 48107, "AI productivity studio with smart chat, autonomous agents, and 300+ assistants.", "跨平台", "A","放心装","#EEEDFE","#534AB7"),
    ("hesreallyhim/awesome-claude-code", 47856, "A hand-picked collection of resources for Claude Code - skills, hooks, slash-commands.", "Claude", "A","放心装","#EEEDFE","#534AB7"),
    ("sickn33/antigravity-awesome-skills", 42272, "1,800+ agentic skills for Claude Code, Cursor, Codex CLI, Gemini CLI, Antigravity.", "跨平台", "A","放心装","#EEEDFE","#534AB7"),
    ("wshobson/agents", 37468, "Multi-harness agentic plugin marketplace for Claude Code, Codex, Cursor, Copilot, Gemini CLI.", "跨平台", "A","放心装","#EEEDFE","#534AB7"),
    ("github/awesome-copilot", 36135, "Community-contributed instructions, agents, skills for GitHub Copilot.", "通用", "A","放心装","#EEEDFE","#534AB7"),
    ("hesamsheikh/awesome-openclaw-usecases", 31463, "A community collection of OpenClaw use cases for making life easier.", "OpenClaw", "A","放心装","#EEEDFE","#534AB7"),
    ("K-Dense-AI/scientific-agent-skills", 30030, "Turn any AI agent into an AI Scientist. Used by 160,000+ scientists worldwide.", "跨平台", "A","放心装","#EEEDFE","#534AB7"),
    ("googleworkspace/cli", 29338, "Google Workspace CLI - one tool for Drive, Gmail, Calendar, Sheets, Docs, Chat, Admin.", "通用", "A","放心装","#EEEDFE","#534AB7"),
    ("VoltAgent/awesome-agent-skills", 27185, "1,000+ agent skills from official dev teams and community, multi-platform.", "跨平台", "A","放心装","#EEEDFE","#534AB7"),
    ("topoteretes/cognee", 26740, "Open-source AI memory platform for agents - persistent long-term memory across sessions.", "通用", "A","放心装","#EEEDFE","#534AB7"),
    ("OthmanAdi/planning-with-files", 24412, "Persistent file-based planning for AI coding agents - crash-proof markdown plans.", "跨平台", "A","放心装","#EEEDFE","#534AB7"),
    ("JimLiu/baoyu-skills", 23054, "暴鱼 Skills - Chinese agent skills collection for AI coding tools.", "通用", "A","放心装","#EEEDFE","#534AB7"),
    ("phuryn/pm-skills", 22295, "PM Skills Marketplace: 100+ agentic skills for product management.", "通用", "A","放心装","#EEEDFE","#534AB7"),
    ("agentskills/agentskills", 21810, "Specification and documentation for Agent Skills standard.", "通用", "A","放心装","#EEEDFE","#534AB7"),
    ("alirezarezvani/claude-skills", 19795, "337 Claude Code skills across 13 platforms: engineering, marketing, product, compliance.", "跨平台", "A","放心装","#EEEDFE","#534AB7"),
    ("teng-lin/notebooklm-py", 17126, "Unofficial Python API and agentic skill for Google NotebookLM.", "跨平台", "A","放心装","#EEEDFE","#534AB7"),
    ("kubesphere/kubesphere", 16992, "The container platform for Kubernetes multi-cloud, datacenter, and edge management.", "通用", "A","放心装","#EEEDFE","#534AB7"),
    ("eigent-ai/eigent", 14457, "Eigent: Open Source Cowork Desktop. Local & free alternative to Claude Cowork.", "Claude", "A","放心装","#EEEDFE","#534AB7"),
    ("NevaMind-AI/memU", 13971, "Personal memory for agents - fast retrieval, self-evolving skills, lower cost.", "OpenClaw", "A","放心装","#EEEDFE","#534AB7"),
    ("wanshuiyin/Auto-claude-code-research-in-sleep", 12959, "ARIS - Lightweight Markdown-only skills for autonomous ML research.", "跨平台", "A","放心装","#EEEDFE","#534AB7"),
    ("alibaba/zvec", 12740, "A lightweight, lightning-fast, in-process vector database.", "通用", "A","放心装","#EEEDFE","#534AB7"),
    ("aden-hive/hive", 10633, "Multi-Agent Harness for Production AI.", "Claude", "A","放心装","#EEEDFE","#534AB7"),
    ("microsoft/SkillOpt", 10529, "Text-space optimizer that trains reusable natural-language skills for frozen LLM agents.", "通用", "S","闭眼装","#E1F5EE","#0F6E56"),
    ("alibaba/open-code-review", 9874, "Open-source code review tool - hybrid architecture with deterministic pipelines + LLM.", "通用", "B","看一眼","#FAEEDA","#854F0B"),
    ("AgriciDaniel/claude-obsidian", 8594, "Self-organizing AI second brain for Obsidian + Claude Code.", "Claude", "B","看一眼","#FAEEDA","#854F0B"),
    ("xixu-me/xget", 8154, "Ultra-high-performance, secure, all-in-one acceleration engine for developer resources.", "通用", "B","看一眼","#FAEEDA","#854F0B"),
    ("nexu-io/html-anything", 7492, "The agentic HTML editor - 75 Skills x 9 Surfaces (magazine, deck, blog, docs).", "跨平台", "B","看一眼","#FAEEDA","#854F0B"),
    ("refly-ai/refly", 7418, "First open-source agent skills builder. Define skills by vibe workflow.", "跨平台", "B","看一眼","#FAEEDA","#854F0B"),
    ("htmlstreamofficial/preline", 6349, "Preline UI - open-source prebuilt UI components based on Tailwind CSS.", "通用", "B","看一眼","#FAEEDA","#854F0B"),
    ("jnMetaCode/superpowers-zh", 6326, "AI编程超能力中文增强版 - superpowers (116k+) 完整汉化 + 中国原创skills.", "跨平台", "B","看一眼","#FAEEDA","#854F0B"),
    ("ThinkInAIXYZ/deepchat", 6075, "DeepChat - A smart assistant connecting powerful AI to your personal world.", "跨平台", "B","看一眼","#FAEEDA","#854F0B"),
    ("ikaijua/Awesome-AITools", 6062, "Collection of AI-related utilities. 收藏AI相关的实用工具.", "跨平台", "B","看一眼","#FAEEDA","#854F0B"),
    ("trailofbits/skills", 5975, "Trail of Bits Claude Code skills for security research, vulnerability detection.", "Claude", "S","闭眼装","#E1F5EE","#0F6E56"),
    ("heilcheng/awesome-agent-skills", 5926, "Tutorials, Guides and Agent Skills Directories.", "跨平台", "B","看一眼","#FAEEDA","#854F0B"),
    ("Gen-Verse/OpenClaw-RL", 5538, "OpenClaw-RL: Train any agent simply by talking.", "OpenClaw", "B","看一眼","#FAEEDA","#854F0B"),
    ("antfu/skills", 5465, "Anthony Fu's curated collection of agent skills.", "通用", "B","看一眼","#FAEEDA","#854F0B"),
    ("breaking-brake/cc-wf-studio", 5299, "CC Workflow Studio for Claude Code.", "通用", "B","看一眼","#FAEEDA","#854F0B"),
    ("metalbear-co/mirrord", 5192, "Run any process as if it were a pod in your Kubernetes cluster.", "通用", "B","看一眼","#FAEEDA","#854F0B"),
    ("Agents365-ai/drawio-skill", 5007, "Generate draw.io diagrams from natural language - 6 presets, vision self-check.", "OpenClaw", "B","看一眼","#FAEEDA","#854F0B"),
    ("OpenSenseNova/SenseNova-Skills", 4652, "Modular SenseNova skills for building AI-powered office assistants.", "通用", "B","看一眼","#FAEEDA","#854F0B"),
    ("gosom/google-maps-scraper", 4636, "Scrape data from Google Maps - name, address, phone, website, rating, reviews.", "通用", "B","看一眼","#FAEEDA","#854F0B"),
    ("xianyu110/awesome-openclaw-tutorial", 4514, "从零开始玩转OpenClaw - 最全面的中文教程，涵盖安装、配置、实战案例.", "OpenClaw", "B","看一眼","#FAEEDA","#854F0B"),
    ("xixu-me/awesome-persona-distill-skills", 4513, "Agent Skills centered on people, relationships, commemorative scenes, methodology.", "通用", "B","看一眼","#FAEEDA","#854F0B"),
]

# ── Previous month data (June 2026) ──
prev = {
    "anthropics/skills": 152722, "nexu-io/open-design": 67725,
    "DietrichGebert/ponytail": 38983, "addyosmani/agent-skills": 63194,
    "ComposioHQ/awesome-claude-skills": 65183,
    "shanraisshan/claude-code-best-practice": 58332,
    "VoltAgent/awesome-openclaw-skills": 50381,
    "CherryHQ/cherry-studio": 47538, "hesreallyhim/awesome-claude-code": 46825,
    "sickn33/antigravity-awesome-skills": 41106, "wshobson/agents": 36958,
    "github/awesome-copilot": 35295, "hesamsheikh/awesome-openclaw-usecases": 31392,
    "K-Dense-AI/scientific-agent-skills": 28739, "googleworkspace/cli": 27154,
    "VoltAgent/awesome-agent-skills": 25840, "topoteretes/cognee": 17903,
    "OthmanAdi/planning-with-files": 23605, "JimLiu/baoyu-skills": 21980,
    "agentskills/agentskills": 20758, "phuryn/pm-skills": 19700,
    "alirezarezvani/claude-skills": 18525, "teng-lin/notebooklm-py": 16635,
    "kubesphere/kubesphere": 16974, "eigent-ai/eigent": 14329,
    "NevaMind-AI/memU": 13891, "wanshuiyin/Auto-claude-code-research-in-sleep": 12342,
    "alibaba/zvec": 11465, "aden-hive/hive": 10565,
    "microsoft/SkillOpt": 8335, "xixu-me/xget": 8144,
    "refly-ai/refly": 7381, "AgriciDaniel/claude-obsidian": 7126,
    "nexu-io/html-anything": 6998, "htmlstreamofficial/preline": 6341,
    "ikaijua/Awesome-AITools": 6030, "ThinkInAIXYZ/deepchat": 6027,
    "trailofbits/skills": 5775, "heilcheng/awesome-agent-skills": 5691,
    "jnMetaCode/superpowers-zh": 5612, "Gen-Verse/OpenClaw-RL": 5506,
    "antfu/skills": 5341, "metalbear-co/mirrord": 5142,
    "breaking-brake/cc-wf-studio": 5128, "OpenSenseNova/SenseNova-Skills": 4576,
    "xianyu110/awesome-openclaw-tutorial": 4491,
    "xixu-me/awesome-persona-distill-skills": 4442,
    "gosom/google-maps-scraper": 4410, "Agents365-ai/drawio-skill": 4135,
    "zebbern/claude-code-guide": 4315,
}

# ── Compute comparison ──
new_entries = []
dropouts = []
growths = []
prev_names = set(prev.keys())

for i, (name, stars, *_) in enumerate(current):
    if name not in prev_names:
        new_entries.append((i+1, name, stars))
    else:
        old_stars = prev[name]
        if old_stars > 0:
            pct = (stars - old_stars) / old_stars * 100
            growths.append((name, old_stars, stars, pct))

for name in prev_names:
    if name not in [c[0] for c in current]:
        dropouts.append((name, prev[name]))

growths.sort(key=lambda x: x[3], reverse=True)
top_risers = growths[:5]

# ── Platforms count ──
platforms = set(c[3] for c in current)
max_star = current[0][1]

# ── Build HTML ──
def build_row(rank, name, stars, desc, platform, level, label, bg, color, is_new=False, change_pct=None):
    top_class = ' class="top3"' if rank <= 3 else ""
    
    # NEW badge
    new_badge = ' <span class="new-badge">NEW</span>' if is_new else ""
    
    # Change indicator
    change_html = ""
    if change_pct is not None and change_pct > 0.1:
        arrow = "↑" if change_pct > 0 else "↓"
        change_html = f'<span class="change {"up" if change_pct > 0 else "down"}">{arrow}{abs(change_pct):.0f}%</span>'
    
    desc_short = escape(desc[:140])
    if len(desc) > 140:
        desc_short += "..."
    
    return f"""        <tr{top_class}>
          <td class="rank">{rank}</td>
          <td><div class="repo-name">{escape(name)}{new_badge}</div><div class="repo-desc">{desc_short}</div></td>
          <td class="stars">{stars:,}{change_html}</td>
          <td><span class="badge" style="background:{bg};color:{color};">{level} · {label}</span></td>
          <td>{platform}</td>
        </tr>"""

rows = []
for i, (name, stars, desc, platform, level, label, bg, color) in enumerate(current):
    rank = i + 1
    is_new = name in [n[1] for n in new_entries]
    change_pct = None
    if name in prev:
        old = prev[name]
        if old > 0:
            change_pct = (stars - old) / old * 100
    rows.append(build_row(rank, name, stars, desc, platform, level, label, bg, color, is_new, change_pct))

# ── Build risers section ──
risers_html = ""
for name, old, new, pct in top_risers:
    risers_html += f"""          <tr>
            <td>{escape(name)}</td>
            <td class="stars">{old:,} → {new:,}</td>
            <td class="stars" style="color:#0F6E56;">↑ {pct:.1f}%</td>
          </tr>
"""

# ── Build dropouts section ──
dropouts_html = ""
if dropouts:
    for name, stars in dropouts:
        dropouts_html += f'<span class="dropout-tag">{escape(name)} ({stars:,} ⭐)</span> '
else:
    dropouts_html = "<span>无</span>"

# ── New entries section ──
new_entries_html = ""
if new_entries:
    for rank, name, stars in new_entries:
        new_entries_html += f'<span class="dropout-tag">{escape(name)} ({stars:,} ⭐, #{rank})</span> '
else:
    new_entries_html = "<span>无</span>"

# ── HTML ──
html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<link rel="icon" type="image/svg+xml" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 32 32'><rect width='32' height='32' rx='6' fill='%23534AB7'/><text x='16' y='23' text-anchor='middle' font-size='16' font-weight='bold' fill='white' font-family='system-ui'>AS</text></svg>">
<title>GitHub AI Agent Skills Top 50 — {MONTH}</title>
<style>
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; background: #f8f9fa; color: #1a1a2e; line-height: 1.6; }}
  .container {{ max-width: 1200px; margin: 0 auto; padding: 32px 24px; }}
  h1 {{ font-size: 28px; font-weight: 700; margin-bottom: 6px; }}
  h2 {{ font-size: 18px; font-weight: 600; margin: 32px 0 16px; color: #534AB7; }}
  .subtitle {{ font-size: 14px; color: #6b7280; margin-bottom: 24px; }}
  .summary {{ display: flex; gap: 16px; margin-bottom: 24px; flex-wrap: wrap; }}
  .stat-card {{ background: #fff; border-radius: 10px; padding: 18px 24px; border: 1px solid #e5e7eb; flex: 1; min-width: 160px; box-shadow: 0 1px 2px rgba(0,0,0,0.04); }}
  .stat-card .label {{ font-size: 12px; color: #6b7280; margin-bottom: 4px; letter-spacing: 0.3px; }}
  .stat-card .value {{ font-size: 24px; font-weight: 700; color: #534AB7; }}
  
  /* Table */
  .table-wrapper {{ overflow-x: auto; }}
  table {{ width: 100%; border-collapse: collapse; background: #fff; border-radius: 12px; overflow: hidden; box-shadow: 0 1px 3px rgba(0,0,0,0.08); }}
  thead {{ background: #534AB7; }}
  thead th {{ color: #fff; font-size: 13px; font-weight: 600; padding: 14px 16px; text-align: left; }}
  thead th:first-child {{ width: 52px; text-align: center; }}
  thead th:nth-child(3) {{ width: 110px; text-align: right; }}
  tbody tr {{ border-bottom: 1px solid #f0f0f0; transition: background 0.15s; }}
  tbody tr:hover {{ background: #f5f3ff; }}
  tbody td {{ padding: 12px 16px; font-size: 13px; vertical-align: top; }}
  td.rank {{ text-align: center; font-weight: 700; color: #9ca3af; font-size: 15px; }}
  td.stars {{ text-align: right; font-weight: 700; color: #534AB7; white-space: nowrap; }}
  .repo-name {{ font-weight: 600; color: #1a1a2e; display: flex; align-items: center; gap: 8px; flex-wrap: wrap; }}
  .repo-desc {{ color: #6b7280; font-size: 12px; margin-top: 3px; line-height: 1.5; }}
  .badge {{ display: inline-block; font-size: 11px; padding: 2px 8px; border-radius: 4px; font-weight: 600; white-space: nowrap; }}
  .new-badge {{ display: inline-block; font-size: 10px; padding: 1px 6px; border-radius: 3px; font-weight: 700; background: #E1F5EE; color: #0F6E56; letter-spacing: 0.5px; }}
  .top3 {{ background: #faf9ff; }}
  .top3 td.rank {{ color: #534AB7; }}
  
  /* Change indicators */
  .change {{ display: inline-block; font-size: 11px; margin-left: 6px; font-weight: 600; }}
  .change.up {{ color: #0F6E56; }}
  .change.down {{ color: #A32D2D; }}
  
  /* Comparison panels */
  .comp-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 16px; margin-bottom: 24px; }}
  @media (max-width: 768px) {{ .comp-grid {{ grid-template-columns: 1fr; }} }}
  .comp-card {{ background: #fff; border-radius: 10px; padding: 20px; border: 1px solid #e5e7eb; box-shadow: 0 1px 2px rgba(0,0,0,0.04); }}
  .comp-card h3 {{ font-size: 14px; font-weight: 600; color: #534AB7; margin-bottom: 12px; }}
  .comp-card table {{ box-shadow: none; border-radius: 0; }}
  .comp-card thead {{ background: #f5f3ff; }}
  .comp-card thead th {{ color: #534AB7; font-size: 12px; padding: 8px 12px; }}
  .comp-card tbody td {{ padding: 8px 12px; font-size: 12px; }}
  
  /* Dropout tags */
  .dropout-tag {{ display: inline-block; font-size: 12px; padding: 2px 8px; border-radius: 4px; background: #FCEBEB; color: #A32D2D; margin: 2px 4px 2px 0; }}
  
  /* Security warning box */
  .security-warn {{ background: #FFF8E1; border: 1px solid #FFD54F; border-radius: 10px; padding: 20px; margin-bottom: 24px; font-size: 13px; line-height: 1.8; }}
  .security-warn strong {{ color: #854F0B; }}
  
  .footer {{ margin-top: 24px; padding: 20px; background: #fff; border-radius: 10px; border: 1px solid #e5e7eb; font-size: 12px; color: #6b7280; line-height: 1.9; box-shadow: 0 1px 2px rgba(0,0,0,0.04); }}
  .footer strong {{ color: #534AB7; }}
  
  /* Responsive */
  @media (max-width: 768px) {{
    .container {{ padding: 16px 12px; }}
    h1 {{ font-size: 22px; }}
    .summary {{ gap: 8px; }}
    .stat-card {{ min-width: 120px; padding: 12px 16px; }}
    .stat-card .value {{ font-size: 18px; }}
  }}
</style>
</head>
<body>
<div class="container">
  <h1>🚀 GitHub AI Agent Skills Star Top 50</h1>
  <p class="subtitle">数据更新：{NOW} · 报告月份：{MONTH} · 自动采集自 GitHub API · 对比上月：{PREV_MONTH}</p>

  <!-- Summary stats -->
  <div class="summary">
    <div class="stat-card"><div class="label">收录 Skill 数</div><div class="value">50</div></div>
    <div class="stat-card"><div class="label">最高 Star</div><div class="value">{max_star:,}</div></div>
    <div class="stat-card"><div class="label">覆盖平台数</div><div class="value">{len(platforms)}</div></div>
    <div class="stat-card"><div class="label">新增入榜</div><div class="value">{len(new_entries)}</div></div>
    <div class="stat-card"><div class="label">跌出 Top 50</div><div class="value">{len(dropouts)}</div></div>
    <div class="stat-card"><div class="label">Top 10 总 Star</div><div class="value">{sum(c[1] for c in current[:10]):,}</div></div>
  </div>

  <!-- Month-over-month comparison -->
  <h2>📊 月度变动对比 (vs {PREV_MONTH})</h2>
  <div class="comp-grid">
    <div class="comp-card">
      <h3>🔥 Star 增长最快 Top 5</h3>
      <table>
        <thead><tr><th>仓库</th><th>变动</th><th>涨幅</th></tr></thead>
        <tbody>{risers_html}        </tbody>
      </table>
    </div>
    <div class="comp-card">
      <h3>🆕 新入榜 Skill</h3>
      <p style="margin-bottom:8px;">{new_entries_html}</p>
      <h3 style="margin-top:16px;">📉 本月跌出 Top 50</h3>
      <p>{dropouts_html}</p>
    </div>
  </div>

  <!-- Security warning -->
  <div class="security-warn">
    <strong>⚠️ 安全提示：安装 Skill 前三思</strong><br>
    • 根据 <strong>NVIDIA SkillSpector</strong> 2026 年扫描数据：<strong>26.1%</strong> 的 Agent Skills 包含安全漏洞，<strong>5.2%</strong> 疑似恶意代码（数据来源：<a href="https://developer.nvidia.com/blog/introducing-skillspector-agentic-ai-security/" style="color:#534AB7;">NVIDIA SkillSpector Blog, 2026</a>）<br>
    • 参考 <strong>OWASP Top 10 for Agentic Skills</strong> 安全框架，重点关注：指令注入、敏感数据泄露、权限提升、供应链投毒（来源：<a href="https://owasp.org/www-project-top-10-for-large-language-model-applications/" style="color:#534AB7;">OWASP LLM Top 10</a>）<br>
    • <span style="background:#E1F5EE;color:#0F6E56;padding:1px 6px;border-radius:3px;font-size:11px;font-weight:600;">S·闭眼装</span> = 官方出品（Anthropic/Microsoft/Trail of Bits），可信任<br>
    • <span style="background:#EEEDFE;color:#534AB7;padding:1px 6px;border-radius:3px;font-size:11px;font-weight:600;">A·放心装</span> = Star 10K+ 且运营 6 个月以上，高度可信<br>
    • <span style="background:#FAEEDA;color:#854F0B;padding:1px 6px;border-radius:3px;font-size:11px;font-weight:600;">B·看一眼</span> = 个人开发者或 Star<5K，建议审查后安装<br>
    • <span style="background:#FCEBEB;color:#A32D2D;padding:1px 6px;border-radius:3px;font-size:11px;font-weight:600;">D·不建议</span> = 无 README / 营销话术过度，存在风险<br>
    • 安装前检查：SKILL.md 内容是否合理、是否有可疑脚本、仓库是否活跃维护
  </div>

  <!-- Main ranking table -->
  <h2>🏆 完整排名 (Top 50)</h2>
  <div class="table-wrapper">
  <table>
    <thead>
      <tr>
        <th>#</th>
        <th>仓库名称 / 核心功能</th>
        <th>Star</th>
        <th>安全等级</th>
        <th>平台</th>
      </tr>
    </thead>
    <tbody>
{chr(10).join(rows)}
    </tbody>
  </table>
  </div>

  <div class="footer">
    <p><strong>📋 数据来源说明</strong></p>
    <p>• 数据通过 <strong>GitHub Search API</strong> 自动采集，搜索 Topics: <code>claude-code-skills</code>, <code>openclaw-skills</code>, <code>agent-skills</code></p>
    <p>• 收录范围：含 SKILL.md 结构的技能包/插件/工具链仓库；排除通用 AI 项目（AutoGPT、LangChain、n8n 等）</p>
    <p>• 去重规则：同一仓库不同来源以最高 Star 数为准</p>
    <p>• 安全等级评估维度：出品方背景、Star 数量、维护周期、文档完整度、安装复杂度</p>
    <p>• 平台归属判断依据：仓库 Topics 和描述中的关键词匹配（Claude / OpenClaw / Cursor / Codex / Gemini）</p>
    <p>• 上月报告：<a href="../../reports/2026-06/top50-ai-skills-2026-06.html" style="color:#534AB7;">top50-ai-skills-{PREV_MONTH}.html</a></p>
    <p>• 生成时间：{NOW} · 采集脚本：collect_star.py + build_enhanced_report.py</p>
  </div>
</div>
</body>
</html>"""

# ── Write output ──
os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
    f.write(html)
print(f"[Enhanced Report] Saved to: {OUTPUT_PATH}")

# ── Copy to docs/ ──
os.makedirs(os.path.dirname(DOCS_COPY), exist_ok=True)
with open(DOCS_COPY, "w", encoding="utf-8") as f:
    f.write(html)
print(f"[Enhanced Report] Copied to: {DOCS_COPY}")

# ── Summary ──
print(f"\n[Summary] 2026-07 Top 50 Report")
print(f"  Total: 50 skills")
print(f"  Max Stars: {max_star:,} ({current[0][0]})")
print(f"  New entries: {len(new_entries)} ({', '.join(n[1] for n in new_entries)})")
print(f"  Dropouts: {len(dropouts)} ({', '.join(d[0] for d in dropouts)})")
print(f"  Top risers:")
for name, old, new, pct in top_risers:
    print(f"    {name}: {old:,} → {new:,} (+{pct:.1f}%)")
print(f"  Platforms: {', '.join(sorted(platforms))}")
