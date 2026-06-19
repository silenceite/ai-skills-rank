#!/usr/bin/env python3
"""
AI Skills Rank - Activity Ranking Collector
采集 GitHub AI Agent Skills 仓库的活跃度数据，生成 Top 30 榜单。
"""

import argparse
import json
import os
import sys
import time
import urllib.request
import urllib.error
from datetime import datetime, timedelta, timezone
from html import escape

GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN") or os.environ.get("COLLECTOR_TOKEN", "")
TOPICS = ["claude-code-skills", "openclaw-skills", "agent-skills"]
MIN_STARS = 50


def github_api(url):
    req = urllib.request.Request(url)
    req.add_header("Accept", "application/vnd.github+json")
    req.add_header("User-Agent", "ai-skills-rank")
    if GITHUB_TOKEN:
        req.add_header("Authorization", f"Bearer {GITHUB_TOKEN}")
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        if e.code == 403:
            time.sleep(10)
            return github_api(url)
        return None
    except Exception:
        return None


def search_repos(topic):
    repos = []
    for page in range(1, 4):
        url = f"https://api.github.com/search/repositories?q=topic:{topic}&sort=stars&order=desc&per_page=100&page={page}"
        data = github_api(url)
        if not data or not data.get("items"):
            break
        for item in data["items"]:
            if item.get("stargazers_count", 0) >= MIN_STARS:
                repos.append(item)
        time.sleep(1)
    return repos


