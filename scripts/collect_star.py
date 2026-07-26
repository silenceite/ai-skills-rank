#!/usr/bin/env python3
"""
AI Skills Rank - Star Ranking Collector (增强版 v2.0)
采集 GitHub AI Agent Skills 仓库的 Star 数据，生成 Top 50 榜单 HTML 报告。

相比 v1.0 的改进：
1. 环比对比（NEW / 跌出 / 涨幅 Top 5）从「上月报告 HTML」自动解析，不再依赖硬编码数据。
2. 数据缓存 data/cache/ 减少 GitHub API 调用（避免限流）。
3. 数据异常校验：Star 为 0 或骤降 >50% 时标记告警，不直接污染排名。
4. 输出增强版 HTML（对比面板 + 安全提示 + 变化标记），与自动化流程闭环。
"""

import argparse
import hashlib
import json
import os
import re
import sys
import time
import urllib.request
import urllib.error
from datetime import datetime
from html import escape
from pathlib import Path

GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN") or os.environ.get("COLLECTOR_TOKEN", "")

TOPICS = ["claude-code-skills", "openclaw-skills", "agent-skills"]
MIN_STARS = 50
MAX_REPOS = 500
CACHE_DIR = Path("data/cache")
CACHE_TTL = 24 * 3600  # 缓存有效期（秒）


# ───────────────────────── 缓存 ─────────────────────────
def _cache_path(url: str) -> Path:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    key = hashlib.md5(url.encode("utf-8")).hexdigest()
    return CACHE_DIR / f"{key}.json"


def _cache_get(url: str):
    p = _cache_path(url)
    if not p.exists():
        return None
    try:
        if time.time() - p.stat().st_mtime > CACHE_TTL:
            return None
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return None


def _cache_set(url: str, data) -> None:
    try:
        _cache_path(url).write_text(json.dumps(data), encoding="utf-8")
    except Exception:
        pass


# ───────────────────────── API ─────────────────────────
def github_api(url, params=None, use_cache=True):
    """调用 GitHub API（带缓存与限流重试）"""
    if params:
        query = "&".join(f"{k}={v}" for k, v in params.items())
        url = f"{url}?{query}"

    if use_cache:
        cached = _cache_get(url)
        if cached is not None:
            return cached, "cache"

    req = urllib.request.Request(url)
    req.add_header("Accept", "application/vnd.github+json")
    req.add_header("User-Agent", "ai-skills-rank")
    if GITHUB_TOKEN:
        req.add_header("Authorization", f"Bearer {GITHUB_TOKEN}")

    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            remaining = resp.headers.get("X-RateLimit-Remaining", "?")
            data = json.loads(resp.read().decode())
            if use_cache:
                _cache_set(url, data)
            return data, remaining
    except urllib.error.HTTPError as e:
        if e.code == 403:
            print(f"  [WARN] Rate limited. Waiting 10s...", file=sys.stderr)
            time.sleep(10)
            return github_api(url, params, use_cache)
        print(f"  [ERROR] HTTP {e.code}: {e.reason}", file=sys.stderr)
        return None, "0"
    except Exception as e:
        print(f"  [ERROR] {e}", file=sys.stderr)
        return None, "0"


def search_repos_by_topic(topic, per_page=100, max_pages=5, use_cache=True):
    """按 topic 搜索仓库"""
    repos = []
    for page in range(1, max_pages + 1):
        url = "https://api.github.com/search/repositories"
        params = {
            "q": f"topic:{topic}",
            "sort": "stars",
            "order": "desc",
            "per_page": str(per_page),
            "page": str(page),
        }
        data, remaining = github_api(url, params, use_cache)
        if not data:
            break

        items = data.get("items", [])
        if not items:
            break

        for item in items:
            if item.get("stargazers_count", 0) >= MIN_STARS:
                repos.append({
                    "full_name": item["full_name"],
                    "name": item["name"],
                    "owner": item["owner"]["login"],
                    "stars": item["stargazers_count"],
                    "forks": item["forks_count"],
                    "description": item.get("description") or "",
                    "url": item["html_url"],
                    "language": item.get("language") or "",
                    "topics": item.get("topics", []),
                    "updated_at": item.get("updated_at", ""),
                    "pushed_at": item.get("pushed_at", ""),
                    "open_issues": item.get("open_issues_count", 0),
                    "license": (item.get("license") or {}).get("spdx_id", "Unknown"),
                })

        print(f"  [{topic}] Page {page}: {len(items)} repos (rate limit: {remaining})", file=sys.stderr)
        time.sleep(1)

    return repos


