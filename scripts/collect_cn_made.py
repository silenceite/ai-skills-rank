#!/usr/bin/env python3
"""
AI Skills Rank - CN-Made Ranking Collector
发现和推广中国开发者创作的 AI Agent Skills。
"""
import argparse, json, os, sys, time, urllib.request, urllib.error
from datetime import datetime, timezone
from html import escape

GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN") or os.environ.get("COLLECTOR_TOKEN", "")
TOPICS = ["claude-code-skills", "openclaw-skills", "agent-skills"]
MIN_STARS = 10  # 国产 skill 门槛降低

def api(url):
    req = urllib.request.Request(url)
    req.add_header("Accept","application/vnd.github+json")
    req.add_header("User-Agent","ai-skills-rank")
    if GITHUB_TOKEN: req.add_header("Authorization",f"Bearer {GITHUB_TOKEN}")
    try:
        with urllib.request.urlopen(req,timeout=30) as r: return json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        if e.code==403: time.sleep(10); return api(url)
        return None
    except: return None

def has_chinese(text):
    if not text: return False
    return any('\u4e00' <= c <= '\u9fff' for c in text)

def is_cn_developer(repo):
    """判断是否为国产"""
    owner = repo.get("owner",{})
    if isinstance(owner, dict):
        owner_login = owner.get("login","")
    else:
        owner_login = str(owner)
    
    desc = repo.get("description") or ""
    name = repo.get("full_name","")
    topics = repo.get("topics",[])
    
    # 中国公司/组织
    cn_orgs = ["iflytek","alibaba","tencent","bytedance","baidu","huacloud","voltagent"]
    if any(org in owner_login.lower() for org in cn_orgs):
        return True, "中国公司/组织"
    
    # README 含中文（用 description 代替）
    if has_chinese(desc):
        return True, "中文描述"
    
    # 仓库名含中文
    if has_chinese(name):
        return True, "中文仓库名"
    
    return False, None

def search(topic):
    repos=[]
    for p in range(1,4):
        d=api(f"https://api.github.com/search/repositories?q=topic:{topic}&sort=stars&order=desc&per_page=100&page={p}")
        if not d or not d.get("items"): break
        repos.extend([r for r in d["items"] if r.get("stargazers_count",0)>=MIN_STARS])
        time.sleep(1)
    return repos

def score_cn_made(r, reason):
    stars = r.get("stargazers_count",0)
    desc = r.get("description") or ""
    name = r.get("full_name","").lower()
    
    # 综合热度 25%
    s1 = min(100, stars/500) if stars>=1000 else (60 if stars>=100 else 40 if stars>=10 else 20)
    
    # 技术创新度 25%
    cn_kw = ["glm","deepseek","qwen","feishu","dingtalk","wechat","飞书","钉钉","微信","中文"]
    s2 = 100 if any(k in name or k in desc.lower() for k in cn_kw) else 60
    
    # 维护活跃度 20%
    try:
        pushed=datetime.strptime(r.get("pushed_at","")[:19],"%Y-%m-%dT%H:%M:%S")
        days=(datetime.now(timezone.utc).replace(tzinfo=None)-pushed).days
        s3=100 if days<=30 else 70 if days<=90 else 40 if days<=180 else 10
    except: s3=10
    
    # 国内影响力 20%
    s4 = 70 if has_chinese(desc) else 40
    
    # 文档生态 10%
    s5 = 100 if has_chinese(desc) else 40
    
    total = s1*.25+s2*.25+s3*.20+s4*.20+s5*.10
    if total>=80: return ("明星项目","#0F6E56","#E1F5EE",round(total,1))
    if total>=60: return ("优秀项目","#534AB7","#EEEDFE",round(total,1))
    if total>=40: return ("潜力项目","#854F0B","#FAEEDA",round(total,1))
    if total>=20: return ("早期项目","#D85A30","#FAECE7",round(total,1))
    return ("待观察","#A32D2D","#FCEBEB",round(total,1))

