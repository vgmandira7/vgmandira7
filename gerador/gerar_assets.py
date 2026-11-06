#!/usr/bin/env python3
"""
Gera todos os SVGs do perfil (versões clara e escura) e o README.md.

Todo texto é convertido em CURVAS (paths): assim a fonte não depende do
computador de quem abre o perfil. Para mudar textos/cores, edite este arquivo
e rode:   python3 gerar_assets.py
Requer:   pip install fonttools
"""
import math
import os
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
from fontTools.ttLib import TTFont

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.abspath(os.path.join(HERE, ".."))
ASSETS = os.path.join(OUT, "assets")
os.makedirs(ASSETS, exist_ok=True)

# ---------------------------------------------------------------- DADOS ----
USER = "vgmandira7"
PORTFOLIO = "https://SEU-PORTFOLIO.vercel.app"  # <<< TROQUE pelo link real
LINKEDIN = "https://www.linkedin.com/in/vgmandira/"
EMAIL = "vg.mandira@gmail.com"

C = dict(
    black="#0A0A0A", white="#FFFFFF", yellow="#FFE01B", red="#FF2D3A", blue="#1559FF",
    lime="#B8F24E", cyan="#55E8FF", sky="#7AD3FF", orange="#FFB55E", pink="#FFA3A3",
    mint="#5FEAB5", coral="#FF6464",
)

THEMES = {
    "light": dict(ink="#0A0A0A", paper="#F4F4EF", surface="#FFFFFF"),
    "dark": dict(ink="#F4F4EF", paper="#14141A", surface="#1E1E24"),
}

# ---------------------------------------------------------------- FONTES ---
class Font:
    def __init__(self, path):
        self.f = TTFont(path)
        self.gs = self.f.getGlyphSet()
        self.cmap = self.f.getBestCmap()
        self.upm = self.f["head"].unitsPerEm
        self.hmtx = self.f["hmtx"]

    def _glyph(self, ch):
        return self.cmap.get(ord(ch), ".notdef")

    def width(self, text, size, tr=0.0):
        k = size / self.upm
        return sum(self.hmtx[self._glyph(c)][0] * k + tr * size for c in text) - tr * size

    def d(self, text, size, x, y, tr=0.0):
        pen = SVGPathPen(self.gs, ntos=lambda v: f"{v:.1f}".rstrip("0").rstrip("."))
        k = size / self.upm
        cx = x
        for ch in text:
            g = self._glyph(ch)
            if ch != " ":
                self.gs[g].draw(TransformPen(pen, (k, 0, 0, -k, cx, y)))
            cx += self.hmtx[g][0] * k + tr * size
        return pen.getCommands()


DISPLAY = Font(os.path.join(HERE, "fonts", "Poppins-Bold.ttf"))
MONO = Font(os.path.join(HERE, "fonts", "LiberationMono-Bold.ttf"))


def text(s, size, x, y, fill, font=DISPLAY, anchor="s", tr=0.0):
    w = font.width(s, size, tr)
    if anchor == "m":
        x -= w / 2
    elif anchor == "e":
        x -= w
    return f'<path d="{font.d(s, size, x, y, tr)}" fill="{fill}"/>'


# ---------------------------------------------------------------- PRIMITIVAS
def box(x, y, w, h, fill, ink, sh=6, sw=3, shadow=True):
    s = f'<rect x="{x + sh}" y="{y + sh}" width="{w}" height="{h}" fill="{ink}"/>' if shadow else ""
    return s + f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="{fill}" stroke="{ink}" stroke-width="{sw}"/>'


def rot(inner, deg, cx, cy):
    return f'<g transform="rotate({deg} {cx} {cy})">{inner}</g>'


def star(cx, cy, r, fill):
    pts = []
    for i in range(10):
        a = -math.pi / 2 + i * math.pi / 5
        rr = r if i % 2 == 0 else r * 0.42
        pts.append(f"{cx + rr * math.cos(a):.1f},{cy + rr * math.sin(a):.1f}")
    return f'<polygon points="{" ".join(pts)}" fill="{fill}"/>'


def svg(w, h, body, title, defs=""):
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" '
        f'role="img" aria-label="{title}"><title>{title}</title><defs>{defs}</defs>{body}</svg>'
    )


def save(name, theme, content):
    with open(os.path.join(ASSETS, f"{name}-{theme}.svg"), "w", encoding="utf-8") as f:
        f.write(content)


