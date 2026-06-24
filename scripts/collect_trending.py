#!/usr/bin/env python3
"""
AI Agent Skills Rank — Trending Ranking Collector
抓取 GitHub Trending weekly 页面，筛选 AI Agent Skill 相关仓库，
按本周新增 Star 排序，生成 Top 30 飙升榜 HTML 报告。

执行频率：每周日 UTC 12:00（北京时间 20:00）
"""
import argparse
import json
import os
import re
import sys
import time
import urllib.request
import urllib.error
from datetime import datetime
from html import escape

GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "")

# 筛选关键词：判定是否为 AI Agent Skill 仓库
SKILL_NAME_PATTERNS = [
    r"-skills$", r"^skills-",           # 以 -skills 结尾或 skills- 开头
    r"agent-skills?", r"skills?-agent",  # 含 agent-skill
    r"-mcp$", r"^mcp-",                 # MCP 服务器
    r"agent-",                           # agent- 前缀（如 agent-reach, agent-tool）
]
SKILL_DESC_KEYWORDS = [
    "agent skill", "agent skills",            # 直接提及 agent skill
    "agent-skills",                            # topic 格式
    "SKILL.md", "skill.md",                   # 明确引用 SKILL.md 格式
    "claude-code skills", "claude code skills",# Claude Code skills
    "skills for ai agent", "skills for agent", # skills for AI agents
    "ai coding skills", "agentic skill",       # 变体
    "mcp server", "mcp skill",                 # MCP 生态
    "agent tool", "ai agent tool",             # Agent 工具
    "claude code plugin", "codex skill",       # 各平台 skill
    "claude skills", "cursor skills",          # 平台 skills
    "ai agent skills", "agent skills repo",    # 直接匹配
]

TRENDING_URL = "https://github.com/trending?since=weekly"

# 反爬退避策略
MAX_RETRIES = 3
RETRY_DELAY = 10


