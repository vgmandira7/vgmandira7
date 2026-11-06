#!/usr/bin/env python3
"""
Busca seus números reais na API do GitHub e gera assets/stats-light.svg e stats-dark.svg
no estilo neo-brutalista.

Uso local:   GITHUB_TOKEN=seu_token GH_USER=vgmandira7 python3 atualizar_stats.py
Sem token:   python3 atualizar_stats.py --placeholder   (gera o painel "aguardando atualização")
No GitHub:   roda sozinho todo dia pelo workflow .github/workflows/stats.yml
"""
import json
import os
import sys
import urllib.request
from collections import defaultdict

from gerar_assets import ASSETS, C, DISPLAY, MONO, THEMES, box, svg, text

USER = os.environ.get("GH_USER", "vgmandira7")

QUERY = """
query($login: String!) {
  user(login: $login) {
    contributionsCollection {
      totalCommitContributions
      totalPullRequestContributions
      totalIssueContributions
      totalPullRequestReviewContributions
      contributionCalendar {
        totalContributions
        weeks { contributionDays { contributionCount } }
      }
    }
    repositories(ownerAffiliations: OWNER, isFork: false, privacy: PUBLIC, first: 100) {
      totalCount
      nodes {
        languages(first: 10, orderBy: {field: SIZE, direction: DESC}) {
          edges { size node { name } }
        }
      }
    }
  }
}
"""


def fetch(token):
    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=json.dumps({"query": QUERY, "variables": {"login": USER}}).encode(),
        headers={"Authorization": f"bearer {token}", "Content-Type": "application/json",
                 "User-Agent": "profile-stats"},
    )
    with urllib.request.urlopen(req, timeout=30) as r:
        payload = json.load(r)
    if "errors" in payload:
        raise SystemExit(f"Erro da API do GitHub: {payload['errors']}")
    u = payload["data"]["user"]
    cc = u["contributionsCollection"]
    weeks = [[d["contributionCount"] for d in w["contributionDays"]]
             for w in cc["contributionCalendar"]["weeks"]]
    sizes = defaultdict(int)
    for repo in u["repositories"]["nodes"]:
        for e in repo["languages"]["edges"]:
            sizes[e["node"]["name"]] += e["size"]
    total = sum(sizes.values()) or 1
    langs = [(n, v / total * 100) for n, v in sorted(sizes.items(), key=lambda kv: -kv[1])]
    return dict(
        commits=cc["totalCommitContributions"],
        prs=cc["totalPullRequestContributions"],
        repos=u["repositories"]["totalCount"],
        active_days=sum(1 for w in weeks for c in w if c > 0),
        total=cc["contributionCalendar"]["totalContributions"],
        weeks=weeks,
        langs=langs,
    )


LANG_COLORS = ["yellow", "sky", "lime", "coral", "orange", "mint"]
HEAT = ["", "yellow", "orange", "coral", "red"]  # nível 0 = vazio


def level(count, mx):
    if count <= 0:
        return 0
    return min(4, 1 + int(3 * (count - 1) / max(1, mx - 1))) if mx > 1 else 1


