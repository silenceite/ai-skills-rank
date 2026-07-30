#!/usr/bin/env python3
"""
AI Agent Skills Rank — Trending Ranking Collector (v1.1)
抓取 GitHub Trending monthly 页面，筛选 AI / Agent / MCP 相关仓库，
按本月新增 Star 排序，生成 Top 30 飙升榜 HTML 报告。

执行频率：每月 28 号 UTC 12:00（北京时间 20:00）

v1.1 增强（2026-07-30）：
- 反爬健壮性：随机真实浏览器 UA 池、识别 429/403 的 Retry-After、
  45s 超时、对"过小响应（疑似反爬验证页）"主动重试。
- 兜底机制：实时抓取全部重试失败后，回退到最近一次成功缓存的 HTML，
  确保即便被 GitHub 限流也能产出（带"数据可能滞后"标注）的报告，
  不再出现"完全不能更新"的空窗。
"""
import argparse
import json
import os
import random
import re
import sys
import time
import urllib.request
import urllib.error
from datetime import datetime
from html import escape

GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "")

# 脚本根目录与缓存目录（data/cache，已被 .gitignore 忽略，不入库）
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
CACHE_DIR = os.path.join(os.path.dirname(SCRIPT_DIR), "data", "cache")
CACHE_HTML = os.path.join(CACHE_DIR, "trending_last.html")
CACHE_META = os.path.join(CACHE_DIR, "trending_last.meta.json")

# 真实浏览器 User-Agent 池，降低被 Trending 反爬拦截的概率
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:125.0) Gecko/20100101 Firefox/125.0",
]

# 筛选关键词：判定是否为 AI/Agent 相关项目
SKILL_NAME_PATTERNS = [
    r"-skills$", r"^skills-",           # 以 -skills 结尾或 skills- 开头
    r"agent-skills?", r"skills?-agent",  # 含 agent-skill
    r"-mcp$", r"^mcp-",                 # MCP 服务器
    r"^ai-", r"-ai$",                   # AI 前缀后缀
    r"agent-",                           # agent- 前缀
]
SKILL_DESC_KEYWORDS = [
    # Agent/Skill 核心
    "agent skill", "agent skills", "agent-skills",
    "SKILL.md", "skill.md",
    "skills for ai", "skills for agent", "ai skills",
    "agentic skill", "agentic",
    # MCP 生态
    "mcp server", "mcp skill", "mcp ",
    # Claude/Codex/Cursor 生态
    "claude code", "claude-code", "claude skills",
    "codex skill", "cursor skill", "cursor agent",
    # AI Agent 相关
    "ai agent", "ai agents", "agent framework",
    "coding agent", "ai coding", "ai-powered",
    "agent tool", "ai agent tool",
    # AI 开发工具
    "ai voice", "ai studio", "llm",
    "system prompt", "language model",
    # 通用 AI+Skill
    "agent for", "agent toolkit",
]

TRENDING_URL = "https://github.com/trending?since=monthly"

# 反爬退避策略
MAX_RETRIES = 4
RETRY_DELAY = 10
REQUEST_TIMEOUT = 45
# 响应过小（字节数低于此值）通常意味着拿到了反爬验证页而非真实列表
ANTI_BOT_MIN_BYTES = 5000


def _write_cache(html):
    """将成功抓取的 HTML 与元数据写入本地缓存（供后续兜底使用）"""
    try:
        os.makedirs(CACHE_DIR, exist_ok=True)
        with open(CACHE_HTML, "w", encoding="utf-8") as f:
            f.write(html)
        with open(CACHE_META, "w", encoding="utf-8") as f:
            json.dump(
                {"fetched_at": datetime.now().isoformat(), "url": TRENDING_URL},
                f, ensure_ascii=False,
            )
    except Exception as e:
        print(f"[Trending] WARN: failed to write cache: {e}", file=sys.stderr)


def load_cache_html():
    """读取最近一次成功缓存的 Trending HTML"""
    if os.path.exists(CACHE_HTML):
        try:
            with open(CACHE_HTML, encoding="utf-8") as f:
                return f.read()
        except Exception:
            return ""
    return ""