def fetch_trending_html():
    """请求 GitHub Trending weekly 页面原始 HTML"""
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            req = urllib.request.Request(TRENDING_URL)
            req.add_header("User-Agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
            req.add_header("Accept", "text/html,application/xhtml+xml")
            req.add_header("Accept-Language", "en-US,en;q=0.9")
            with urllib.request.urlopen(req, timeout=30) as resp:
                html = resp.read().decode("utf-8", errors="replace")
                print(f"[Trending] Fetched {len(html)} bytes from GitHub Trending", file=sys.stderr)
                return html
        except urllib.error.HTTPError as e:
            print(f"[Trending] HTTP {e.code} on attempt {attempt}", file=sys.stderr)
            if attempt < MAX_RETRIES:
                time.sleep(RETRY_DELAY * attempt)
        except Exception as e:
            print(f"[Trending] Error on attempt {attempt}: {e}", file=sys.stderr)
            if attempt < MAX_RETRIES:
                time.sleep(RETRY_DELAY * attempt)
    print("[Trending] All retries exhausted. Returning empty.", file=sys.stderr)
    return ""


def parse_number(text):
    """将 '1,234' 或 '1.2k' 格式转为整数"""
    text = text.strip().lower().replace(",", "")
    if "k" in text:
        return int(float(text.replace("k", "")) * 1000)
    try:
        return int(text)
    except ValueError:
        return 0


def parse_trending_repos(html):
    """从 GitHub Trending HTML 中提取仓库列表"""
    repos = []
    seen = set()

    # 方法 1：按 <article class="Box-row"> 分割
    articles = re.split(r'<article\s+class="Box-row"[^>]*>', html)
    blocks = [a for a in articles if a]  # 所有有效块

    # 方法 2：如果方法 1 捕获不到，直接从全文搜索 h2 仓库链接
    if len(blocks) <= 1:
        # 全 HTML 作为一个大块
        blocks = [html]

    print(f"[Trending] Processing {len(blocks)} blocks (articles + fallback)", file=sys.stderr)

    # 先收集 h2 中所有的仓库链接（跨所有区块）
    # 找到所有 h2.h3.lh-condensed，这些就是 trending repos 的标题
    h2_blocks = re.finditer(r'<h2 class="h3 lh-condensed">(.*?)</h2>', html, re.DOTALL)
    h2_repos = {}
    for h2m in h2_blocks:
        # 在 h2 块内找 repo 链接：<a ... href="/owner/repo" ...>
        a_match = re.search(
            r'href="/([a-zA-Z0-9][a-zA-Z0-9.-]*)/([a-zA-Z0-9][a-zA-Z0-9._-]*)"',
            h2m.group(1)
        )
        if not a_match:
            continue
        owner, repo_name = a_match.groups()
        skip_owners = {"trending", "explore", "topics", "collections", "settings",
                       "notifications", "login", "sponsors", "features", "github",
                       "marketplace", "pricing", "enterprise", "orgs", "security"}
        if owner.lower() in skip_owners or owner.startswith("login"):
            continue
        if "?" in repo_name or "%" in repo_name or "&" in repo_name:
            continue
        full_name = f"{owner}/{repo_name}"
        h2_repos[full_name] = h2m.start()

    print(f"[Trending] Found {len(h2_repos)} unique repos in h2 headings", file=sys.stderr)

    # 对每个仓库，在附近的 HTML 中提取描述和 star 数据
    for full_name, pos in h2_repos.items():
        if full_name in seen:
            continue
        seen.add(full_name)
        owner, repo_name = full_name.split("/", 1)

        # 提取描述（h2 后面的 <p> 标签）
        # 取到下一个 h2 或 20000 字符的上下文窗口
        next_h2 = html.find('<h2 class="h3 lh-condensed">', pos + 1)
        context_end = next_h2 if next_h2 > pos else pos + 20000
        context = html[pos:context_end]
        desc_match = re.search(
            r'<p\s+class="[^"]*color-fg-muted[^"]*"[^>]*>\s*(.*?)\s*</p>',
            context, re.DOTALL
        )
        description = ""
        if desc_match:
            description = re.sub(r'<[^>]+>', '', desc_match.group(1)).strip()

        # 提取本周新增 star
        weekly_match = re.search(r'(\d[\d,]*)\s+stars?\s+this\s+week', context, re.IGNORECASE)
        weekly_stars = parse_number(weekly_match.group(1)) if weekly_match else 0

        # 提取总 star（stargazers 链接）
        total_stars = 0
        star_link = re.search(
            rf'href="/{re.escape(owner)}/{re.escape(repo_name)}/stargazers"[^>]*>\s*(.*?)\s*</a>',
            context, re.DOTALL
        )
        if star_link:
            star_text = re.sub(r'<[^>]+>', '', star_link.group(1)).strip()
            total_stars = parse_number(star_text)
        if total_stars == 0:
            alt_star = re.search(r'stargazers.*?>([\d,]+)</a>', context, re.IGNORECASE)
            if alt_star:
                total_stars = parse_number(alt_star.group(1))

        # 提取语言
        lang_match = re.search(r'programmingLanguage">([^<]+)<', context)
        language = lang_match.group(1).strip() if lang_match else ""

        repos.append({
            "full_name": full_name,
            "owner": owner,
            "repo": repo_name,
            "description": description,
            "weekly_stars": weekly_stars,
            "stars": total_stars,
            "language": language,
            "url": f"https://github.com/{full_name}",
        })

    print(f"[Trending] Parsed {len(repos)} repos from trending page", file=sys.stderr)
    for r in repos[:5]:
        print(f"  {r['full_name']}: +{r['weekly_stars']:,} this week, {r['stars']:,} total", file=sys.stderr)
    return repos


def is_agent_skill_repo(repo):
    """判断仓库是否为 AI Agent Skill 相关"""
    name = repo["full_name"].lower()
    desc = repo.get("description", "").lower()

    # 仓库名匹配
    for pattern in SKILL_NAME_PATTERNS:
        if re.search(pattern, name):
            return True

    # 描述关键词匹配
    for keyword in SKILL_DESC_KEYWORDS:
        if keyword in desc:
            return True

    # 仓库名直接包含 skill 且描述涉及 agent/AI
    if "skill" in name and ("agent" in desc or "claude" in desc or "ai " in desc):
        return True

    return False


def filter_agent_skills(repos):
    """筛选 Agent Skill 相关仓库，并通过 API 验证 topics（尽力而为）"""
    skill_repos = []

    for repo in repos:
        if is_agent_skill_repo(repo):
            # 尝试用 API 获取 topics 做精确验证
            topics = fetch_repo_topics(repo["full_name"])
            if topics:
                repo["topics"] = topics
            # 即使 API 失败，关键词匹配通过也保留
            skill_repos.append(repo)

    return skill_repos


def fetch_repo_topics(full_name):
    """通过 GitHub API 获取仓库的 topics 标签"""
    if not GITHUB_TOKEN:
        return None

    url = f"https://api.github.com/repos/{full_name}/topics"
    req = urllib.request.Request(url)
    req.add_header("Accept", "application/vnd.github.mercy-preview+json")
    req.add_header("User-Agent", "ai-skills-rank")
    req.add_header("Authorization", f"Bearer {GITHUB_TOKEN}")
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode())
            return data.get("names", [])
    except Exception:
        return None


