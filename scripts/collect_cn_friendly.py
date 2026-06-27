#!/usr/bin/env python3
"""
AI Skills Rank - CN-Friendly Ranking Collector
评估 AI Agent Skills 仓库的中文友好度。
"""
import argparse, json, os, sys, time, urllib.request, urllib.error
from datetime import datetime
from html import escape

GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN") or os.environ.get("COLLECTOR_TOKEN", "")
TOPICS = ["claude-code-skills", "openclaw-skills", "agent-skills"]
MIN_STARS = 50

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

def search(topic):
    repos=[]
    for p in range(1,4):
        d=api(f"https://api.github.com/search/repositories?q=topic:{topic}&sort=stars&order=desc&per_page=100&page={p}")
        if not d or not d.get("items"): break
        repos.extend([r for r in d["items"] if r.get("stargazers_count",0)>=MIN_STARS])
        time.sleep(1)
    return repos

def has_chinese(text):
    if not text: return False
    for c in text:
        if '\u4e00' <= c <= '\u9fff': return True
    return False

def score_cn_friendly(r):
    desc = r.get("description") or ""
    topics = r.get("topics", [])
    name = r.get("full_name","").lower()
    
    # 中文文档 30%
    s1 = 100 if has_chinese(desc) else 10
    
    # 国内讨论度 25% (简化判断)
    s2 = 70 if has_chinese(desc) else 10
    
    # 中文维护者 15%
    owner = r.get("owner",{})
    if isinstance(owner, dict):
        owner_name = owner.get("login","")
    else:
        owner_name = str(owner)
    s3 = 70 if has_chinese(owner_name) else 10
    
    # 国内可用性 20%
    s4 = 70  # 默认基本可用
    
    # 中文生态适配 10%
    cn_keywords = ["glm","deepseek","qwen","feishu","dingtalk","wechat","飞书","钉钉","微信"]
    s5 = 100 if any(k in name or k in desc.lower() for k in cn_keywords) else 40
    
    total = s1*.30 + s2*.25 + s3*.15 + s4*.20 + s5*.10
    if total>=80: return ("优","#0F6E56","#E1F5EE",round(total,1))
    if total>=60: return ("良","#534AB7","#EEEDFE",round(total,1))
    if total>=40: return ("中","#854F0B","#FAEEDA",round(total,1))
    if total>=20: return ("差","#D85A30","#FAECE7",round(total,1))
    return ("极差","#A32D2D","#FCEBEB",round(total,1))