def load_cache_meta():
    """读取缓存元数据（含抓取时间）"""
    if os.path.exists(CACHE_META):
        try:
            with open(CACHE_META, encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}


def fetch_trending_html():
    """请求 GitHub Trending 页面原始 HTML，含重试与反爬退避。

    返回 HTML 字符串；全部重试失败返回空字符串（由调用方决定是否兜底）。
    """
    for attempt in range(1, MAX_RETRIES + 1):
        ua = random.choice(USER_AGENTS)
        try:
            req = urllib.request.Request(TRENDING_URL)
            req.add_header("User-Agent", ua)
            req.add_header("Accept", "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8")
            req.add_header("Accept-Language", "en-US,en;q=0.9")
            req.add_header("Connection", "keep-alive")
            with urllib.request.urlopen(req, timeout=REQUEST_TIMEOUT) as resp:
                html = resp.read().decode("utf-8", errors="replace")
                # 反爬验证页通常很小，拿到这种页面应当作失败重试
                if len(html) < ANTI_BOT_MIN_BYTES:
                    raise ValueError(
                        f"suspiciously small response ({len(html)} bytes), likely anti-bot page"
                    )
                print(
                    f"[Trending] Fetched {len(html)} bytes (UA #{attempt})",
                    file=sys.stderr,
                )
                _write_cache(html)
                return html
        except urllib.error.HTTPError as e:
            wait = RETRY_DELAY * attempt
            # 尊重服务端 Retry-After（常见于 429/403 限流）
            retry_after = e.headers.get("Retry-After") if e.headers else None
            if retry_after:
                try:
                    wait = max(wait, int(retry_after))
                except ValueError:
                    pass
            print(
                f"[Trending] HTTP {e.code} on attempt {attempt}; retry after {wait}s",
                file=sys.stderr,
            )
            if attempt < MAX_RETRIES:
                time.sleep(wait)
        except Exception as e:
            wait = RETRY_DELAY * attempt
            print(
                f"[Trending] Error on attempt {attempt}: {e}; retry after {wait}s",
                file=sys.stderr,
            )
            if attempt < MAX_RETRIES:
                time.sleep(wait)
    print("[Trending] All retries exhausted. Will try local cache fallback.", file=sys.stderr)
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

        # 提取本月新增 star
        weekly_match = re.search(r'(\d[\d,]*)\s+stars?\s+this\s+(?:week|month)', context, re.IGNORECASE)
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

    # 描述中包含 "AI" 独立词（如 "AI tool", "AI-powered"）或 "OpenAI"
    if re.search(r'\bai\b', desc) or "openai" in desc:
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


def generate_html(repos, month, fallback_meta=None):
    """生成飙升榜 HTML 报告。

    fallback_meta: 若本次为缓存兜底，则传入缓存元数据（含 fetched_at），
                   并在页脚标注数据可能滞后。
    """
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
            "本月 GitHub Trending 上暂未发现 Agent Skill 相关仓库</td></tr>"
        )

    # 最高周增
    max_weekly = f"{repos[0]['weekly_stars']:,}+" if repos else "—"

    # 缓存兜底提示
    if fallback_meta:
        fetched_at = fallback_meta.get("fetched_at", "未知时间")
        fallback_note = (
            f'<p style="color:#b45309;">⚠️ <strong>数据说明：</strong>'
            f'本次实时抓取 GitHub Trending 失败（疑似限流 / 反爬），已回退使用最近一次成功缓存'
            f'（抓取于 {escape(fetched_at)}）。数据可能略有滞后，下个周期将自动重试实时抓取。</p>'
        )
    else:
        fallback_note = ""

    html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<meta name="description" content="AI Agent Skills 飙升榜 Top 30。抓取 GitHub Trending 页面，筛选 AI / Agent / MCP 相关热门项目，按本月新增 Star 排序。每月 28 号自动更新。">