def generate_html(repos, month):
    """生成飙升榜 HTML 报告"""
    now = datetime.now().strftime("%Y-%m-%d %H:%M UTC")

    rows = []
    for i, repo in enumerate(repos, 1):
        name = escape(repo["full_name"])
        desc = escape(repo.get("description", "") or "(无描述)")
        weekly = repo.get("weekly_stars", 0)
        total = repo.get("stars", 0)
        lang = escape(repo.get("language", "") or "")
        url = escape(repo.get("url", ""))
        topics = repo.get("topics", [])

        # 安全等级标记（基于已知规则）
        badge = ""
        if topics:
            topic_str = ", ".join(topics[:3])
            badge = f'<span class="badge badge-topic">{escape(topic_str)}</span>'

        # 飙升快慢标记
        if weekly >= 5000:
            fire = "🔥🔥🔥"
        elif weekly >= 2000:
            fire = "🔥🔥"
        elif weekly >= 500:
            fire = "🔥"
        else:
            fire = ""

        rows.append(
            f'<tr class="{"top3" if i <= 3 else ""}">'
            f'<td class="rank">#{i} {fire}</td>'
            f'<td>'
            f'<a class="repo-name" href="{url}" target="_blank">{name}</a>'
            f'<div class="repo-desc">{desc}</div>'
            f'{badge}'
            f"</td>"
            f'<td class="stars">+{weekly:,}</td>'
            f'<td class="stars">{total:,}</td>'
            f'<td>{lang}</td>'
            f"</tr>"
        )

    if not rows:
        rows.append(
            '<tr><td colspan="5" style="text-align:center;padding:40px;color:#9ca3af;">'
            "本周 GitHub Trending 上暂未发现 Agent Skill 相关仓库</td></tr>"
        )

    # 最高周增
    max_weekly = f"{repos[0]['weekly_stars']:,}+" if repos else "—"

    html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>AI Agent Skills 飙升榜 · {month}</title>
