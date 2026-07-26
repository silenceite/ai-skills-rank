#!/usr/bin/env python3
"""
AI Skills Rank - 历史趋势图生成器

读取 data/history/stars.csv（每月 Top 50 Star 快照累加），
生成 docs/trends.html：用纯 Python 内联 SVG 折线图展示 Top N skill 的
月度 Star 轨迹。零外部依赖（不依赖 Chart.js / CDN），离线可用。

用法:
  python scripts/build_trend_report.py --output docs/trends.html [--top 15]
"""

import argparse
import csv
import math
import os
import sys
from datetime import datetime
from pathlib import Path

CSV_PATH = Path("data/history/stars.csv")
TOP_N = 15

# 15 个区分度高的颜色（用于折线）
PALETTE = [
    "#534AB7", "#0F6E56", "#D85A30", "#1F6FEB", "#B5179E",
    "#E0A100", "#2A9D8F", "#E63946", "#6A4C93", "#118AB2",
    "#F3722C", "#43AA8B", "#577590", "#9C6644", "#F94144",
]


def load_data(csv_path):
    """读取 CSV，返回 (months, series)。
    months: 排序后的月份列表
    series: {repo: {month: stars}}
    """
    if not csv_path.exists():
        return [], {}
    months = []
    series = {}
    with open(csv_path, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            m = row["month"]
            repo = row["repo"]
            stars = int(row["stars"])
            if m not in months:
                months.append(m)
            series.setdefault(repo, {})[m] = stars
    months.sort()
    return months, series


def fmt_stars(n):
    if n >= 1000:
        v = n / 1000
        return f"{v:.0f}k" if v == int(v) else f"{v:.1f}k"
    return str(n)


def nice_ceil(v):
    if v <= 0:
        return 10
    exp = 10 ** math.floor(math.log10(v))
    f = v / exp
    nf = 1 if f <= 1 else 2 if f <= 2 else 5 if f <= 5 else 10
    return nf * exp


def build_svg(months, top_repos, series):
    """生成内联 SVG 折线图。top_repos: [(repo, latest_stars)] 已按最新月排序。"""
    W, H = 960, 480
    ml, mr, mt, mb = 72, 20, 24, 64
    plot_w = W - ml - mr
    plot_h = H - mt - mb
    n = len(months)

    max_star = max((s for repo, _ in top_repos for s in series[repo].values()), default=1)
    ymax = nice_ceil(max_star * 1.1)

    def x(i):
        if n == 1:
            return ml + plot_w / 2
        return ml + plot_w * i / (n - 1)

    def y(v):
        return mt + plot_h * (1 - v / ymax)

    parts = [f'<svg viewBox="0 0 {W} {H}" width="100%" preserveAspectRatio="xMidYMid meet" '
             f'role="img" aria-label="AI Agent Skills Star 趋势折线图" '
             f'style="font-family:system-ui,-apple-system,sans-serif;">']

    # 背景
    parts.append(f'<rect x="0" y="0" width="{W}" height="{H}" fill="#ffffff"/>')

    # 横向网格线 + Y 轴标签
    ticks = 5
    for i in range(ticks + 1):
        val = ymax * i / ticks
        yy = y(val)
        parts.append(f'<line x1="{ml}" y1="{yy:.1f}" x2="{ml+plot_w}" y2="{yy:.1f}" '
                     f'stroke="#eee" stroke-width="1"/>')
        parts.append(f'<text x="{ml-10}" y="{yy+4:.1f}" text-anchor="end" '
                     f'font-size="11" fill="#6b7280">{fmt_stars(int(val))}</text>')

    # X 轴标签
    for i, m in enumerate(months):
        parts.append(f'<text x="{x(i):.1f}" y="{mt+plot_h+22:.1f}" text-anchor="middle" '
                     f'font-size="12" fill="#374151">{m}</text>')

    # 轴线
    parts.append(f'<line x1="{ml}" y1="{mt}" x2="{ml}" y2="{mt+plot_h}" stroke="#cbd5e1" stroke-width="1"/>')
    parts.append(f'<line x1="{ml}" y1="{mt+plot_h}" x2="{ml+plot_w}" y2="{mt+plot_h}" stroke="#cbd5e1" stroke-width="1"/>')

    # 每条折线
    for idx, (repo, _) in enumerate(top_repos):
        color = PALETTE[idx % len(PALETTE)]
        pts = []
        for i, m in enumerate(months):
            if m in series[repo]:
                pts.append((x(i), y(series[repo][m])))
        if pts:
            poly = " ".join(f"{px:.1f},{py:.1f}" for px, py in pts)
            parts.append(f'<polyline points="{poly}" fill="none" stroke="{color}" '
                         f'stroke-width="2.2" stroke-linejoin="round" stroke-linecap="round"/>')
            for px, py in pts:
                # 跳过极小点也可用同色圆点
                parts.append(f'<circle cx="{px:.1f}" cy="{py:.1f}" r="3.2" fill="{color}" '
                             f'stroke="#fff" stroke-width="1"/>')

    parts.append("</svg>")
    return "\n".join(parts)


def build_legend(top_repos, series, months):
    latest = months[-1]
    items = []
    for idx, (repo, _) in enumerate(top_repos):
        color = PALETTE[idx % len(PALETTE)]
        latest_star = series[repo].get(latest, 0)
        # 首月值（取最早有数据的月份）
        first_val = next((series[repo][m] for m in months if m in series[repo]), 0)
        delta = latest_star - first_val
        arrow = "↑" if delta > 0 else ("↓" if delta < 0 else "–")
        items.append(
            f'<span class="legend-item"><span class="swatch" style="background:{color};"></span>'
            f'<span class="legend-name">{repo}</span>'
            f'<span class="legend-val">{fmt_stars(latest_star)} <span style="color:'
            f'{"#0F6E56" if delta>0 else ("#A32D2D" if delta<0 else "#6b7280")};">'
            f'{arrow}{abs(delta):,}</span></span></span>'
        )
    return "\n".join(items)


def build_table(top_repos, series, months):
    latest = months[-1]
    first = months[0]
    rows = []
    for i, (repo, _) in enumerate(top_repos, 1):
        latest_star = series[repo].get(latest, 0)
        first_val = next((series[repo][m] for m in months if m in series[repo]), 0)
        delta = latest_star - first_val
        if first_val > 0:
            pct = delta / first_val * 100
            change = (f'<span style="color:#0F6E56;">↑ {pct:.0f}%</span>' if pct > 0
                      else f'<span style="color:#A32D2D;">↓ {abs(pct):.0f}%</span>' if pct < 0
                      else "–")
        else:
            change = '<span style="color:#534AB7;">NEW</span>'
        rows.append(
            f"<tr><td class='rank'>{i}</td>"
            f"<td class='repo'>{repo}</td>"
            f"<td class='stars'>{latest_star:,}</td>"
            f"<td class='stars'>{change}</td></tr>"
        )
    return "\n".join(rows)


def generate_html(csv_path, top_n):
    months, series = load_data(csv_path)
    now = datetime.now().strftime("%Y-%m-%d %H:%M")

    if not months:
        return ("<!DOCTYPE html><html lang='zh-CN'><head><meta charset='UTF-8'>"
                "<title>趋势图</title></head><body style='font-family:sans-serif;padding:40px;'>"
                "<h1>暂无历史数据</h1><p>请先运行 collect_star.py 生成至少一个月的 Star 榜单，"
                "历史数据将写入 data/history/stars.csv。</p></body></html>")

    latest = months[-1]
    # Top N by 最新月 Star
    ranked = [(repo, series[repo].get(latest, 0)) for repo in series]
    ranked.sort(key=lambda x: x[1], reverse=True)
    top_repos = ranked[:top_n]

    # 汇总统计
    distinct_repos = len(series)
    latest_total = sum(series[r].get(latest, 0) for r in series)
    max_single = max((s for repo in series for s in series[repo].values()), default=0)
    thin_note = (f"<div class='thin-note'>⚠️ 当前仅 {len(months)} 个月数据"
                 f"（{months[0]} ~ {months[-1]}）。趋势线会随每月自动累积而逐渐丰富，"
                 f"无需人工干预。</div>") if len(months) < 3 else ""

    svg = build_svg(months, top_repos, series)
    legend = build_legend(top_repos, series, months)
    table = build_table(top_repos, series, months)

    html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<meta name="description" content="AI Agent Skills Star 历史趋势图，展示 Top {top_n} skill 的月度 Star 增长轨迹。">
<title>AI Agent Skills Star 趋势图 (Top {top_n})</title>
<style>
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; background: #f8f9fa; color: #1a1a2e; line-height: 1.6; }}
  .container {{ max-width: 1100px; margin: 0 auto; padding: 32px 24px; }}
  h1 {{ font-size: 26px; font-weight: 700; margin-bottom: 6px; }}
  .subtitle {{ font-size: 14px; color: #6b7280; margin-bottom: 24px; }}
  .summary {{ display: flex; gap: 16px; margin-bottom: 24px; flex-wrap: wrap; }}
  .stat-card {{ background: #fff; border-radius: 10px; padding: 18px 24px; border: 1px solid #e5e7eb; flex: 1; min-width: 160px; box-shadow: 0 1px 2px rgba(0,0,0,0.04); }}
  .stat-card .label {{ font-size: 12px; color: #6b7280; margin-bottom: 4px; }}
  .stat-card .value {{ font-size: 24px; font-weight: 700; color: #534AB7; }}
  .chart-card {{ background: #fff; border-radius: 12px; padding: 20px; border: 1px solid #e5e7eb; box-shadow: 0 1px 3px rgba(0,0,0,0.08); margin-bottom: 20px; }}
  .chart-card h2 {{ font-size: 16px; color: #534AB7; margin-bottom: 12px; }}
  .legend {{ display: flex; flex-wrap: wrap; gap: 8px 18px; margin-top: 14px; }}
  .legend-item {{ display: inline-flex; align-items: center; gap: 6px; font-size: 12px; color: #374151; }}
  .swatch {{ width: 12px; height: 12px; border-radius: 3px; display: inline-block; }}
  .legend-name {{ font-weight: 600; }}
  .legend-val {{ color: #6b7280; }}
  .table-wrapper {{ overflow-x: auto; background: #fff; border-radius: 12px; border: 1px solid #e5e7eb; box-shadow: 0 1px 3px rgba(0,0,0,0.08); }}
  table {{ width: 100%; border-collapse: collapse; }}
  thead {{ background: #534AB7; }}
  thead th {{ color: #fff; font-size: 13px; padding: 12px 16px; text-align: left; }}
  thead th:first-child {{ width: 52px; text-align: center; }}
  thead th:nth-child(3), thead th:nth-child(4) {{ text-align: right; }}
  tbody tr {{ border-bottom: 1px solid #f0f0f0; }}
  tbody tr:hover {{ background: #f5f3ff; }}
  tbody td {{ padding: 10px 16px; font-size: 13px; }}
  td.rank {{ text-align: center; font-weight: 700; color: #9ca3af; }}
  td.repo {{ font-weight: 600; }}
  td.stars {{ text-align: right; font-weight: 700; color: #534AB7; white-space: nowrap; }}
  .thin-note {{ background: #FFF8E1; border: 1px solid #FFD54F; border-radius: 10px; padding: 14px 18px; margin-bottom: 20px; font-size: 13px; color: #854F0B; }}
  .footer {{ margin-top: 24px; padding: 20px; background: #fff; border-radius: 10px; border: 1px solid #e5e7eb; font-size: 12px; color: #6b7280; line-height: 1.9; }}
  .footer strong {{ color: #534AB7; }}
  .back-link {{ display: inline-block; margin-bottom: 16px; color: #534AB7; text-decoration: none; font-size: 14px; }}
  .back-link:hover {{ text-decoration: underline; }}
  @media (max-width: 768px) {{
    .container {{ padding: 16px 12px; }}
    h1 {{ font-size: 22px; }}
    .stat-card {{ min-width: 120px; padding: 12px 16px; }}
    .stat-card .value {{ font-size: 18px; }}
  }}
</style>
</head>
<body>
<div class="container">
  <a class="back-link" href="index.html">← 返回首页</a>
  <h1>📈 AI Agent Skills Star 趋势图</h1>
  <p class="subtitle">数据更新：{now} · 追踪月份：{len(months)} 个（{months[0]} ~ {months[-1]}）· Top {top_n} 按最新月 Star 排序</p>

  <div class="summary">
    <div class="stat-card"><div class="label">追踪月份数</div><div class="value">{len(months)}</div></div>
    <div class="stat-card"><div class="label">覆盖 Skill 数</div><div class="value">{distinct_repos}</div></div>
    <div class="stat-card"><div class="label">最新月总 Star</div><div class="value">{latest_total:,}</div></div>
    <div class="stat-card"><div class="label">最高单月 Star</div><div class="value">{max_single:,}</div></div>
  </div>

  {thin_note}

  <div class="chart-card">
    <h2>🔝 Top {top_n} Skill 月度 Star 轨迹</h2>
    {svg}
    <div class="legend">
      {legend}
    </div>
  </div>

  <h2 style="font-size:16px;color:#534AB7;margin:8px 0 12px;">📋 Top {top_n} 当前排名与变动</h2>
  <div class="table-wrapper">
    <table>
      <thead><tr><th>#</th><th>仓库</th><th>最新 Star</th><th>较首月变动</th></tr></thead>
      <tbody>
      {table}
      </tbody>
    </table>
  </div>

  <div class="footer">
    <p><strong>📋 数据说明</strong></p>
    <p>• 数据来源：<code>data/history/stars.csv</code>，由 collect_star.py 每月自动写入（每月 1 号 GitHub Actions 运行后追加）</p>
    <p>• 每个数据点 = 该月 GitHub Star Top 50 榜单中对应仓库的 Star 数快照，非实时值</p>
    <p>• 折线仅连接该 skill 在榜的月份；跌出 Top 50 的月份不显示（非归零）</p>
    <p>• 图表为纯 SVG 渲染，无外部 JavaScript / CDN 依赖，可离线查看</p>
    <p>• 生成时间：{now} · 生成脚本：build_trend_report.py（零外部依赖）</p>
  </div>
</div>
</body>
</html>"""
    return html


def main():
    parser = argparse.ArgumentParser(description="AI Skills 历史趋势图生成器")
    parser.add_argument("--csv", default=str(CSV_PATH), help="历史 CSV 路径")
    parser.add_argument("--output", "-o", required=True, help="输出 HTML 路径")
    parser.add_argument("--top", type=int, default=TOP_N, help="展示 Top N 个 skill")
    args = parser.parse_args()

    html = generate_html(Path(args.csv), args.top)
    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    with open(args.output, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"[Trend Report] Generated: {args.output} (top={args.top})", file=sys.stderr)


if __name__ == "__main__":
    main()