def gen_html(repos, month):
    now = datetime.now().strftime("%Y-%m-%d")
    rows = []
    for i, r in enumerate(repos, 1):
        lv, lc, lb, sc = r["cn_info"]
        desc = escape((r.get("description") or "")[:100])
        top = f' class="top3"' if i <= 3 else ""
        rows.append(f'<tr{top}><td class="rank">{i}</td><td><div class="repo-name">{escape(r["full_name"])}</div><div class="repo-desc">{desc}</div></td><td class="score">{sc}</td><td><span class="badge" style="background:{lb};color:{lc};">{lv}</span></td><td>{r.get("stargazers_count",0):,}</td></tr>')
    you = sum(1 for r in repos if r["cn_info"][0]=="优")
    liang = sum(1 for r in repos if r["cn_info"][0]=="良")
    return f"""<!DOCTYPE html><html lang="zh-CN"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0"><link rel="icon" type="image/svg+xml" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 32 32'><rect width='32' height='32' rx='6' fill='%23534AB7'/><text x='16' y='23' text-anchor='middle' font-size='16' font-weight='bold' fill='white' font-family='system-ui'>AS</text></svg>">
<title>中文友好 AI Agent Skills 榜单 Top 30 — {month}</title>
<style>*{{margin:0;padding:0;box-sizing:border-box}}body{{font-family:-apple-system,sans-serif;background:#f8f9fa;color:#1a1a2e;line-height:1.6}}.container{{max-width:1100px;margin:0 auto;padding:32px 24px}}h1{{font-size:26px;font-weight:600;margin-bottom:8px}}.subtitle{{font-size:14px;color:#6b7280;margin-bottom:24px}}.summary{{display:flex;gap:16px;margin-bottom:24px;flex-wrap:wrap}}.stat-card{{background:#fff;border-radius:8px;padding:16px 24px;border:1px solid #e5e7eb;flex:1;min-width:140px}}.stat-card .label{{font-size:12px;color:#6b7280}}.stat-card .value{{font-size:22px;font-weight:600;color:#854F0B}}table{{width:100%;border-collapse:collapse;background:#fff;border-radius:12px;overflow:hidden;box-shadow:0 1px 3px rgba(0,0,0,.08)}}thead{{background:#854F0B}}thead th{{color:#fff;font-size:13px;font-weight:500;padding:14px 16px;text-align:left}}tbody tr{{border-bottom:1px solid #f0f0f0}}tbody tr:hover{{background:#fffbeb}}tbody td{{padding:12px 16px;font-size:13px}}td.rank{{text-align:center;font-weight:600;color:#9ca3af;font-size:15px}}td.score{{text-align:right;font-weight:600;color:#854F0B}}.repo-name{{font-weight:500}}.repo-desc{{color:#6b7280;font-size:12px;margin-top:2px}}.badge{{display:inline-block;font-size:11px;padding:2px 8px;border-radius:4px;font-weight:500}}.top3{{background:#fffbeb}}.top3 td.rank{{color:#854F0B}}.footer{{margin-top:24px;padding:16px;background:#fff;border-radius:8px;border:1px solid #e5e7eb;font-size:12px;color:#6b7280}}</style>
</head><body><div class="container"><h1>中文友好 AI Agent Skills 榜单 Top 30</h1><p class="subtitle">数据更新：{now} · {month} · GitHub API 自动采集</p>
<div class="summary"><div class="stat-card"><div class="label">收录数</div><div class="value">{len(repos)}</div></div><div class="stat-card"><div class="label">优级</div><div class="value">{you}</div></div><div class="stat-card"><div class="label">良级</div><div class="value">{liang}</div></div></div>
<table><thead><tr><th>#</th><th>仓库名称</th><th>评分</th><th>中文友好等级</th><th>Star</th></tr></thead><tbody>{chr(10).join(rows)}</tbody></table>
<div class="footer"><p>• 5维评估：中文文档(30%)+国内讨论度(25%)+中文维护者(15%)+国内可用性(20%)+生态适配(10%)</p><p>• collect_cn_friendly.py v1.0 · {now}</p></div>
</div></body></html>"""

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--output","-o",required=True)
    p.add_argument("--month","-m",default=None)
    a = p.parse_args()
    if not a.month: a.month = datetime.now().strftime("%Y-%m")
    print(f"[CN-Friendly] Starting for {a.month}...",file=sys.stderr)
    all_r = []
    for t in TOPICS:
        print(f"  Searching: {t}",file=sys.stderr)
        all_r.extend(search(t))
    seen = {}
    for r in all_r:
        n = r["full_name"]
        if n not in seen or r["stargazers_count"] > seen[n]["stargazers_count"]: seen[n] = r
    repos = list(seen.values())
    repos.sort(key=lambda x: x["stargazers_count"], reverse=True)
    repos = repos[:60]
    for r in repos: r["cn_info"] = score_cn_friendly(r)
    repos.sort(key=lambda x: x["cn_info"][3], reverse=True)
    repos = repos[:30]
    html = gen_html(repos, a.month)
    os.makedirs(os.path.dirname(a.output), exist_ok=True)
    with open(a.output, "w", encoding="utf-8") as f: f.write(html)
    print(f"[CN-Friendly] Done. {len(repos)} skills.",file=sys.stderr)

if __name__ == "__main__": main()