def marquee(w, items, ink, y=0, h=44, speed=60):
    """Faixa preta com texto em loop (animação SMIL — funciona em <img> no GitHub)."""
    size = 17
    unit = []
    x = 0.0
    for it in items:
        unit.append(text(it.upper(), size, x, h / 2 + 6, "#FFFFFF", tr=0.02))
        x += DISPLAY.width(it.upper(), size, 0.02) + 22
        unit.append(star(x + 8, h / 2, 8, C["yellow"]))
        x += 16 + 22
    seq_w = x
    copies = math.ceil(w / seq_w) + 1
    g = "".join(f'<g transform="translate({i * seq_w:.1f} 0)">{"".join(unit)}</g>' for i in range(copies))
    anim = (
        f'<animateTransform attributeName="transform" type="translate" from="0 0" to="-{seq_w:.1f} 0" '
        f'dur="{seq_w / speed:.1f}s" repeatCount="indefinite"/>'
    )
    return (
        f'<rect x="0" y="{y}" width="{w}" height="{h}" fill="{C["black"]}"/>'
        f'<rect x="0" y="{y}" width="{w}" height="{h}" fill="none" stroke="{ink}" stroke-width="3"/>'
        f'<g transform="translate(0 {y})"><g>{g}{anim}</g></g>'
    )


# ---------------------------------------------------------------- BANNER ---
def banner(t):
    ink, paper = t["ink"], t["paper"]
    W, H = 1200, 440
    defs = (
        f'<pattern id="dots" width="24" height="24" patternUnits="userSpaceOnUse">'
        f'<circle cx="2" cy="2" r="1.1" fill="{ink}" opacity="0.2"/></pattern>'
    )
    b = [f'<rect width="{W}" height="{H}" fill="{paper}"/><rect width="{W}" height="{H}" fill="url(#dots)"/>']

    # meio-tom (halftone) de quadrinhos no canto inferior direito
    for i in range(14):
        for j in range(10):
            cx, cy = W - 20 - i * 18, H - 20 - j * 18
            r = max(0.0, 6.5 - (i + j) * 0.38)
            if r > 0.6:
                b.append(f'<circle cx="{cx}" cy="{cy}" r="{r:.1f}" fill="{C["red"]}" opacity="0.55"/>')

    b.append(marquee(W, ["APIs robustas", "Resolução de problemas reais", "Refatoração", "Arquitetura",
                         "Operações de TI", "Back-end", "Mobile"], ink))

    # selo "disponível"
    tag = "DISPONÍVEL PARA NOVAS OPORTUNIDADES"
    tw = DISPLAY.width(tag, 16, 0.01)
    b.append(rot(
        box(60, 84, tw + 56, 38, C["lime"], ink, sh=5)
        + f'<circle cx="80" cy="103" r="6" fill="{C["black"]}"/>'
        + text(tag, 16, 96, 109, C["black"], tr=0.01), -2, 60 + tw / 2, 103))

    # nome
    n1, size = "VITOR GABRIEL", 86
    b.append(text(n1, size, 56, 206, ink, tr=-0.03))
    n2 = "MANDIRA SOARES"
    w2 = DISPLAY.width(n2, size, -0.03)
    b.append(box(60, 222, w2 + 44, 104, C["yellow"], ink, sh=6, sw=4))
    b.append(text(n2, size, 82, 306, C["black"], tr=-0.03))

    # cargo
    role = "DESENVOLVEDOR MOBILE & BACK-END"
    rw = DISPLAY.width(role, 24, 0.0)
    b.append(box(60, 352, rw + 36, 50, C["blue"], ink, sh=5))
    b.append(text(role, 24, 78, 385, "#FFFFFF"))

    # balão de fala (quadrinhos)
    bx, by, bw, bh = 960, 66, 190, 46
    b.append(rot(
        f'<polygon points="{bx + 30},{by + bh - 2} {bx + 14},{by + bh + 26} {bx + 62},{by + bh - 2}" '
        f'fill="{C["white"]}" stroke="{C["black"]}" stroke-width="3" stroke-linejoin="round"/>'
        + f'<rect x="{bx + 5}" y="{by + 5}" width="{bw}" height="{bh}" rx="22" fill="{C["black"]}"/>'
        + f'<rect x="{bx}" y="{by}" width="{bw}" height="{bh}" rx="22" fill="{C["white"]}" stroke="{C["black"]}" stroke-width="3"/>'
        + text("OLÁ, MUNDO!", 20, bx + bw / 2, by + 31, C["black"], anchor="m"), 3, bx + 90, by + 20))

    # terminal
    tx, ty, tw_, th = 850, 140, 310, 262
    lines = [
        (0, [("const ", C["lime"]), ("vitor = {", "#FFFFFF")]),
        (1, [("role: ", C["lime"]), ('"Mobile & Back-End",', C["yellow"])]),
        (1, [("stack: ", C["lime"]), ('["Node", "Expo"],', C["yellow"])]),
        (1, [("db: ", C["lime"]), ('"PostgreSQL",', C["yellow"])]),
        (1, [("mindset: ", C["lime"]), ('"problema real",', C["yellow"])]),
        (1, [("status: ", C["lime"]), ('"construindo...",', C["yellow"])]),
        (0, [("}", "#FFFFFF")]),
    ]
    term = box(tx, ty, tw_, th, C["black"], ink, sh=9, sw=4)
    term += f'<rect x="{tx}" y="{ty}" width="{tw_}" height="38" fill="{C["yellow"]}" stroke="{ink}" stroke-width="4"/>'
    for i, col in enumerate([C["red"], C["white"], C["lime"]]):
        term += f'<rect x="{tx + 14 + i * 22}" y="{ty + 12}" width="14" height="14" fill="{col}" stroke="{C["black"]}" stroke-width="2.5"/>'
    term += text("vitor@dev ~ %", 14, tx + 90, ty + 25, C["black"], font=MONO)
    ly = ty + 74
    for indent, segs in lines:
        x = tx + 18 + indent * 18
        for s, col in segs:
            term += text(s, 14.5, x, ly, col, font=MONO)
            x += MONO.width(s, 14.5)
        ly += 25
    term += (f'<rect x="{tx + 36}" y="{ly - 18}" width="9" height="17" fill="{C["lime"]}">'
             f'<animate attributeName="opacity" values="1;0" dur="1s" calcMode="discrete" repeatCount="indefinite"/></rect>')
    b.append(rot(term, 2, tx + tw_ / 2, ty + th / 2))

    return svg(W, H, "".join(b), "Vitor Gabriel Mandira Soares — Desenvolvedor Mobile e Back-end", defs)