def deduplicate(repos):
    """去重（同仓库保留最高 Star）"""
    seen = {}
    for r in repos:
        name = r["full_name"]
        if name not in seen or r["stars"] > seen[name]["stars"]:
            seen[name] = r
    return list(seen.values())


# ───────────────────────── 平台 / 安全分级 ─────────────────────────
def classify_platform(repo):
    """判断平台归属"""
    topics = set(repo.get("topics", []))
    name = (repo.get("full_name", "") + repo.get("description", "")).lower()

    is_claude = "claude" in topics or "claude" in name
    is_openclaw = "openclaw" in topics or "openclaw" in name
    is_cursor = "cursor" in topics or "cursor" in name
    is_codex = "codex" in topics or "codex" in name
    is_gemini = "gemini" in topics or "gemini" in name

    platforms = []
    if is_claude: platforms.append("Claude")
    if is_openclaw: platforms.append("OpenClaw")
    if is_cursor: platforms.append("Cursor")
    if is_codex: platforms.append("Codex")
    if is_gemini: platforms.append("Gemini")

    if len(platforms) >= 3:
        return "跨平台"
    elif len(platforms) == 1:
        return platforms[0]
    elif len(platforms) == 0:
        return "通用"
    else:
        return "跨平台"


def security_level(repo):
    """快速安全分级（基于出品方 / Star / 描述营销话术的启发式评估）"""
    owner = repo.get("owner", "").lower()
    stars = repo.get("stars", 0)
    desc = repo.get("description", "").lower()

    official_orgs = ["anthropics", "openai", "vercel", "vercel-labs", "nvidia",
                     "microsoft", "google", "iflytek", "trailofbits", "remotion-dev"]
    known_orgs = ["composiohq", "k-dense-ai", "voltagent", "sickn33", "obra",
                  "hesreallyhim", "affaan-m", "shangrui"]

    if owner in official_orgs:
        return ("S", "闭眼装", "#0F6E56", "#E1F5EE")
    if owner in known_orgs or stars >= 10000:
        return ("A", "放心装", "#534AB7", "#EEEDFE")
    if stars >= 1000:
        return ("B", "看一眼", "#854F0B", "#FAEEDA")
    if "最强" in desc or "终极" in desc or "神器" in desc:
        return ("D", "不建议", "#A32D2D", "#FCEBEB")
    return ("C", "需审查", "#D85A30", "#FAECE7")


# ───────────────────────── 环比对比 ─────────────────────────
def prev_month_str(month: str) -> str:
    y, m = map(int, month.split("-"))
    m -= 1
    if m == 0:
        m = 12
        y -= 1
    return f"{y:04d}-{m:02d}"


def load_previous(prev_month: str):
    """从上月报告 HTML 解析 Top 50 的 仓库名→Star 映射。无文件返回 None。"""
    path = Path("reports") / prev_month / f"top50-ai-skills-{prev_month}.html"
    if not path.exists():
        return None
    try:
        html = path.read_text(encoding="utf-8")
    except Exception:
        return None
    pairs = re.findall(r'class="repo-name">([^<]+)</div>.*?class="stars">([\d,]+)', html, re.DOTALL)
    data = {}
    for name, stars in pairs:
        data[name.strip()] = int(stars.replace(",", ""))
    return data or None


