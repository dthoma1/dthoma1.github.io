#!/usr/bin/env python3
"""Static site generator for Darby Thomas's portfolio.

Reads content from ~/portfolio-content and emits a finished static site into
the repository root (the directory this file lives in). No framework, no build
tooling required to host — just push to GitHub Pages.
"""
import os, re, shutil
import markdown as md

HERE = os.path.dirname(os.path.abspath(__file__))
CONTENT = os.path.expanduser("~/portfolio-content")
OUT = HERE

# slug -> (Title, [category tokens]) in homepage order
PROJECTS = [
    ("quirk-up-your-workplace", "Quirk up your workplace", ["speaking"]),
    ("sponsors-onboarding", "Sponsors Onboarding", ["product"]),
    ("octocat-keycap", "Octocat Keycap", ["industrial", "brand"]),
    ("github-sponsors-landing-page", "GitHub Sponsors Landing Page", ["product", "brand"]),
    ("tamagotchi", "Tamagotchi", ["illustration"]),
    ("cyberdecks", "Cyberdecks", ["illustration"]),
    ("ink-drawing-series", "Ink Drawing Series", ["illustration"]),
    ("supper-club", "Supper Club", ["brand", "illustration"]),
    ("kitchen-mural", "Kitchen Mural", ["illustration"]),
    ("gartarot", "Gartarot", ["illustration"]),
    ("dispo-cam", "Dispo Cam", ["product", "illustration", "brand"]),
    ("engineering-prints", "Engineering Prints", ["product", "illustration", "brand", "frontend"]),
    ("apple-juicebox-illustration", "Apple Juicebox Illustration", ["illustration", "industrial"]),
    ("iris-smartphone-lens", "Iris Smartphone Lens", ["brand", "illustration"]),
    ("friendly-cargo-theme", "Friendly Cargo Theme", ["brand", "frontend"]),
    ("coop-website", "Coop Website", ["brand", "frontend"]),
    ("fresh-cookie-scent", "Fresh Cookie Scent", ["brand", "illustration"]),
]

CAT_LABELS = {
    "product": "Product design",
    "illustration": "Illustration",
    "brand": "Brand &amp; marketing",
    "industrial": "Industrial design",
    "frontend": "Frontend",
    "speaking": "Speaking",
}

# A saturated, playful accent color per project (for card tints / gradients)
CARD_COLORS = [
    "#ff5c8a", "#7c5cff", "#00c2a8", "#ffb01f", "#ff6a3d", "#3d8bff",
    "#e64bd0", "#28c76f", "#ff477e", "#8a5cff", "#12b5c9", "#ffce1f",
    "#ff7a45", "#5c7cff", "#2ec4b6", "#ff5c8a",
]

# A vivid, playful background color per project page (black text sits on all).
PALETTE = [
    "#ff5b39", "#ffa92e", "#ffd21f", "#b6e02a", "#37d9a0", "#46b6ff",
    "#8f8cff", "#c78cff", "#ff7ab0", "#ff6f61", "#f9c80e", "#7bd389",
    "#4dd0e1", "#b39ddb", "#ff8a5c", "#ea6fb0",
]
INDEX_BG = "#ff5b39"   # homepage signature color (coral red)
INFO_BG = "#8f8cff"    # info page (periwinkle)
PROJECT_BG = "#DBE6EA"
WRITING_BG = "#f7f1e6"  # calm cream for long-form reading
WRITING_INK = "#1c1913"

def ink_for(hexbg):
    """Pick near-black or white text for best contrast on a background."""
    h = hexbg.lstrip("#")
    r, g, b = (int(h[i:i+2], 16) / 255 for i in (0, 2, 4))
    def lin(c):
        return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
    lum = 0.2126 * lin(r) + 0.7152 * lin(g) + 0.0722 * lin(b)
    return "#141210" if lum > 0.16 else "#fbf7ff"

def read(path):
    with open(path, encoding="utf-8") as f:
        return f.read()