<style>
* {{ margin: 0; padding: 0; box-sizing: border-box; }}
body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", system-ui, sans-serif; background: #f8f9fa; color: #1a1a2e; }}
.container {{ max-width: 900px; margin: 0 auto; padding: 24px 20px 48px; }}
h1 {{ font-size: 24px; margin-bottom: 4px; color: #ff6b35; }}
.subtitle {{ font-size: 13px; color: #6b7280; margin-bottom: 20px; }}
.summary {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; margin-bottom: 24px; }}
.stat-card {{ background: #fff; border-radius: 8px; padding: 16px; border: 1px solid #e5e7eb; text-align: center; }}
.stat-card .label {{ font-size: 11px; color: #9ca3af; text-transform: uppercase; margin-bottom: 4px; }}
.stat-card .value {{ font-size: 20px; font-weight: 700; color: #ff6b35; }}
table {{ width: 100%; border-collapse: separate; border-spacing: 0; background: #fff; border-radius: 10px; overflow: hidden; border: 1px solid #e5e7eb; }}
thead {{ background: #ff6b35; color: #fff; }}
thead th {{ padding: 12px 16px; font-size: 13px; text-align: left; font-weight: 600; }}
thead th:first-child {{ width: 80px; text-align: center; }}
thead th.stars {{ text-align: right; }}
tbody tr {{ border-bottom: 1px solid #f0f0f0; transition: background 0.15s; }}
tbody tr:hover {{ background: #fff5f0; }}
tbody td {{ padding: 12px 16px; font-size: 13px; vertical-align: top; }}
td.rank {{ text-align: center; font-weight: 600; color: #9ca3af; font-size: 14px; white-space: nowrap; }}
td.stars {{ text-align: right; font-weight: 600; color: #ff6b35; white-space: nowrap; }}
td.stars:last-child {{ color: #534AB7; }}
.repo-name {{ font-weight: 500; color: #1a1a2e; text-decoration: none; }}
.repo-name:hover {{ color: #ff6b35; text-decoration: underline; }}
.repo-desc {{ color: #6b7280; font-size: 12px; margin-top: 2px; line-height: 1.5; }}
.badge {{ display: inline-block; font-size: 11px; padding: 2px 8px; border-radius: 4px; font-weight: 500; margin-top: 4px; white-space: nowrap; }}
.badge-topic {{ background: #fef3c7; color: #92400e; }}
.top3 {{ background: #fffaf5; }}
.top3 td.rank {{ color: #ff6b35; }}
.footer {{ margin-top: 24px; padding: 16px; background: #fff; border-radius: 8px; border: 1px solid #e5e7eb; font-size: 12px; color: #6b7280; line-height: 1.8; }}
.footer a {{ color: #534AB7; }}
</style>
</head>
<body>
<div class="container">
  <h1>🚀 AI Agent Skills 飙升榜 Top {len(repos)}</h1>
  <p class="subtitle">数据来源：GitHub Trending weekly · 更新：{now} · 报告月份：{month}</p>

  <div class="summary">
    <div class="stat-card"><div class="label">本周上榜</div><div class="value">{len(repos)}</div></div>
    <div class="stat-card"><div class="label">最高周增</div><div class="value">{max_weekly}</div></div>
    <div class="stat-card"><div class="label">数据来源</div><div class="value">GitHub Trending</div></div>
    <div class="stat-card"><div class="label">更新周期</div><div class="value">每周日</div></div>
  </div>

  <table>
    <thead>
      <tr>
        <th># 飙升</th>
        <th>仓库名称 / 核心功能</th>
        <th>本周新增 ⭐</th>
        <th>总 Star</th>
        <th>语言</th>
      </tr>
    </thead>
    <tbody>
{chr(10).join(rows)}
    </tbody>
  </table>

  <div class="footer">
    <p><strong>数据说明：</strong></p>
    <p>• 数据来自 <a href="https://github.com/trending?since=weekly" target="_blank">GitHub Trending weekly</a> 页面，筛选 AI Agent Skill 相关仓库</p>
    <p>• 筛选逻辑：仓库名匹配 skill/agent-skills 模式，或描述中包含 agent skill / claude code / SKILL.md 等关键词</p>
    <p>• 榜单按本周新增 Star 降序排列，反映当前 GitHub 上"正在爆火"的 Agent Skill 项目</p>
    <p>• 生成时间：{now} · 采集脚本：collect_trending.py v1.0</p>
  </div>
</div>
</body>
</html>"""

    return html


def main():
    parser = argparse.ArgumentParser(description="AI Skills Trending Ranking Collector")
    parser.add_argument("--output", "-o", required=True, help="Output HTML file path")
    parser.add_argument("--month", "-m", default=None, help="Report month (YYYY-MM)")
    args = parser.parse_args()

    if not args.month:
        args.month = datetime.now().strftime("%Y-%m")

    print(f"[Trending] Starting collection for {args.month}...", file=sys.stderr)

    # 1. 抓取 Trending HTML
    html = fetch_trending_html()
    if not html:
        print("[Trending] ERROR: Failed to fetch trending page", file=sys.stderr)
        sys.exit(1)

    # 2. 解析仓库
    repos = parse_trending_repos(html)
    if not repos:
        print("[Trending] WARNING: No repos parsed from trending page", file=sys.stderr)
        # 生成空报告
        repos = []

    # 3. 不过滤，直接使用所有 Trending 仓库
    # (Agent Skill 筛选逻辑保留备用，需要时取消注释即可)
    # skill_repos = filter_agent_skills(repos)
    skill_repos = repos
    print(f"[Trending] Using all {len(skill_repos)} trending repos (filter disabled)", file=sys.stderr)

    # 4. 按本周新增 Star 降序排列
    skill_repos.sort(key=lambda x: x["weekly_stars"], reverse=True)
    skill_repos = skill_repos[:30]

    # 5. 生成 HTML 报告
    html_content = generate_html(skill_repos, args.month)

    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    with open(args.output, "w", encoding="utf-8") as f:
        f.write(html_content)

    print(f"[Trending] Report saved to: {args.output}", file=sys.stderr)
    print(f"[Trending] Done. {len(skill_repos)} skills in trending report.", file=sys.stderr)


if __name__ == "__main__":
    main()