def render(t, d):
    ink, surface = t["ink"], t["surface"]
    W = 830
    ph = d is None  # placeholder
    b = []

    # ---- linha 1: 4 números ----
    cards = [
        ("COMMITS", "commits" , "sky", "enviados em 12 meses"),
        ("PULL REQUESTS", "prs", "lime", "propostas de código"),
        ("REPOSITÓRIOS", "repos", "yellow", "públicos criados por mim"),
        ("DIAS ATIVOS", "active_days", "pink", "dias com código enviado"),
    ]
    cw, gap, x0, y0, ch = 184, 22, 10, 10, 112
    for i, (label, key, col, cap) in enumerate(cards):
        x = x0 + i * (cw + gap)
        val = "—" if ph else str(d[key])
        b.append(box(x, y0, cw, ch, C[col], ink, sh=6))
        b.append(text(label, 12.5, x + 16, y0 + 28, C["black"], font=MONO))
        b.append(text(val, 54, x + 16, y0 + 80, C["black"], tr=-0.02))
        b.append(text(cap, 11, x + 16, y0 + 100, C["black"], font=MONO))

    # ---- linha 2: mapa de atividade ----
    hy, hh = 158, 196
    b.append(box(10, hy, 810, hh, surface, ink, sh=6))
    b.append(text("ATIVIDADE NOS ÚLTIMOS 12 MESES", 19, 28, hy + 34, ink, tr=-0.01))
    sub = ("aguardando a primeira atualização automática" if ph
           else f"{d['total']} contribuições = commits + pull requests + issues + revisões de código")
    b.append(text(sub, 11.5, 28, hy + 54, ink, font=MONO))

    weeks = [[0] * 7 for _ in range(53)] if ph else d["weeks"]
    mx = max((c for w in weeks for c in w), default=0)
    pitch, cell = 14.5, 11.5
    gx, gy = 28, hy + 70
    for wi, w in enumerate(weeks[-53:]):
        for di, c in enumerate(w):
            lv = level(c, mx)
            x, y = gx + wi * pitch, gy + di * pitch
            if lv == 0:
                b.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="{cell}" height="{cell}" fill="{ink}" opacity="0.12"/>')
            else:
                b.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="{cell}" height="{cell}" fill="{C[HEAT[lv]]}" '
                         f'stroke="{ink}" stroke-width="1.5"/>')
    # legenda
    lx = 820 - 18 - (5 * 18 + 70 + 70)
    ly = hy + hh - 24
    b.append(text("menos", 11, lx, ly + 10, ink, font=MONO))
    px = lx + 46
    for lv in range(5):
        if lv == 0:
            b.append(f'<rect x="{px}" y="{ly}" width="12" height="12" fill="{ink}" opacity="0.12"/>')
        else:
            b.append(f'<rect x="{px}" y="{ly}" width="12" height="12" fill="{C[HEAT[lv]]}" stroke="{ink}" stroke-width="1.5"/>')
        px += 18
    b.append(text("mais", 11, px + 4, ly + 10, ink, font=MONO))

    # ---- linha 3: linguagens ----
    ly0, lh = 378, 150
    b.append(box(10, ly0, 810, lh, surface, ink, sh=6))
    b.append(text("LINGUAGENS MAIS USADAS", 19, 28, ly0 + 34, ink, tr=-0.01))
    langs = [] if ph else d["langs"][:6]
    if ph or not langs:
        b.append(text("aguardando a primeira atualização automática", 11.5, 28, ly0 + 60, ink, font=MONO))
    else:
        tot = sum(p for _, p in langs)
        bx, bw, by = 28, 774, ly0 + 50
        cx = bx
        for i, (name, pct) in enumerate(langs):
            w = bw * pct / tot
            b.append(f'<rect x="{cx:.1f}" y="{by}" width="{w:.1f}" height="26" fill="{C[LANG_COLORS[i % 6]]}" '
                     f'stroke="{ink}" stroke-width="3"/>')
            cx += w
        for i, (name, pct) in enumerate(langs):
            col, row = i % 3, i // 3
            x, y = 28 + col * 258, ly0 + 108 + row * 28
            b.append(f'<rect x="{x}" y="{y - 12}" width="14" height="14" fill="{C[LANG_COLORS[i % 6]]}" '
                     f'stroke="{ink}" stroke-width="2.5"/>')
            b.append(text(f"{name}", 14, x + 24, y, ink, font=MONO))
            b.append(text(f"{pct:.1f}%", 14, x + 236, y, ink, font=MONO, anchor="e"))
    H = ly0 + lh + 16
    return svg(W, H, "".join(b), "Painel de estatísticas do GitHub: commits, pull requests, repositórios, dias ativos, atividade e linguagens")


def write(data):
    for name, t in THEMES.items():
        with open(os.path.join(ASSETS, f"stats-{name}.svg"), "w", encoding="utf-8") as f:
            f.write(render(t, data))


if __name__ == "__main__":
    if "--placeholder" in sys.argv:
        write(None)
        print("Painel 'aguardando atualização' gerado.")
    else:
        token = os.environ.get("GITHUB_TOKEN")
        if not token:
            raise SystemExit("Defina GITHUB_TOKEN (ou use --placeholder).")
        write(fetch(token))
        print("Painel de estatísticas atualizado para", USER)