def parse_post(path):
    """Parse a writing post with simple --- frontmatter --- (title/date/summary)."""
    raw = read(path)
    meta = {"title": "Untitled", "date": "", "summary": ""}
    body = raw
    if raw.startswith("---"):
        _, fm, body = raw.split("---", 2)
        for line in fm.strip().splitlines():
            if ":" in line:
                k, v = line.split(":", 1)
                meta[k.strip()] = v.strip()
    meta["body"] = body.strip()
    return meta

def fmt_date(s):
    try:
        from datetime import datetime
        return datetime.strptime(s.strip(), "%Y-%m-%d").strftime("%B %-d, %Y")
    except Exception:
        return s

def load_posts():
    wdir = os.path.join(CONTENT, "writing")
    posts = []
    if not os.path.isdir(wdir):
        return posts
    for fn in os.listdir(wdir):
        if fn.endswith(".md"):
            path = os.path.join(wdir, fn)
            meta = parse_post(path)
            meta["slug"] = fn[:-3]
            meta["_mtime"] = os.path.getmtime(path)
            posts.append(meta)
    posts.sort(key=lambda p: (p.get("date", ""), p.get("_mtime", 0)), reverse=True)
    return posts

def find_thumb(slug):
    imgdir = os.path.join(CONTENT, "projects", slug, "images")
    for name in ("thumbnail.jpg", "thumbnail.png", "thumbnail.gif"):
        if os.path.isfile(os.path.join(imgdir, name)):
            return name
    for name in sorted(os.listdir(imgdir)):
        if name.lower().endswith((".jpg", ".png", ".gif", ".jpeg", ".webp")):
            return name
    return None

def body_html(slug):
    """Convert a project README to HTML, stripping the H1 title and the
    Categories line, and rewriting image paths to the site's asset folder."""
    text = read(os.path.join(CONTENT, "projects", slug, "README.md"))
    kept = []
    for ln in text.splitlines():
        if ln.startswith("# ") or ln.startswith("**Categories:**"):
            continue
        kept.append(ln)
    body = "\n".join(kept).strip()
    body = body.replace("](images/", f"](../assets/img/projects/{slug}/")
    body = body.replace('src="images/', f'src="../assets/img/projects/{slug}/')
    htmlout = md.markdown(body, extensions=["extra"])
    # Turn the bare GitHub raw .mp4 URL line into a real local video player
    htmlout = re.sub(
        r"<p>https://github\.com/[^<\s]+/([^/<\s]+\.mp4)</p>",
        lambda m: (f'<video controls loop muted playsinline '
                   f'src="../assets/img/projects/{slug}/{m.group(1)}"></video>'),
        htmlout,
    )
    return htmlout

def head(title, desc, css_path, extra=""):
    asset_prefix = "../" if css_path.startswith("../") else ""
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{title}</title>
  <link rel="icon" href="{asset_prefix}assets/img/favicon.ico">
  <meta name="description" content="{desc}">
  <meta property="og:title" content="{title}">
  <meta property="og:description" content="{desc}">
  <meta property="og:type" content="website">
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Bricolage+Grotesque:opsz,wght@12..96,400..800&family=Instrument+Serif:ital@0;1&family=Inter:wght@400;500;600&display=swap" rel="stylesheet">
  <link rel="stylesheet" href="{css_path}">
  {extra}
</head>"""

def nav(prefix):
    return f"""<header class="site-header">
  <div class="wrap nav">
    <a class="logo" href="{prefix}index.html">Darby&nbsp;Thomas</a>
    <nav class="nav-links">
      <a href="{prefix}index.html">Work</a>
      <a href="{prefix}writing/index.html">Writing</a>
      <a href="{prefix}info.html">Info</a>
    </nav>
  </div>
</header>"""

def footer(prefix):
    return """<footer class="site-footer">
  <div class="wrap footer-inner">
    <span>&copy; Darby Thomas</span>
    <nav class="socials">
      <a href="https://www.linkedin.com/in/darby-thomas-b4ba71265/" target="_blank" rel="noopener">LinkedIn</a>
      <a href="https://twitter.com/ddddarby" target="_blank" rel="noopener">Twitter</a>
      <a href="https://github.com/dthoma1" target="_blank" rel="noopener">GitHub</a>
    </nav>
  </div>
