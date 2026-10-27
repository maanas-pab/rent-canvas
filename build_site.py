"""Render the GitHub Pages site for Rent = Canvas.

Reads data/rents.csv, copies the exported PNGs, and writes a static
docs/index.html — the same argument the README makes, told at gallery
scale: hero wall, both charts, and every city's canvas in a grid.

Usage:
    python rent_canvas.py --export images/   # refresh the PNGs first
    python build_site.py                     # writes docs/
"""

import shutil
from pathlib import Path

import pandas as pd

from rent_canvas import affordable_sqft, load_rents

ROOT = Path(__file__).parent
IMAGES = ROOT / "images"
DOCS = ROOT / "docs"

SITE_CSS = """
:root {
  --wall: #1a1a1e;
  --wall-2: #141417;
  --line: #2c2c33;
  --canvas: #f4f2ed;
  --ink: #e8e8ee;
  --muted: #8a8a93;
  --gold: #e8c468;
}
* { box-sizing: border-box; }
body {
  margin: 0;
  background: var(--wall);
  color: var(--ink);
  font-family: Georgia, "Times New Roman", serif;
  line-height: 1.65;
}
.wrap { max-width: 1080px; margin: 0 auto; padding: 0 24px; }
a { color: var(--gold); text-decoration: none; border-bottom: 1px solid #55503c; }
a:hover { border-bottom-color: var(--gold); }
header { padding: 72px 0 8px; text-align: center; }
h1 {
  font-size: clamp(1.6rem, 7vw, 4.2rem);
  letter-spacing: 0.06em;
  margin: 0;
}
.tagline { color: var(--muted); font-style: italic; font-size: 1.15rem; }
.lede { max-width: 46em; margin: 26px auto 0; color: #c9c9d2; }
h2 {
  font-size: 1.5rem;
  letter-spacing: 0.08em;
  margin: 72px 0 8px;
  border-bottom: 1px solid var(--line);
  padding-bottom: 10px;
}
h2 .sub {
  display: block;
  font-size: 0.92rem;
  font-weight: normal;
  font-style: italic;
  color: var(--muted);
  letter-spacing: 0;
  margin-top: 4px;
}
figure { margin: 34px 0; text-align: center; }
figure img { max-width: 100%; height: auto; border: 1px solid var(--line); }
figcaption {
  color: var(--muted);
  font-style: italic;
  font-size: 0.95rem;
  margin: 12px auto 0;
  max-width: 46em;
  text-align: center;
}
.stats {
  display: flex;
  flex-wrap: wrap;
  gap: 16px;
  margin: 34px 0;
}
.stat {
  flex: 1 1 160px;
  background: var(--wall-2);
  border: 1px solid var(--line);
  padding: 18px 20px;
  text-align: center;
}
.stat .n { font-size: 1.9rem; color: var(--gold); }
.stat .l { color: var(--muted); font-size: 0.88rem; font-style: italic; }
pre {
  background: var(--wall-2);
  border: 1px solid var(--line);
  padding: 16px 20px;
  overflow-x: auto;
  color: #c9c9d2;
  font-size: 0.98rem;
}
.grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(240px, 1fr));
  gap: 20px;
  margin-top: 30px;
}
.grid figure { margin: 0; }
.grid img { width: 100%; display: block; }
table {
  border-collapse: collapse;
  margin: 26px 0;
  width: 100%;
  max-width: 560px;
}
th, td { padding: 8px 14px; text-align: left; }
th:last-child, td:last-child { text-align: right; }
th { color: var(--muted); font-weight: normal; font-style: italic; }
tbody tr { border-top: 1px solid var(--line); }
td.num { font-variant-numeric: tabular-nums; }
.note { color: var(--muted); font-size: 0.95rem; max-width: 46em; }
footer {
  margin-top: 80px;
  border-top: 1px solid var(--line);
  padding: 28px 0 48px;
  color: var(--muted);
  font-size: 0.92rem;
  text-align: center;
}
"""


def stat(value: str, label: str) -> str:
    return f'<div class="stat"><div class="n">{value}</div><div class="l">{label}</div></div>'


def figure(src: str, alt: str, caption: str) -> str:
    return (f'<figure><img src="{src}" alt="{alt}" loading="lazy"></figure>'
            f'<figcaption>{caption}</figcaption>')


def build(df: pd.DataFrame) -> str:
    d = df.assign(sqft=affordable_sqft(df))
    psf = d.price_per_sqft_usd
    cheapest = d.loc[psf.idxmin()]
    priciest = d.loc[psf.idxmax()]

    cards = "".join(
        f'<figure><img src="images/canvas-{row.city.lower().replace(" ", "-")}.png" '
        f'alt="{row.city}: {row.sqft:,.0f} sq ft for ${row.monthly_rent_usd:,.0f}/mo" '
        f'loading="lazy"></figure>'
        for row in d.sort_values("sqft", ascending=False).itertuples()
    )

    rows = "".join(
        f"<tr><td>{row.city}</td>"
        f'<td class="num">${row.monthly_rent_usd:,.0f}/mo</td>'
        f'<td class="num">{row.sqft:,.0f} sq ft</td></tr>'
        for row in d.sort_values("sqft", ascending=False).itertuples()
    )

    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Rent = Canvas — what your rent buys, drawn to scale</title>
