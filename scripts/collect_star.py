#!/usr/bin/env python3
"""
AI Skills Rank - Star Ranking Collector
采集 GitHub AI Agent Skills 仓库的 Star 数据，生成 Top 50 榜单 HTML 报告。
"""

import argparse
import json
import os
import sys
import time
import urllib.request
import urllib.error
from datetime import datetime
from html import escape

GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN") or os.environ.get("COLLECTOR_TOKEN", "")

TOPICS = ["claude-code-skills", "openclaw-skills", "agent-skills"]
MIN_STARS = 50
MAX_REPOS = 500


def github_api(url, params=None):
    """调用 GitHub API"""
    if params:
        query = "&".join(f"{k}={v}" for k, v in params.items())
        url = f"{url}?{query}"

    req = urllib.request.Request(url)
    req.add_header("Accept", "application/vnd.github+json")
    req.add_header("User-Agent", "ai-skills-rank")
    if GITHUB_TOKEN:
        req.add_header("Authorization", f"Bearer {GITHUB_TOKEN}")

    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            remaining = resp.headers.get("X-RateLimit-Remaining", "?")
            return json.loads(resp.read().decode()), remaining
    except urllib.error.HTTPError as e:
        if e.code == 403:
            print(f"  [WARN] Rate limited. Waiting 10s...", file=sys.stderr)
            time.sleep(10)
            return github_api(url, params)
        print(f"  [ERROR] HTTP {e.code}: {e.reason}", file=sys.stderr)
        return None, "0"
    except Exception as e:
        print(f"  [ERROR] {e}", file=sys.stderr)
        return None, "0"


def search_repos_by_topic(topic, per_page=100, max_pages=5):
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
        data, remaining = github_api(url, params)
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
                    "open_issues": item.get("open_issues_count", 0),
                    "license": (item.get("license") or {}).get("spdx_id", "Unknown"),
                })

        print(f"  [{topic}] Page {page}: {len(items)} repos (rate limit: {remaining})", file=sys.stderr)
        time.sleep(1)

    return repos


def deduplicate(repos):
    """去重"""
    seen = {}
    for r in repos:
        name = r["full_name"]
        if name not in seen or r["stars"] > seen[name]["stars"]:
            seen[name] = r
    return list(seen.values())


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
    """快速安全分级"""
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


def generate_html(repos, month):
    """生成 HTML 报告"""
    repos_sorted = sorted(repos, key=lambda x: x["stars"], reverse=True)[:50]

    now = datetime.now().strftime("%Y-%m-%d")

    rows = []
    for i, r in enumerate(repos_sorted, 1):
        level, label, color, bg = security_level(r)
        platform = classify_platform(r)
        desc = escape(r.get("description", "暂无描述")[:120])
        if len(r.get("description", "")) > 120:
            desc += "..."

        top_class = ' class="top3"' if i <= 3 else ""

        rows.append(f"""        <tr{top_class}>
          <td class="rank">{i}</td>
          <td><div class="repo-name">{escape(r['full_name'])}</div><div class="repo-desc">{desc}</div></td>
          <td class="stars">{r['stars']:,}</td>
          <td><span class="badge" style="background:{bg};color:{color};">{level} · {label}</span></td>
          <td>{platform}</td>
        </tr>""")

    html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<link rel="icon" type="image/svg+xml" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 32 32'><rect width='32' height='32' rx='6' fill='%23534AB7'/><text x='16' y='23' text-anchor='middle' font-size='16' font-weight='bold' fill='white' font-family='system-ui'>AS</text></svg>">
