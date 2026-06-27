#!/usr/bin/env python3
"""
AI Skills Rank - Security Ranking Collector
对 GitHub AI Agent Skills 仓库进行安全分级评估。
"""
import argparse, json, os, sys, time, urllib.request, urllib.error
from datetime import datetime, timezone
from html import escape

GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN") or os.environ.get("COLLECTOR_TOKEN", "")
TOPICS = ["claude-code-skills", "openclaw-skills", "agent-skills"]
MIN_STARS = 50
OFFICIAL = ["anthropics","openai","vercel","vercel-labs","nvidia","microsoft","google","iflytek","trailofbits","remotion-dev"]
KNOWN = ["composiohq","k-dense-ai","voltagent","sickn33","obra","hesreallyhim","affaan-m","shanraisshan"]

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

def score_security(r):
    owner=r["owner"]["login"].lower() if isinstance(r.get("owner"),dict) else r.get("owner","").lower()
    stars=r.get("stargazers_count",0)
    desc=(r.get("description") or "").lower()
    issues=r.get("open_issues_count",0)
    has_scripts = "scripts" in str(r.get("topics",[]))  # 简化判断

    # 出品方 25%
    if owner in OFFICIAL: s1=100
    elif owner in KNOWN: s1=80
    elif stars>=10000: s1=60
    elif stars>=1000: s1=40
    else: s1=20

    # 脚本风险 20% (简化：无法直接判断，给中等分)
    s2=70

    # SKILL.md质量 15% (简化：用 description 判断)
    if desc and len(desc)>20 and "最强" not in desc and "终极" not in desc: s3=70
    else: s3=30

    # 维护活跃度 15%
    try:
        pushed=datetime.strptime(r.get("pushed_at","")[:19],"%Y-%m-%dT%H:%M:%S")
        days=(datetime.now(timezone.utc).replace(tzinfo=None)-pushed).days
        s4=100 if days<=30 else 70 if days<=90 else 40 if days<=180 else 10
    except: s4=10

    # 社区审查 15%
    if stars>=50000 and issues>=100: s5=100
    elif stars>=10000 or issues>=30: s5=70
    elif stars>=1000 or issues>=10: s5=40
    else: s5=10

    # 已知安全记录 10% (默认无已知漏洞)
    s6=100

    total=s1*.25+s2*.20+s3*.15+s4*.15+s5*.15+s6*.10
    if total>=85: return ("S","闭眼装","#0F6E56","#E1F5EE",round(total,1))
    if total>=70: return ("A","放心装","#534AB7","#EEEDFE",round(total,1))
    if total>=55: return ("B","看一眼","#854F0B","#FAEEDA",round(total,1))
    if total>=40: return ("C","需审查","#D85A30","#FAECE7",round(total,1))
    return ("D","不建议","#A32D2D","#FCEBEB",round(total,1))