<meta property="og:title" content="AI Agent Skills 飙升榜 · {month}">
<meta property="og:description" content="本月哪个 AI Agent Skill 最火？GitHub Trending 实时热度排名，每月自动更新。">
<meta property="og:type" content="website">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="AI Agent Skills 飙升榜 · {month}">
<title>AI Agent Skills 飙升榜 · {month}</title>
<link rel="icon" type="image/svg+xml" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 32 32'><rect width='32' height='32' rx='6' fill='%23534AB7'/><text x='16' y='23' text-anchor='middle' font-size='16' font-weight='bold' fill='white' font-family='system-ui'>AS</text></svg>">
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
  <p class="subtitle">数据来源：GitHub Trending · 更新：{now} · 报告月份：{month}</p>

  <div class="summary">
    <div class="stat-card"><div class="label">本月上榜</div><div class="value">{len(repos)}</div></div>
    <div class="stat-card"><div class="label">最高月增</div><div class="value">{max_weekly}</div></div>
    <div class="stat-card"><div class="label">数据来源</div><div class="value">GitHub Trending</div></div>
    <div class="stat-card"><div class="label">更新周期</div><div class="value">每月28号</div></div>
  </div>

  <table>
    <thead>
      <tr>
        <th># 飙升</th>
        <th>仓库名称 / 核心功能</th>
        <th>本月新增 ⭐</th>
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
    <p>• 数据来自 <a href="https://github.com/trending?since=monthly" target="_blank">GitHub Trending</a> 页面，筛选 AI / Agent / MCP 相关热门项目</p>
    <p>• 筛选逻辑：仓库名匹配 skill/agent/mcp 模式，或描述中含 AI agent / coding agent / MCP / Claude Code 等关键词</p>
    <p>• 榜单按本月新增 Star 降序排列，反映当前 GitHub 上"正在爆火"的 AI Agent 生态项目</p>
    <p>• 生成时间：{now} · 采集脚本：collect_trending.py v1.1</p>
{fallback_note}
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

    # 1. 实时抓取 Trending HTML（含重试与反爬退避）
    html = fetch_trending_html()

    # 2. 兜底：实时抓取失败则回退最近一次成功缓存
    fallback_used = False
    if not html:
        cached = load_cache_html()
        if cached:
            html = cached
            fallback_used = True
            meta = load_cache_meta()
            print(
                f"[Trending] Using cached HTML fallback (fetched_at={meta.get('fetched_at')})",
                file=sys.stderr,
            )

    if not html:
        print("[Trending] ERROR: No live data and no cache available.", file=sys.stderr)
        sys.exit(1)

    # 3. 解析仓库
    repos = parse_trending_repos(html)
    if not repos:
        print("[Trending] WARNING: No repos parsed from trending page", file=sys.stderr)
        # 生成空报告（仅当非兜底时也拿不到数据时；兜底数据通常可解析）
        repos = []

    # 4. 放宽筛选：AI/Agent/MCP 相关项目
    skill_repos = filter_agent_skills(repos)
    print(f"[Trending] Filtered {len(skill_repos)} AI/Agent repos from {len(repos)} total", file=sys.stderr)
    for r in skill_repos:
        print(f"  ✓ {r['full_name']}: +{r['weekly_stars']:,} this week", file=sys.stderr)

    # 5. 按本月新增 Star 降序排列
    skill_repos.sort(key=lambda x: x["weekly_stars"], reverse=True)
    skill_repos = skill_repos[:30]

    # 6. 生成 HTML 报告（兜底时标注滞后）
    fallback_meta = load_cache_meta() if fallback_used else None
    html_content = generate_html(skill_repos, args.month, fallback_meta=fallback_meta)

    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    with open(args.output, "w", encoding="utf-8") as f:
        f.write(html_content)

    if fallback_used:
        print(
            "[Trending] Report generated from CACHE fallback (data may be stale).",
            file=sys.stderr,
        )
    print(f"[Trending] Report saved to: {args.output}", file=sys.stderr)
    print(f"[Trending] Done. {len(skill_repos)} skills in trending report.", file=sys.stderr)


if __name__ == "__main__":
    main()