<title>GitHub Star 最高的 50 个 AI Agent Skill — {month}</title>
<style>
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; background: #f8f9fa; color: #1a1a2e; line-height: 1.6; }}
  .container {{ max-width: 1100px; margin: 0 auto; padding: 32px 24px; }}
  h1 {{ font-size: 26px; font-weight: 600; margin-bottom: 8px; }}
  .subtitle {{ font-size: 14px; color: #6b7280; margin-bottom: 24px; }}
  .summary {{ display: flex; gap: 16px; margin-bottom: 24px; flex-wrap: wrap; }}
  .stat-card {{ background: #fff; border-radius: 8px; padding: 16px 24px; border: 1px solid #e5e7eb; flex: 1; min-width: 140px; }}
  .stat-card .label {{ font-size: 12px; color: #6b7280; margin-bottom: 4px; }}
  .stat-card .value {{ font-size: 22px; font-weight: 600; color: #534AB7; }}
  table {{ width: 100%; border-collapse: collapse; background: #fff; border-radius: 12px; overflow: hidden; box-shadow: 0 1px 3px rgba(0,0,0,0.08); }}
  thead {{ background: #534AB7; }}
  thead th {{ color: #fff; font-size: 13px; font-weight: 500; padding: 14px 16px; text-align: left; }}
  thead th:first-child {{ width: 50px; text-align: center; }}
  thead th:nth-child(3) {{ width: 90px; text-align: right; }}
  tbody tr {{ border-bottom: 1px solid #f0f0f0; }}
  tbody tr:hover {{ background: #f5f3ff; }}
  tbody td {{ padding: 12px 16px; font-size: 13px; vertical-align: top; }}
  td.rank {{ text-align: center; font-weight: 600; color: #9ca3af; font-size: 15px; }}
  td.stars {{ text-align: right; font-weight: 600; color: #534AB7; white-space: nowrap; }}
  .repo-name {{ font-weight: 500; color: #1a1a2e; }}
  .repo-desc {{ color: #6b7280; font-size: 12px; margin-top: 2px; line-height: 1.5; }}
  .badge {{ display: inline-block; font-size: 11px; padding: 2px 8px; border-radius: 4px; font-weight: 500; white-space: nowrap; }}
  .top3 {{ background: #faf9ff; }}
  .top3 td.rank {{ color: #534AB7; }}
  .footer {{ margin-top: 24px; padding: 16px; background: #fff; border-radius: 8px; border: 1px solid #e5e7eb; font-size: 12px; color: #6b7280; line-height: 1.8; }}
</style>
</head>
<body>
<div class="container">
  <h1>GitHub Star 最高的 AI Agent Skills Top 50</h1>
  <p class="subtitle">数据更新：{now} · 报告月份：{month} · 自动采集自 GitHub API</p>

  <div class="summary">
    <div class="stat-card"><div class="label">收录 Skill 数</div><div class="value">{len(repos_sorted)}</div></div>
    <div class="stat-card"><div class="label">最高 Star</div><div class="value">{repos_sorted[0]['stars']:,}</div></div>
    <div class="stat-card"><div class="label">采集来源</div><div class="value">GitHub API</div></div>
    <div class="stat-card"><div class="label">搜索 Topics</div><div class="value">{len(TOPICS)}</div></div>
  </div>

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

  <div class="footer">
    <p><strong>数据说明：</strong></p>
    <p>• 数据通过 GitHub Search API 采集，搜索 topics: {", ".join(TOPICS)}</p>
    <p>• 最低 Star 门槛：{MIN_STARS}，最多采集 {MAX_REPOS} 个仓库</p>
    <p>• 安全等级为快速评估（S=官方/A=高可信/B=中可信/C=需审查/D=高风险），仅供参考</p>
    <p>• 生成时间：{now} · 采集脚本：collect_star.py v1.0</p>
  </div>
</div>
</body>
</html>"""

    return html


def main():
    parser = argparse.ArgumentParser(description="AI Skills Star Ranking Collector")
    parser.add_argument("--output", "-o", required=True, help="Output HTML file path")
    parser.add_argument("--month", "-m", default=None, help="Report month (YYYY-MM)")
    args = parser.parse_args()

    if not args.month:
        args.month = datetime.now().strftime("%Y-%m")

    print(f"[Star Ranking] Starting collection for {args.month}...", file=sys.stderr)

    all_repos = []
    for topic in TOPICS:
        print(f"  Searching topic: {topic}", file=sys.stderr)
        repos = search_repos_by_topic(topic)
        all_repos.extend(repos)
        print(f"  Found {len(repos)} repos for topic: {topic}", file=sys.stderr)

    repos = deduplicate(all_repos)
    repos.sort(key=lambda x: x["stars"], reverse=True)
    repos = repos[:MAX_REPOS]

    print(f"[Star Ranking] Total unique repos: {len(repos)}", file=sys.stderr)
    print(f"[Star Ranking] Top 5: {[(r['full_name'], r['stars']) for r in repos[:5]]}", file=sys.stderr)

    html = generate_html(repos, args.month)

    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    with open(args.output, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"[Star Ranking] Report saved to: {args.output}", file=sys.stderr)
    print(f"[Star Ranking] Done. {len(repos[:50])} skills in report.", file=sys.stderr)


if __name__ == "__main__":
    main()