# ---------------------------------------------------------------- SEÇÕES ---
SECTIONS = [
    ("sobre", "01", "SOBRE MIM", "coral"),
    ("stack", "02", "MINHA STACK", "lime"),
    ("projetos", "03", "PROJETOS", "sky"),
    ("numeros", "04", "GITHUB EM NÚMEROS", "orange"),
    ("contato", "05", "BORA CONVERSAR?", "yellow"),
]


def section_header(t, num, title, accent):
    ink = t["ink"]
    W, H = 830, 76
    body = box(6, 8, 56, 56, C[accent], ink, sh=5)
    body += text(num, 24, 34, 45, C["black"], font=MONO, anchor="m")
    body += text(title, 46, 84, 55, ink, tr=-0.02)
    return svg(W, H, body, title)


# ---------------------------------------------------------------- STACK ----
STACK = [
    ("REACT NATIVE", "sky", -1.5), ("NODE.JS", "lime", 1), ("EXPRESS", "yellow", -1),
    ("PYTHON", "orange", 1.5), ("POSTGRESQL", "blue", -1),
    ("DOCKER", "cyan", 1), ("PRISMA", "mint", -1.5), ("TYPESCRIPT", "sky", 1), ("GIT / CI-CD", "pink", -1),
]


def stack(t):
    ink = t["ink"]
    W, cw, ch, gap = 830, 142, 84, 24
    left = 12
    b = []
    for i, (name, col, deg) in enumerate(STACK):
        r, c = divmod(i, 5)
        x, y = left + c * (cw + gap), 16 + r * (ch + 30)
        size = min(17, (cw - 28) / (DISPLAY.width(name, 1, -0.01)))
        fg = "#FFFFFF" if col == "blue" else C["black"]
        card = box(x, y, cw, ch, C[col], ink, sh=6)
        card += text(f"{i + 1:02d}", 13, x + 14, y + 26, fg, font=MONO)
        card += text(name, size, x + 14, y + ch - 16, fg, tr=-0.01)
        b.append(rot(card, deg, x + cw / 2, y + ch / 2))
    H = 16 + 2 * ch + 30 + 24
    return svg(W, H, "".join(b), "Stack: React Native, Node.js, Express, Python, PostgreSQL, Docker, Prisma, TypeScript, Git")