</footer>"""


def build_index():
    filters = [("all", "All")] + [(k, v) for k, v in CAT_LABELS.items()]
    filter_html = "\n".join(
        f'      <button class="chip{" is-active" if k=="all" else ""}" data-filter="{k}">{v}</button>'
        for k, v in filters
    )
    cards = []
    for i, (slug, title, cats) in enumerate(PROJECTS):
        thumb = find_thumb(slug)
        color = PROJECT_BG
        cink = ink_for(color)
        cat_attr = " ".join(cats)
        cat_pills = "".join(f'<span class="pill">{CAT_LABELS[c]}</span>' for c in cats)
        cards.append(f"""      <a class="card" href="projects/{slug}.html" data-cats="{cat_attr}" style="--card-bg:{color}; --card-ink:{cink}">
        <div class="card-media"><img loading="lazy" src="assets/img/projects/{slug}/{thumb}" alt="{title}"></div>
        <div class="card-body">
          <h3 class="card-title">{title}</h3>
          <div class="pills">{cat_pills}</div>
        </div>
      </a>""")
    cards_html = "\n".join(cards)

    # Writing teaser: latest 5 post titles (Brian Lovin style)
    posts = load_posts()[:5]
    teaser_rows = "\n".join(
        f"""        <li><a href="writing/{p['slug']}.html"><span class="t-title">{p['title']}</span><span class="t-date">{fmt_date(p['date'])}</span></a></li>"""
        for p in posts
    )
    writing_teaser = f"""
  <section class="home-writing wrap">
    <div class="section-head">
      <h2 class="section-title">Writing</h2>
      <a class="section-more" href="writing/index.html">All writing &rarr;</a>
    </div>
    <ul class="teaser-list">
{teaser_rows}
    </ul>
  </section>
""" if posts else ""

    page = head("Darby Thomas — Product Designer",
                "Product designer, illustrator, and eclectic creative based in California.",
                "assets/css/style.css") + f"""
<body class="home" style="--page-bg:{INDEX_BG}; --ink:{ink_for(INDEX_BG)}">
<img class="home-corner-flowers" src="assets/img/yellow-flowers.png" alt="" aria-hidden="true">
{nav("")}
<main>
  <section class="hero">
    <div class="wrap hero-inner">
      <p class="eyebrow">Product designer · Illustrator · California</p>
      <h1 class="hero-title">Hi, I'm <span class="grad">Darby</span> — I make playful, useful things.</h1>
      <p class="hero-sub">I'm a product designer, illustrator, and eclectic creative. Currently designing at <strong>GitHub</strong>, previously <strong>Patreon</strong> and <strong>Photojojo</strong>.</p>
    </div>
  </section>
{writing_teaser}
  <section class="work wrap">
    <div class="section-head">
      <h2 class="section-title">Selected work</h2>
    </div>
    <div class="filters">
{filter_html}
    </div>
    <div class="grid" id="grid">
{cards_html}
    </div>
  </section>
</main>
{footer("")}
<script src="assets/js/main.js"></script>
</body>
</html>"""
    with open(os.path.join(OUT, "index.html"), "w", encoding="utf-8") as f:
        f.write(page)


def build_info():
    about = read(os.path.join(CONTENT, "ABOUT.md"))
    about = re.sub(r"^# .*\n", "", about, count=1)
    about_html = md.markdown(about, extensions=["extra"])
    page = head("Info — Darby Thomas", "About Darby Thomas.",
                "assets/css/style.css") + f"""
<body class="tiled-bg" style="--page-bg:{INFO_BG}; --ink:{ink_for(INFO_BG)}">
{nav("")}
<main>
  <section class="info wrap">
    <h1 class="page-title"><span class="grad">Info</span></h1>
    <div class="prose">{about_html}</div>
  </section>
</main>
{footer("")}
</body>
</html>"""
    with open(os.path.join(OUT, "info.html"), "w", encoding="utf-8") as f:
        f.write(page)


def build_projects():
    os.makedirs(os.path.join(OUT, "projects"), exist_ok=True)
    n = len(PROJECTS)
    for i, (slug, title, cats) in enumerate(PROJECTS):
        cat_pills = "".join(f'<span class="pill">{CAT_LABELS[c]}</span>' for c in cats)
        content = body_html(slug)
        nxt = PROJECTS[(i + 1) % n]
        page = head(f"{title} — Darby Thomas", f"{title} — a project by Darby Thomas.",
                    "../assets/css/style.css") + f"""