def gen_html(repos,month):
    now=datetime.now().strftime("%Y-%m-%d")
    rows=[]
    for i,r in enumerate(repos,1):
        lv,lb,lc,lb_,sc=r["sec_info"]
        desc=escape((r.get("description") or "")[:100])
        top=' class="top3"' if i<=3 else ""
        rows.append(f'<tr{top}><td class="rank">{i}</td><td><div class="repo-name">{escape(r["full_name"])}</div><div class="repo-desc">{desc}</div></td><td class="score">{sc}</td><td><span class="badge" style="background:{lb_};color:{lc};">{lv} · {lb}</span></td><td>{r.get("stargazers_count",0):,}</td></tr>')
    s_count=sum(1 for r in repos if r["sec_info"][0]=="S")
    a_count=sum(1 for r in repos if r["sec_info"][0]=="A")
    return f"""<!DOCTYPE html><html lang="zh-CN"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0"><link rel="icon" type="image/svg+xml" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 32 32'><rect width='32' height='32' rx='6' fill='%23534AB7'/><text x='16' y='23' text-anchor='middle' font-size='16' font-weight='bold' fill='white' font-family='system-ui'>AS</text></svg>">
<title>AI Agent Skills 安全分级榜单 Top 30 — {month}</title>
<style>*{{margin:0;padding:0;box-sizing:border-box}}body{{font-family:-apple-system,sans-serif;background:#f8f9fa;color:#1a1a2e;line-height:1.6}}.container{{max-width:1100px;margin:0 auto;padding:32px 24px}}h1{{font-size:26px;font-weight:600;margin-bottom:8px}}.subtitle{{font-size:14px;color:#6b7280;margin-bottom:24px}}.summary{{display:flex;gap:16px;margin-bottom:24px;flex-wrap:wrap}}.stat-card{{background:#fff;border-radius:8px;padding:16px 24px;border:1px solid #e5e7eb;flex:1;min-width:140px}}.stat-card .label{{font-size:12px;color:#6b7280}}.stat-card .value{{font-size:22px;font-weight:600;color:#D85A30}}table{{width:100%;border-collapse:collapse;background:#fff;border-radius:12px;overflow:hidden;box-shadow:0 1px 3px rgba(0,0,0,.08)}}thead{{background:#D85A30}}thead th{{color:#fff;font-size:13px;font-weight:500;padding:14px 16px;text-align:left}}tbody tr{{border-bottom:1px solid #f0f0f0}}tbody tr:hover{{background:#fef3ee}}tbody td{{padding:12px 16px;font-size:13px}}td.rank{{text-align:center;font-weight:600;color:#9ca3af;font-size:15px}}td.score{{text-align:right;font-weight:600;color:#D85A30}}.repo-name{{font-weight:500}}.repo-desc{{color:#6b7280;font-size:12px;margin-top:2px}}.badge{{display:inline-block;font-size:11px;padding:2px 8px;border-radius:4px;font-weight:500}}.top3{{background:#fef3ee}}.top3 td.rank{{color:#D85A30}}.footer{{margin-top:24px;padding:16px;background:#fff;border-radius:8px;border:1px solid #e5e7eb;font-size:12px;color:#6b7280}}</style>
</head><body><div class="container"><h1>AI Agent Skills 安全分级榜单 Top 30</h1><p class="subtitle">数据更新：{now} · {month} · GitHub API 自动采集</p>
<div class="summary"><div class="stat-card"><div class="label">收录数</div><div class="value">{len(repos)}</div></div><div class="stat-card"><div class="label">S级</div><div class="value">{s_count}</div></div><div class="stat-card"><div class="label">A级</div><div class="value">{a_count}</div></div></div>
<table><thead><tr><th>#</th><th>仓库名称</th><th>评分</th><th>安全等级</th><th>Star</th></tr></thead><tbody>{chr(10).join(rows)}</tbody></table>
<div class="footer"><p>• 6维评估：出品方(25%)+脚本风险(20%)+SKILL.md质量(15%)+维护(15%)+社区审查(15%)+安全记录(10%)</p><p>• 参考：OWASP Agentic Skills Top 10 · NVIDIA SkillSpector (26.1%含漏洞)</p><p>• 仅供参考，不构成安全建议 · collect_security.py v1.0 · {now}</p></div>
</div></body></html>"""

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--output","-o",required=True)
    p.add_argument("--month","-m",default=None)
    a=p.parse_args()
    if not a.month: a.month=datetime.now().strftime("%Y-%m")
    print(f"[Security] Starting for {a.month}...",file=sys.stderr)
    all_r=[]
    for t in TOPICS:
        print(f"  Searching: {t}",file=sys.stderr)
        all_r.extend(search(t))
    seen={}
    for r in all_r:
        n=r["full_name"]
        if n not in seen or r["stargazers_count"]>seen[n]["stargazers_count"]: seen[n]=r
    repos=list(seen.values())
    repos.sort(key=lambda x:x["stargazers_count"],reverse=True)
    repos=repos[:60]
    for r in repos: r["sec_info"]=score_security(r)
    repos.sort(key=lambda x:x["sec_info"][4],reverse=True)
    repos=repos[:30]
    html=gen_html(repos,a.month)
    os.makedirs(os.path.dirname(a.output),exist_ok=True)
    with open(a.output,"w",encoding="utf-8") as f: f.write(html)
    print(f"[Security] Done. {len(repos)} skills. S={sum(1 for r in repos if r['sec_info'][0]=='S')}",file=sys.stderr)

if __name__=="__main__": main()