# ---------------------------------------------------------------- CITAÇÃO --
def quote(t):
    ink, surface = t["ink"], t["surface"]
    W, H = 830, 186
    l1 = "“O maior erro que alguém pode cometer é estar sempre"
    l2 = "com medo de cometer um erro.”"
    b = (
        f'<polygon points="78,126 70,172 128,126" fill="{surface}" stroke="{ink}" stroke-width="3" stroke-linejoin="round"/>'
        + box(12, 10, 790, 122, C["yellow"], ink, sh=7, sw=4)
        + text(l1, 23, 36, 56, C["black"], tr=-0.01)
        + text(l2, 23, 36, 88, C["black"], tr=-0.01)
        + text("— ÉMILE ZOLA", 14, 36, 116, C["black"], font=MONO)
    )
    return svg(W, H, b, "O maior erro que alguém pode cometer é estar sempre com medo de cometer um erro. — Émile Zola")


# ---------------------------------------------------------------- PROJETOS -
PROJECTS = [
    # ("precobom", "01", "SISTEMA DE LOGÍSTICA", "PREÇOBOM", "API + app + PWA com GPS em tempo real",
    #  ["Node.js", "PostGIS", "React Native", "PWA"], "yellow", "PRIVADO"),

    ("luna", "01", "EDUCAÇÃO COM IA", "LUNA", "Plataforma educacional com IA para TDAH",
     ["Python", "IA", "API REST", "MongoDB"], "mint", "PÚBLICO"),

    # ("stok", "02", "WMS MOBILE", "STOK", "Contagem e gestão de inventário",
    #  ["React Native", "Expo", "Node.js", "Prisma"], "sky", "PRIVADO"),

    ("barbearia", "02", "AGENDAMENTO", "BARBEARIA", "Agendamento online para barbearias",
     ["React", "Node.js", "Express", "MongoDB"], "coral", "PRIVADO"),

    ("fitvale", "03", "ACADEMIA & TREINOS", "FITVALE", "App de gestão de academias (TCC)",
     ["React Native", "Expo", "PHP", "SQL"], "orange", "TCC"),
]


def project(t, p):
    ink, surface = t["ink"], t["surface"]
    _, num, cat, title, desc, tags, col, status = p
    W, H = 420, 214
    x, y, w, h = 6, 6, 400, 196
    b = box(x, y, w, h, surface, ink, sh=7)
    b += f'<rect x="{x}" y="{y}" width="{w}" height="56" fill="{C[col]}" stroke="{ink}" stroke-width="3"/>'
    label = f"{num} / {cat}"
    lw = MONO.width(label, 12.5)
    b += f'<rect x="{x + 16}" y="{y + 16}" width="{lw + 20}" height="26" fill="{C["black"]}"/>'
    b += text(label, 12.5, x + 26, y + 34, "#FFFFFF", font=MONO)
    b += text(status, 12, x + w - 16, y + 34, C["black"], font=MONO, anchor="e")
    b += text(title, 34, x + 18, y + 108, ink, tr=-0.02)
    b += text(desc, 12.5, x + 18, y + 132, ink, font=MONO)
    tx, ty = x + 18, y + 150
    for tg in tags:
        tw = MONO.width(tg, 12) + 18
        if tx + tw > x + w - 14:
            break
        b += f'<rect x="{tx}" y="{ty}" width="{tw}" height="26" fill="{C[col]}" stroke="{ink}" stroke-width="2.5"/>'
        b += text(tg, 12, tx + 9, ty + 18, C["black"], font=MONO)
        tx += tw + 8
    return svg(W, H, b, f"{title}: {desc}")


# ---------------------------------------------------------------- CONTATO --
def contact(t, label, value, col, kind):
    ink = t["ink"]
    W, H = 270, 120
    b = box(6, 6, 250, 100, C[col], ink, sh=6)
    # seta ↗
    b += (f'<path d="M222 28 L238 28 L238 44 M238 28 L218 48" fill="none" stroke="{C["black"]}" '
          f'stroke-width="4.5" stroke-linecap="square"/>')
    b += text(label, 28, 22, 70, C["black"], tr=-0.01)
    b += text(value, 13, 22, 92, C["black"], font=MONO)
    return svg(W, H, b, f"{label}: {value}")


def footer(t):
    ink = t["ink"]
    W, H = 830, 50
    return svg(W, H, marquee(W, ["Feito na raça", "React + Tailwind", "Café + código", "Mão na massa"], ink, y=3, h=44), "Faixa decorativa")


def build_assets():
    for tn, t in THEMES.items():
        save("banner", tn, banner(t))
        for sid, num, title, acc in SECTIONS:
            save(f"h-{sid}", tn, section_header(t, num, title, acc))
        save("stack", tn, stack(t))
        save("quote", tn, quote(t))
        for p in PROJECTS:
            save(f"proj-{p[0]}", tn, project(t, p))
        save("btn-linkedin", tn, contact(t, "LINKEDIN", "in/vgmandira", "sky", "in"))
        save("btn-github", tn, contact(t, "GITHUB", f"@{USER}", "lime", "gh"))
        save("btn-email", tn, contact(t, "E-MAIL", EMAIL, "yellow", "mail"))
        save("footer", tn, footer(t))