<body style="--page-bg:{PROJECT_BG}; --ink:{ink_for(PROJECT_BG)}">
{nav("../")}
<main>
  <article class="project wrap">
    <a class="back" href="../index.html">&larr; All work</a>
    <div class="pills">{cat_pills}</div>
    <h1 class="project-title"><span class="grad">{title}</span></h1>
    <div class="prose project-content">
{content}
    </div>
    <a class="next" href="{nxt[0]}.html">Next project: <strong>{nxt[1]}</strong> &rarr;</a>
  </article>
</main>
{footer("../")}
</body>
</html>"""
        with open(os.path.join(OUT, "projects", f"{slug}.html"), "w", encoding="utf-8") as f:
            f.write(page)


def build_writing():
    outdir = os.path.join(OUT, "writing")
    os.makedirs(outdir, exist_ok=True)
    posts = load_posts()

    # Index page
    items = []
    for p in posts:
        items.append(f"""      <a class="post-link" href="{p['slug']}.html">
        <span class="post-date">{fmt_date(p['date'])}</span>
        <h2 class="post-link-title">{p['title']}</h2>
        <p class="post-summary">{p['summary']}</p>
      </a>""")
    items_html = "\n".join(items) if items else '<p class="prose">Nothing here yet — soon.</p>'
    page = head("Writing — Darby Thomas", "Essays and process notes by Darby Thomas.",
                "../assets/css/style.css") + f"""
<body class="reading tiled-bg" style="--page-bg:{WRITING_BG}; --ink:{WRITING_INK}">
{nav("../")}
<main>
  <section class="writing-index wrap">
    <h1 class="page-title">Writing</h1>
    <p class="writing-intro">Process notes, small experiments, and things I'm figuring out as I go.</p>
    <div class="post-list">
{items_html}
    </div>
  </section>
</main>
{footer("../")}
</body>
</html>"""
    with open(os.path.join(outdir, "index.html"), "w", encoding="utf-8") as f:
        f.write(page)

    # Individual posts
    for p in posts:
        post_body = p["body"].replace("](images/", "](../assets/img/writing/")
        body_md = md.markdown(post_body, extensions=["extra"])
        page = head(f"{p['title']} — Darby Thomas", p["summary"],
                    "../assets/css/style.css") + f"""
<body class="reading tiled-bg article-page" style="--page-bg:{WRITING_BG}; --ink:{WRITING_INK}">
{nav("../")}
<main>
  <article class="post wrap">
    <a class="back" href="index.html">&larr; All writing</a>
    <span class="post-date">{fmt_date(p['date'])}</span>
    <h1 class="post-title">{p['title']}</h1>
    <div class="prose post-body">
{body_md}
    </div>
  </article>
</main>
{footer("../")}
</body>
</html>"""
        with open(os.path.join(outdir, f"{p['slug']}.html"), "w", encoding="utf-8") as f:
            f.write(page)


def copy_assets():
    dst = os.path.join(OUT, "assets", "img", "projects")
    if os.path.isdir(dst):
        shutil.rmtree(dst)
    for slug, _, _ in PROJECTS:
        src = os.path.join(CONTENT, "projects", slug, "images")
        shutil.copytree(src, os.path.join(dst, slug))

    writing_src = os.path.join(CONTENT, "writing", "images")
    writing_dst = os.path.join(OUT, "assets", "img", "writing")
    if os.path.isdir(writing_dst):
        shutil.rmtree(writing_dst)
    if os.path.isdir(writing_src):
        shutil.copytree(writing_src, writing_dst)


def main():
    os.makedirs(os.path.join(OUT, "assets", "css"), exist_ok=True)
    os.makedirs(os.path.join(OUT, "assets", "js"), exist_ok=True)
    copy_assets()
    build_index()
    build_info()
    build_projects()
    build_writing()
    print("Built site into", OUT)


if __name__ == "__main__":
    main()