def gen_html(repos, month):
    now = datetime.now().strftime("%Y-%m-%d")
    rows = []
    for i, r in enumerate(repos, 1):
        lv, lc, lb, sc = r["cn_made_info"]
        desc = escape((r.get("description") or "")[:100])
        reason = r.get("cn_reason","")
        top = f' class="top3"' if i <= 3 else ""
        rows.append(f'<tr{top}><td class="rank">{i}</td><td><div class="repo-name">{escape(r["full_name"])}</div><div class="repo-desc">{desc}</div><div class="cn-tag">国产判定：{escape(reason)}</div></td><td class="score">{sc}</td><td><span class="badge" style="background:{lb};color:{lc};">{lv}</span></td><td>{r.get("stargazers_count",0):,}</td></tr>')
    star_count = sum(1 for r in repos if r["cn_made_info"][0]=="明星项目")
    good_count = sum(1 for r in repos if r["cn_made_info"][0]=="优秀项目")
    return f"""<!DOCTYPE html><html lang="zh-CN"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>国产 AI Agent Skills 创作榜单 Top 20 — {month}</title>
<style>*{{margin:0;padding:0;box-sizing:border-box}}body{{font-family:-apple-system,sans-serif;background:#f8f9fa;color:#1a1a2e;line-height:1.6}}.container{{max-width:1100px;margin:0 auto;padding:32px 24px}}h1{{font-size:26px;font-weight:600;margin-bottom:8px}}.subtitle{{font-size:14px;color:#6b7280;margin-bottom:24px}}.summary{{display:flex;gap:16px;margin-bottom:24px;flex-wrap:wrap}}.stat-card{{background:#fff;border-radius:8px;padding:16px 24px;border:1px solid #e5e7eb;flex:1;min-width:140px}}.stat-card .label{{font-size:12px;color:#6b7280}}.stat-card .value{{font-size:22px;font-weight:600;color:#185FA5}}table{{width:100%;border-collapse:collapse;background:#fff;border-radius:12px;overflow:hidden;box-shadow:0 1px 3px rgba(0,0,0,.08)}}thead{{background:#185FA5}}thead th{{color:#fff;font-size:13px;font-weight:500;padding:14px 16px;text-align:left}}tbody tr{{border-bottom:1px solid #f0f0f0}}tbody tr:hover{{background:#eff6ff}}tbody td{{padding:12px 16px;font-size:13px}}td.rank{{text-align:center;font-weight:600;color:#9ca3af;font-size:15px}}td.score{{text-align:right;font-weight:600;color:#185FA5}}.repo-name{{font-weight:500}}.repo-desc{{color:#6b7280;font-size:12px;margin-top:2px}}.cn-tag{{color:#185FA5;font-size:11px;margin-top:2px}}.badge{{display:inline-block;font-size:11px;padding:2px 8px;border-radius:4px;font-weight:500}}.top3{{background:#eff6ff}}.top3 td.rank{{color:#185FA5}}.footer{{margin-top:24px;padding:16px;background:#fff;border-radius:8px;border:1px solid #e5e7eb;font-size:12px;color:#6b7280}}</style>
</head><body><div class="container"><h1>国产 AI Agent Skills 创作榜单 Top 20</h1><p class="subtitle">数据更新：{now} · {month} · GitHub API 自动采集</p>
<div class="summary"><div class="stat-card"><div class="label">收录数</div><div class="value">{len(repos)}</div></div><div class="stat-card"><div class="label">明星项目</div><div class="value">{star_count}</div></div><div class="stat-card"><div class="label">优秀项目</div><div class="value">{good_count}</div></div></div>
<table><thead><tr><th>#</th><th>仓库名称</th><th>评分</th><th>推荐等级</th><th>Star</th></tr></thead><tbody>{chr(10).join(rows)}</tbody></table>
<div class="footer"><p>• 国产识别：GitHub profile中国/中文名/中文描述/中国公司/README声明</p><p>• 5维评估：热度(25%)+技术创新(25%)+维护(20%)+国内影响力(20%)+文档(10%)</p><p>• collect_cn_made.py v1.0 · {now}</p></div>
</div></body></html>"""

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--output","-o",required=True)
    p.add_argument("--month","-m",default=None)
    a = p.parse_args()
    if not a.month: a.month = datetime.now().strftime("%Y-%m")
    print(f"[CN-Made] Starting for {a.month}...",file=sys.stderr)
    all_r = []
    for t in TOPICS:
        print(f"  Searching: {t}",file=sys.stderr)
        all_r.extend(search(t))
    
    # 筛选国产
    cn_repos = []
    for r in all_r:
        is_cn, reason = is_cn_developer(r)
        if is_cn:
            r["cn_reason"] = reason
            cn_repos.append(r)
    
    print(f"[CN-Made] Found {len(cn_repos)} CN-made repos from {len(all_r)} total",file=sys.stderr)
    
    # 去重
    seen = {}
    for r in cn_repos:
        n = r["full_name"]
        if n not in seen or r["stargazers_count"] > seen[n]["stargazers_count"]: seen[n] = r
    repos = list(seen.values())
    repos.sort(key=lambda x: x["stargazers_count"], reverse=True)
    
    # 评分
    for r in repos: r["cn_made_info"] = score_cn_made(r, r.get("cn_reason",""))
    repos.sort(key=lambda x: x["cn_made_info"][3], reverse=True)
    repos = repos[:20]
    
    html = gen_html(repos, a.month)
    os.makedirs(os.path.dirname(a.output), exist_ok=True)
    with open(a.output, "w", encoding="utf-8") as f: f.write(html)
    print(f"[CN-Made] Done. {len(repos)} skills.",file=sys.stderr)

if __name__ == "__main__": main()