# ---------------------------------------------------------------- README ---
def pic(name, alt, width=None, href=None):
    w = f' width="{width}"' if width else ""
    img = (f'<picture><source media="(prefers-color-scheme: dark)" srcset="assets/{name}-dark.svg">'
           f'<img src="assets/{name}-light.svg" alt="{alt}"{w}></picture>')
    return f'<a href="{href}">{img}</a>' if href else img


proj_links = {
    "precobom": f"{PORTFOLIO}/#projetos", "luna": f"https://github.com/{USER}/Luna",
    "stok": f"{PORTFOLIO}/#projetos", "barbearia": f"https://github.com/{USER}/BarbeariaMandira",
    "fitvale": f"{PORTFOLIO}/#projetos",
}
cards = [pic(f"proj-{p[0]}", f"Projeto {p[3].title()}", 400, proj_links[p[0]]) for p in PROJECTS]
cards_html = "\n".join(cards)

cards_html = "\n".join(cards)

readme = f"""<div align="center">

{pic("banner", "Vitor Gabriel Mandira Soares — Desenvolvedor Mobile e Back-end")}

</div>

<div align="center">

[![Portfólio](https://img.shields.io/badge/PORTF%C3%93LIO-FFE01B?style=for-the-badge&labelColor=0A0A0A&color=FFE01B)]({PORTFOLIO})
[![LinkedIn](https://img.shields.io/badge/LINKEDIN-7AD3FF?style=for-the-badge&labelColor=0A0A0A&color=7AD3FF)]({LINKEDIN})
[![E-mail](https://img.shields.io/badge/E--MAIL-B8F24E?style=for-the-badge&labelColor=0A0A0A&color=B8F24E)](mailto:{EMAIL})

</div>

{pic("h-sobre", "01 — Sobre mim")}

Olá! Eu sou o **Vitor**, tenho 19 anos e sou apaixonado por programação e tecnologia.

Me formei como **Técnico em Desenvolvimento de Sistemas** na ETEC de Registro-SP (integrado ao Ensino Médio, 2024) e hoje curso **Desenvolvimento de Software Multiplataforma na FATEC de Registro**. Antes mesmo do diploma já resolvia problema real com TI, operações e sistemas internos para empresas locais.

Minha praia é a lógica pesada por trás das aplicações: **APIs, arquitetura, refatoração** e entregar tudo isso no celular do usuário.

- 🔭 **Construindo agora:** PreçoBom (logística), Stok (WMS mobile) e Projeto Luna (educação com IA)
- 🌱 **Estudando:** arquitetura de sistemas, Docker e CI/CD
- 💬 **Pode me perguntar sobre:** Node.js, APIs REST, React Native, Prisma e PostgreSQL
- 📍 **Direto de:** Registro, SP

<div align="center">

{pic("quote", "Citação de Émile Zola sobre o medo de errar", 760)}

</div>

{pic("h-stack", "02 — Minha stack")}

<div align="center">

{pic("stack", "React Native, Node.js, Express, Python, PostgreSQL, Docker, Prisma, TypeScript e Git")}

</div>

{pic("h-projetos", "03 — Projetos")}

<div align="center">

{cards_html}

</div>

<p align="center"><sub>Clique em um cartão para abrir o repositório (ou o portfólio, quando o código é privado).</sub></p>

{pic("h-numeros", "04 — GitHub em números")}

<div align="center">

{pic("stats", "Painel com commits, pull requests, repositórios, dias ativos, mapa de atividade e linguagens mais usadas")}

<sub>Atualizado automaticamente todos os dias. “Contribuições” = commits + pull requests + issues + revisões de código.</sub>

</div>

{pic("h-contato", "05 — Bora conversar?")}

<div align="center">

{pic("btn-linkedin", "LinkedIn", 260, LINKEDIN)}
{pic("btn-github", "GitHub", 260, f"https://github.com/{USER}")}
{pic("btn-email", "E-mail", 260, f"mailto:{EMAIL}")}

{pic("footer", "Feito na raça, React + Tailwind, café + código, mão na massa")}

</div>
"""
def build_readme():
    with open(os.path.join(OUT, "README.md"), "w", encoding="utf-8") as f:
        f.write(readme)


if __name__ == "__main__":
    build_assets()
    build_readme()
    print("OK:", len(os.listdir(ASSETS)), "arquivos em", ASSETS)