# ───────────────────────── HTML 生成 ─────────────────────────
def generate_html(repos, month, prev_data=None, prev_month=None):
    """生成增强版 HTML 报告（含环比对比与安全提示）"""
    repos_sorted = sorted(repos, key=lambda x: x["stars"], reverse=True)[:50]
    now = datetime.now().strftime("%Y-%m-%d %H:%M")

    # 对比计算
    prev_names = set(prev_data.keys()) if prev_data else set()
    new_entries, growths = [], []
    for i, r in enumerate(repos_sorted, 1):
        name = r["full_name"]
        if prev_data and name not in prev_names:
            new_entries.append((i, name, r["stars"]))
        elif prev_data and name in prev_data:
            old = prev_data[name]
            if old > 0:
                growths.append((name, old, r["stars"], (r["stars"] - old) / old * 100))
    dropouts = []
    if prev_data:
        cur_names = {r["full_name"] for r in repos_sorted}
        for name, stars in prev_data.items():
            if name not in cur_names:
                dropouts.append((name, stars))
    growths.sort(key=lambda x: x[3], reverse=True)
    top_risers = growths[:5]

    platforms = {classify_platform(r) for r in repos_sorted}
    max_star = repos_sorted[0]["stars"] if repos_sorted else 0
    top10_sum = sum(r["stars"] for r in repos_sorted[:10])

    # 异常校验：Star 为 0 / 骤降 >50% 标记
    anomalies = []
    for r in repos_sorted:
        if prev_data and r["full_name"] in prev_data:
            old = prev_data[r["full_name"]]
            if old > 0 and r["stars"] <= old * 0.5:
                anomalies.append(r["full_name"])

    # 行渲染
    rows = []
    for i, r in enumerate(repos_sorted, 1):
        level, label, color, bg = security_level(r)
        platform = classify_platform(r)
        desc = escape(r.get("description", "暂无描述")[:140])
        if len(r.get("description", "")) > 140:
            desc += "..."

        top_class = ' class="top3"' if i <= 3 else ""
        new_badge = ' <span class="new-badge">NEW</span>' if (prev_data and r["full_name"] in [n[1] for n in new_entries]) else ""

        change_html = ""
        if prev_data and r["full_name"] in prev_data:
            old = prev_data[r["full_name"]]
            if old > 0:
                pct = (r["stars"] - old) / old * 100
                if pct > 0.1:
                    arrow = "↑" if pct > 0 else "↓"
                    change_html = f'<span class="change {"up" if pct > 0 else "down"}">{arrow}{abs(pct):.0f}%</span>'

        rows.append(f"""        <tr{top_class}>
          <td class="rank">{i}</td>
          <td><div class="repo-name">{escape(r['full_name'])}{new_badge}</div><div class="repo-desc">{desc}</div></td>
          <td class="stars">{r['stars']:,}{change_html}</td>
          <td><span class="badge" style="background:{bg};color:{color};">{level} · {label}</span></td>
          <td>{platform}</td>
        </tr>""")

    # 对比面板
    risers_html = "".join(
        f"""          <tr>
            <td>{escape(n)}</td>
            <td class="stars">{o:,} → {nw:,}</td>
            <td class="stars" style="color:#0F6E56;">↑ {pct:.1f}%</td>
          </tr>
"""
        for n, o, nw, pct in top_risers
    ) or '<tr><td colspan="3" style="color:#6b7280;">无</td></tr>'

    new_html = "".join(
        f'<span class="dropout-tag" style="background:#E1F5EE;color:#0F6E56;">{escape(n)} ({s:,} ⭐, #{rk})</span> '
        for rk, n, s in new_entries
    ) or "<span>无</span>"

    drop_html = "".join(
        f'<span class="dropout-tag">{escape(n)} ({s:,} ⭐)</span> '
        for n, s in dropouts
    ) or "<span>无</span>"

    has_compare = bool(prev_data)
    compare_section = f"""
  <h2>📊 月度变动对比 (vs {prev_month})</h2>
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
      <p style="margin-bottom:8px;">{new_html}</p>
      <h3 style="margin-top:16px;">📉 本月跌出 Top 50</h3>
      <p>{drop_html}</p>
    </div>
  </div>""" if has_compare else """
  <h2>📊 月度变动对比</h2>
  <div class="comp-card"><p style="color:#6b7280;">本月为首次生成（或上月报告缺失），暂无环比对比数据。</p></div>"""

    anomaly_html = ""
    if anomalies:
        anomaly_html = f"""
  <div class="security-warn" style="background:#FCEBEB;border-color:#A32D2D;">
    <strong>⚠️ 数据异常告警</strong><br>
    • 以下仓库 Star 较上月骤降超过 50%，可能是 API 瞬时失败或数据异常，请人工复核：{escape("、".join(anomalies))}
  </div>"""

    html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<meta name="description" content="GitHub Star 最高的 50 个 AI Agent Skill 排行榜，每月自动更新。数据来自 GitHub API，按 Star 数降序排列，标注安全等级、平台支持和月度变动。">