<meta name="description" content="Monthly rent, treated as a budget for canvas: {len(d)} cities, each studio drawn to scale as a white rectangle on a dark gallery wall.">
<meta property="og:title" content="Rent = Canvas">
<meta property="og:description" content="What your rent buys, drawn to scale — a white canvas on a dark gallery wall.">
<meta property="og:image" content="images/wall-3400.png">
<style>{SITE_CSS}</style>
</head>
<body>
<div class="wrap">

<header>
  <h1>RENT&nbsp;=&nbsp;CANVAS</h1>
  <p class="tagline">What your rent buys, drawn to scale.</p>
  <p class="lede">Every white square on this page is a studio apartment — its
  area is exactly the square footage a month of rent buys in that city.
  New&nbsp;York's&nbsp;$3,400 is a postage stamp. Tulsa's mural takes the wall.
  Same medium, wildly different canvas.</p>
</header>

<figure>
  <img src="images/wall-3400.png" alt="Gallery wall: what $3,400 per month rents in 23 cities, drawn to scale">
</figure>
<figcaption><em>One $3,400 budget — New York's median studio rent —
spent in every city. Side length grows with &radic;sqft, so every canvas is
true-area scaled.</em></figcaption>

<h2>THE ART
  <span class="sub">rent divided by local price per square foot, framed</span>
</h2>
<p class="lede" style="margin-left:0">Rent is abstract until you can hang it on
a wall. This project treats monthly rent as a <strong>budget for canvas</strong>:
divide the dollars by the local price per square foot and you get the size of
the blank rectangle you're paying for. The bigger the rent, the smaller the
canvas. The cheaper the city, the more wall you get. No photos, no floor
plans — just white rectangles on a dark wall. The geometry does the arguing.</p>
<pre>sqft = monthly_rent_usd / price_per_sqft_usd
side = K &times; &radic;sqft        # true-area scaling, shared K across every render</pre>

<div class="stats">
  {stat(f"{len(d)}", "cities on the wall")}
  {stat(f"${priciest.price_per_sqft_usd:.2f}", f"per sq ft — {priciest.city}")}
  {stat(f"${cheapest.price_per_sqft_usd:.2f}", f"per sq ft — {cheapest.city}")}
  {stat(f"{priciest.price_per_sqft_usd / cheapest.price_per_sqft_usd:.0f}&times;", "the spread between them")}
</div>

<h2>BY THE NUMBERS
  <span class="sub">the same data, argued two other ways</span>
</h2>
{figure("images/chart-ranking.png", "Bars ranking every city by the studio square footage its median rent buys",
        "Tulsa hands over 950 sq ft for $950; Paris hands over 281 for $1,350. "
        "New York, flagged gold, pays the most for one of the smallest canvases.")}
{figure("images/chart-scatter.png", "Scatter plot of monthly rent against studio square footage",
        "Bargains float up-left; the expensive trap sits down-right. "
        "The dotted rule is $3/sq ft — everything below it is paying more than that for air.")}

<h2>THE LOCAL WALL
  <span class="sub">each city at its own rent — what residents actually get</span>
</h2>
{figure("images/wall-local.png", "Wall: each city at its own local monthly rent",
        "Tokyo, paying more than Berlin, gets less than half the canvas.")}

<h2>THE GALLERY
  <span class="sub">every canvas, largest to smallest — each labeled with its rent</span>
</h2>
<div class="grid">{cards}</div>

<h2>THE NUMBERS
  <span class="sub">the full roster</span>
</h2>
<table>
  <thead><tr><th>City</th><th>Rent</th><th>Canvas</th></tr></thead>
  <tbody>{rows}</tbody>
</table>

<h2>DATA &amp; CAVEATS</h2>
<p class="note">Figures are indicative late-2025 asking rents for studios /
one-bedrooms in central-ish neighborhoods, in USD, with rounded
price-per-sqft estimates. They are meant for comparison, not for lease
negotiation. Real rents vary by neighborhood, building, and mood of the
market. Currencies are flattened to USD for a single wall.</p>

<footer>
  MIT · built with pandas &amp; Plotly ·
  <a href="https://github.com/maanas-pab/rent-canvas">source on GitHub</a>
</footer>

</div>
</body>
</html>
"""


def main() -> None:
    if not IMAGES.is_dir():
        raise SystemExit("images/ is missing — run: python rent_canvas.py --export images/")

    DOCS.mkdir(exist_ok=True)
    docs_images = DOCS / "images"
    docs_images.mkdir(exist_ok=True)
    for png in sorted(IMAGES.glob("*.png")):
        shutil.copy2(png, docs_images / png.name)

    (DOCS / "index.html").write_text(build(load_rents()), encoding="utf-8")
    # serve it raw: no Jekyll pass to rewrite paths or drop files
    (DOCS / ".nojekyll").touch()
    print(f"wrote docs/index.html + {len(list(docs_images.glob('*.png')))} pngs")


if __name__ == "__main__":
    main()