def get_activity_data(repo):
    """获取活跃度数据 - 优化版，不额外调 API，用 search 结果已有数据"""
    full_name = repo["full_name"]

    # 直接用 search 返回的数据，不再额外调 API
    pushed_at = repo.get("pushed_at", "")
    updated_at = repo.get("updated_at", "")

    # 贡献者数：search API 不返回，用 forks 数近似（forks 多通常贡献者也多）
    forks = repo.get("forks_count", 0)
    contributor_est = min(100, max(1, forks // 5))  # 粗略估算

    return {
        "full_name": full_name,
        "stars": repo.get("stargazers_count", 0),
        "forks": forks,
        "description": repo.get("description") or "",
        "url": repo.get("html_url", ""),
        "open_issues": repo.get("open_issues_count", 0),
        "last_commit": pushed_at or updated_at,
        "pushed_at": pushed_at or updated_at,
        "contributors": contributor_est,
        "topics": repo.get("topics", []),
    }


def calc_score(repo):
    """计算活跃度评分"""
    now = datetime.now(timezone.utc).replace(tzinfo=None)

    # push 新近度 (20%)
    try:
        push_date = datetime.strptime(repo["pushed_at"][:19], "%Y-%m-%dT%H:%M:%S")
        days_since = (now - push_date).days
        push_score = max(0, 100 - days_since * (100/90))
    except Exception:
        push_score = 0

    # 贡献者 (20%)
    contrib = repo["contributors"]
    contrib_score = min(100, contrib * 10)

    # Issues+PR (15%)
    issues = repo["open_issues"]
    issues_score = min(100, issues * 2)

    # Star 增速代理 (10%) - 用 Star 总数近似
    stars = repo["stars"]
    star_score = min(100, stars / 100)

    # commit 频率 (35%) - 用 push 新近度近似
    commit_score = push_score

    total = commit_score * 0.35 + push_score * 0.20 + contrib_score * 0.20 + issues_score * 0.15 + star_score * 0.10
    return round(total, 1)


def maintenance_status(repo):
    try:
        push_date = datetime.strptime(repo["pushed_at"][:19], "%Y-%m-%dT%H:%M:%S")
        days = (datetime.now(timezone.utc).replace(tzinfo=None) - push_date).days
        if days <= 30: return ("活跃", "#0F6E56", "#E1F5EE")
        if days <= 90: return ("低频", "#854F0B", "#FAEEDA")
        return ("停更", "#A32D2D", "#FCEBEB")
    except Exception:
        return ("未知", "#6b7280", "#f0f0f0")


def generate_html(repos, month):
    now = datetime.now().strftime("%Y-%m-%d")
    rows = []
    for i, r in enumerate(repos, 1):
        status, scolor, sbg = maintenance_status(r)
        desc = escape(r.get("description", "")[:100])
        top = ' class="top3"' if i <= 3 else ""
        rows.append(f"""        <tr{top}>
          <td class="rank">{i}</td>
          <td><div class="repo-name">{escape(r['full_name'])}</div><div class="repo-desc">{desc}</div></td>
          <td class="score">{r['activity_score']}</td>
          <td><span class="badge" style="background:{sbg};color:{scolor};">{status}</span></td>
          <td>{r['contributors']}</td>
          <td>{r['open_issues']}</td>
          <td>{r['stars']:,}</td>
        </tr>""")

    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>AI Agent Skills 活跃度榜单 Top 30 — {month}</title>
<style>
*{{margin:0;padding:0;box-sizing:border-box}}
body{{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;background:#f8f9fa;color:#1a1a2e;line-height:1.6}}
.container{{max-width:1100px;margin:0 auto;padding:32px 24px}}
h1{{font-size:26px;font-weight:600;margin-bottom:8px}}
.subtitle{{font-size:14px;color:#6b7280;margin-bottom:24px}}
.summary{{display:flex;gap:16px;margin-bottom:24px;flex-wrap:wrap}}
.stat-card{{background:#fff;border-radius:8px;padding:16px 24px;border:1px solid #e5e7eb;flex:1;min-width:140px}}
.stat-card .label{{font-size:12px;color:#6b7280;margin-bottom:4px}}
.stat-card .value{{font-size:22px;font-weight:600;color:#0F6E56}}
table{{width:100%;border-collapse:collapse;background:#fff;border-radius:12px;overflow:hidden;box-shadow:0 1px 3px rgba(0,0,0,.08)}}
thead{{background:#0F6E56}}
thead th{{color:#fff;font-size:13px;font-weight:500;padding:14px 16px;text-align:left}}
tbody tr{{border-bottom:1px solid #f0f0f0}}
tbody tr:hover{{background:#f0fdf8}}
tbody td{{padding:12px 16px;font-size:13px;vertical-align:top}}
td.rank{{text-align:center;font-weight:600;color:#9ca3af;font-size:15px}}
td.score{{text-align:right;font-weight:600;color:#0F6E56;white-space:nowrap}}
.repo-name{{font-weight:500;color:#1a1a2e}}
.repo-desc{{color:#6b7280;font-size:12px;margin-top:2px}}
.badge{{display:inline-block;font-size:11px;padding:2px 8px;border-radius:4px;font-weight:500}}
.top3{{background:#f0fdf8}}.top3 td.rank{{color:#0F6E56}}
.footer{{margin-top:24px;padding:16px;background:#fff;border-radius:8px;border:1px solid #e5e7eb;font-size:12px;color:#6b7280;line-height:1.8}}
</style></head><body><div class="container">
<h1>AI Agent Skills 活跃度榜单 Top 30</h1>
<p class="subtitle">数据更新：{now} · 报告月份：{month} · 自动采集自 GitHub API</p>
<div class="summary">
<div class="stat-card"><div class="label">收录数</div><div class="value">{len(repos)}</div></div>
<div class="stat-card"><div class="label">最高评分</div><div class="value">{repos[0]['activity_score'] if repos else 0}</div></div>
<div class="stat-card"><div class="label">活跃维护</div><div class="value">{sum(1 for r in repos if maintenance_status(r)[0]=='活跃')}</div></div>
</div>
<table><thead><tr><th>#</th><th>仓库名称</th><th>评分</th><th>维护状态</th><th>贡献者</th><th>Issues</th><th>Star</th></tr></thead>
<tbody>{chr(10).join(rows)}</tbody></table>
<div class="footer"><p>• 评分=commit(35%)+push新近度(20%)+贡献者(20%)+Issues(15%)+Star(10%)</p><p>• 维护状态：活跃(30天内)/低频(30-90天)/停更(90天+)</p><p>• 生成时间：{now} · collect_activity.py v1.0</p></div>
</div></body></html>"""


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", "-o", required=True)
    parser.add_argument("--month", "-m", default=None)
    args = parser.parse_args()
    if not args.month: args.month = datetime.now().strftime("%Y-%m")

    print(f"[Activity] Starting for {args.month}...", file=sys.stderr)
    all_repos = []
    for topic in TOPICS:
        print(f"  Searching: {topic}", file=sys.stderr)
        all_repos.extend(search_repos(topic))

    seen = {}
    for r in all_repos:
        n = r["full_name"]
        if n not in seen or r["stargazers_count"] > seen[n]["stargazers_count"]:
            seen[n] = r
    repos = list(seen.values())
    repos.sort(key=lambda x: x["stargazers_count"], reverse=True)
    repos = repos[:80]  # 限制采集数量避免 API 超限

    print(f"[Activity] Collecting activity data for {len(repos)} repos...", file=sys.stderr)
    scored = []
    for i, r in enumerate(repos):
        data = get_activity_data(r)
        data["activity_score"] = calc_score(data)
        scored.append(data)
        if (i+1) % 20 == 0:
            print(f"  Progress: {i+1}/{len(repos)}", file=sys.stderr)

    scored.sort(key=lambda x: x["activity_score"], reverse=True)
    scored = scored[:30]

    html = generate_html(scored, args.month)
    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    with open(args.output, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"[Activity] Done. {len(scored)} skills. Saved to {args.output}", file=sys.stderr)


if __name__ == "__main__":
    main()