<meta property="og:title" content="AI Agent Skills Star 榜单 Top 50 — {month}">
<meta property="og:description" content="GitHub 上 Star 最高的 50 个 AI Agent Skill，按热度排名。每月 1 号自动更新。">
<meta property="og:type" content="website">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="AI Agent Skills Star 榜单 Top 50 — {month}">
<link rel="icon" type="image/svg+xml" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 32 32'><rect width='32' height='32' rx='6' fill='%23534AB7'/><text x='16' y='23' text-anchor='middle' font-size='16' font-weight='bold' fill='white' font-family='system-ui'>AS</text></svg>">
<title>GitHub Star 最高的 AI Agent Skills Top 50 — {month}</title>
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
  .change {{ display: inline-block; font-size: 11px; margin-left: 6px; font-weight: 600; }}
  .change.up {{ color: #0F6E56; }}
  .change.down {{ color: #A32D2D; }}
  .comp-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 16px; margin-bottom: 24px; }}
  @media (max-width: 768px) {{ .comp-grid {{ grid-template-columns: 1fr; }} }}
  .comp-card {{ background: #fff; border-radius: 10px; padding: 20px; border: 1px solid #e5e7eb; box-shadow: 0 1px 2px rgba(0,0,0,0.04); }}
  .comp-card h3 {{ font-size: 14px; font-weight: 600; color: #534AB7; margin-bottom: 12px; }}
  .comp-card table {{ box-shadow: none; border-radius: 0; }}
  .comp-card thead {{ background: #f5f3ff; }}
  .comp-card thead th {{ color: #534AB7; font-size: 12px; padding: 8px 12px; }}
  .comp-card tbody td {{ padding: 8px 12px; font-size: 12px; }}
  .dropout-tag {{ display: inline-block; font-size: 12px; padding: 2px 8px; border-radius: 4px; background: #FCEBEB; color: #A32D2D; margin: 2px 4px 2px 0; }}
  .security-warn {{ background: #FFF8E1; border: 1px solid #FFD54F; border-radius: 10px; padding: 20px; margin-bottom: 24px; font-size: 13px; line-height: 1.8; }}
  .security-warn strong {{ color: #854F0B; }}
  .footer {{ margin-top: 24px; padding: 20px; background: #fff; border-radius: 10px; border: 1px solid #e5e7eb; font-size: 12px; color: #6b7280; line-height: 1.9; box-shadow: 0 1px 2px rgba(0,0,0,0.04); }}
  .footer strong {{ color: #534AB7; }}
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
  <p class="subtitle">数据更新：{now} · 报告月份：{month} · 自动采集自 GitHub API{(" · 对比上月：" + prev_month) if has_compare else ""}</p>

  <div class="summary">
    <div class="stat-card"><div class="label">收录 Skill 数</div><div class="value">{len(repos_sorted)}</div></div>
    <div class="stat-card"><div class="label">最高 Star</div><div class="value">{max_star:,}</div></div>
    <div class="stat-card"><div class="label">覆盖平台数</div><div class="value">{len(platforms)}</div></div>
    <div class="stat-card"><div class="label">新增入榜</div><div class="value">{len(new_entries)}</div></div>
    <div class="stat-card"><div class="label">跌出 Top 50</div><div class="value">{len(dropouts)}</div></div>
    <div class="stat-card"><div class="label">Top 10 总 Star</div><div class="value">{top10_sum:,}</div></div>
  </div>

  {compare_section}
  {anomaly_html}

  <div class="security-warn">
    <strong>⚠️ 安全提示：安装 Skill 前三思</strong><br>
    • 根据 <strong>NVIDIA SkillSpector</strong> 2026 年扫描数据：<strong>26.1%</strong> 的 Agent Skills 包含安全漏洞，<strong>5.2%</strong> 疑似恶意代码（数据来源：<a href="https://developer.nvidia.com/blog/introducing-skillspector-agentic-ai-security/" style="color:#534AB7;">NVIDIA SkillSpector Blog, 2026</a>；该数据为行业整体研究，非本榜单逐库实测）<br>
    • 参考 <strong>OWASP Top 10 for Agentic Skills</strong> 安全框架，重点关注：指令注入、敏感数据泄露、权限提升、供应链投毒（来源：<a href="https://owasp.org/www-project-top-10-for-large-language-model-applications/" style="color:#534AB7;">OWASP LLM Top 10</a>）<br>
    • <span style="background:#E1F5EE;color:#0F6E56;padding:1px 6px;border-radius:3px;font-size:11px;font-weight:600;">S·闭眼装</span> = 官方出品（Anthropic/Microsoft/Trail of Bits），可信任<br>
    • <span style="background:#EEEDFE;color:#534AB7;padding:1px 6px;border-radius:3px;font-size:11px;font-weight:600;">A·放心装</span> = Star 10K+ 且运营 6 个月以上，高度可信<br>
    • <span style="background:#FAEEDA;color:#854F0B;padding:1px 6px;border-radius:3px;font-size:11px;font-weight:600;">B·看一眼</span> = 个人开发者或 Star&lt;5K，建议审查后安装<br>
    • <span style="background:#FCEBEB;color:#A32D2D;padding:1px 6px;border-radius:3px;font-size:11px;font-weight:600;">D·不建议</span> = 无 README / 营销话术过度，存在风险<br>
    • 安装前检查：SKILL.md 内容是否合理、是否有可疑脚本、仓库是否活跃维护
  </div>

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
    <p>• 安全等级为启发式评估（S=官方/A=高可信/B=中可信/C=需审查/D=高风险），<strong>非代码级漏洞扫描</strong>，仅供参考</p>
    <p>• 平台归属判断依据：仓库 Topics 和描述中的关键词匹配（Claude / OpenClaw / Cursor / Codex / Gemini）</p>
    {f'• 上月报告：<a href="../../reports/{prev_month}/top50-ai-skills-{prev_month}.html" style="color:#534AB7;">top50-ai-skills-{prev_month}.html</a>' if has_compare else '• 上月报告：缺失（首次生成或文件未提交）'}
    <p>• 生成时间：{now} · 采集脚本：collect_star.py v2.0（自动增强版）</p>
  </div>
</div>
</body>
</html>"""

    return html


def main():
    parser = argparse.ArgumentParser(description="AI Skills Star Ranking Collector (增强版)")
    parser.add_argument("--output", "-o", required=True, help="Output HTML file path")
    parser.add_argument("--month", "-m", default=None, help="Report month (YYYY-MM)")
    parser.add_argument("--no-cache", action="store_true", help="禁用缓存，强制刷新 GitHub API")
    args = parser.parse_args()

    if not args.month:
        args.month = datetime.now().strftime("%Y-%m")

    use_cache = not args.no_cache
    print(f"[Star Ranking] Starting collection for {args.month} (cache={'off' if args.no_cache else 'on'})...", file=sys.stderr)

    all_repos = []
    for topic in TOPICS:
        print(f"  Searching topic: {topic}", file=sys.stderr)
        repos = search_repos_by_topic(topic, use_cache=use_cache)
        all_repos.extend(repos)
        print(f"  Found {len(repos)} repos for topic: {topic}", file=sys.stderr)

    repos = deduplicate(all_repos)
    repos.sort(key=lambda x: x["stars"], reverse=True)
    repos = repos[:MAX_REPOS]

    print(f"[Star Ranking] Total unique repos: {len(repos)}", file=sys.stderr)
    print(f"[Star Ranking] Top 5: {[(r['full_name'], r['stars']) for r in repos[:5]]}", file=sys.stderr)

    prev_month = prev_month_str(args.month)
    prev_data = load_previous(prev_month)
    if prev_data:
        print(f"[Star Ranking] Loaded previous month ({prev_month}) data: {len(prev_data)} repos", file=sys.stderr)
    else:
        print(f"[Star Ranking] No previous month data found for {prev_month}", file=sys.stderr)

    html = generate_html(repos, args.month, prev_data, prev_month)

    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    with open(args.output, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"[Star Ranking] Report saved to: {args.output}", file=sys.stderr)
    print(f"[Star Ranking] Done. {len(repos[:50])} skills in report.", file=sys.stderr)


if __name__ == "__main__":
    main()
