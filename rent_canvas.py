"""Rent = Canvas. What your monthly rent buys, drawn to scale."""

import argparse
from pathlib import Path
from typing import Optional

import pandas as pd
import plotly.graph_objects as go

DATA = Path(__file__).parent / "data" / "rents.csv"

WALL = "#1a1a1e"
CANVAS = "#f4f2ed"
ACCENT = "#e8c468"    # placard gold — used to flag the dataset's punchlines
VIEW_W, VIEW_H = 1000.0, 720.0
WALL_W = 2400.0  # wall height is computed from the hang itself
# Shared scale: pixels per sqrt(sqft). 1000 sqft -> ~600px mural.
K = 600.0 / (1000.0 ** 0.5)

# Placard geometry on the wall: names + sqft sit in a block right under
# each tier of canvases, so labels never drift away from their art.
PAD, GAP = 30.0, 16.0
LABEL_FONT, SUB_FONT = 13, 11
LABEL_BLOCK = 46.0    # height of a two-line placard
TIER_GAP = 34.0       # vertical air between tiers
MAX_PER_TIER = 16     # wrap to a second row once a tier outgrows this

SHORT = {
    "San Francisco": "S.F.", "Los Angeles": "L.A.", "Mexico City": "MEXICO",
    "New York": "N.Y.C.",
}


def load_rents() -> pd.DataFrame:
    df = pd.read_csv(DATA)
    df["city"] = df["city"].str.strip()
    return df


def affordable_sqft(df: pd.DataFrame, budget: Optional[float] = None) -> pd.Series:
    """Square footage a monthly budget buys in each city.

    With no budget, each city's own median rent is the budget —
    what a local actually gets for the price they pay.
    """
    spend = df["monthly_rent_usd"] if budget is None else budget
    return (spend / df["price_per_sqft_usd"]).round(0)


def canvas_figure(sqft: float, label: str, sublabel: str = "") -> go.Figure:
    """A white rectangle on a dark wall — true-area scaled.

    One shared pixel scale (K) across every render, so a 400 sqft
    New York canvas really is a stamp next to a Tulsa mural.
    """
    side = K * (sqft ** 0.5)  # area-true: side grows with sqrt(sqft)
    x0, y0 = (VIEW_W - side) / 2.0, (VIEW_H - side) / 2.0 + 30

    fig = go.Figure()
    fig.add_shape(
        type="rect", x0=x0, y0=y0, x1=x0 + side, y1=y0 + side,
        fillcolor=CANVAS, line=dict(color="#ffffff", width=2),
    )
    fig.update_xaxes(visible=False, range=[0, VIEW_W], fixedrange=True)
    fig.update_yaxes(visible=False, range=[0, VIEW_H], fixedrange=True,
                     scaleanchor="x", scaleratio=1)
    fig.update_layout(
        width=int(VIEW_W), height=int(VIEW_H),
        plot_bgcolor=WALL, paper_bgcolor=WALL,
        margin=dict(l=40, r=40, t=50, b=60),
        annotations=[dict(
            text=f"<b>{label}</b><br><span style='color:#8a8a93'>{sublabel}</span>",
            x=VIEW_W / 2, y=28, xanchor="center", yanchor="top",
            font=dict(color="#e8e8ee", size=20, family="Georgia, serif"),
            showarrow=False,
        )],
    )
    return fig


def _text_width(text: str, size: float) -> float:
    """Rough upper-case serif width in px — good enough for slot packing."""
    return 0.72 * size * len(text) + 22


def wall_figure(df: pd.DataFrame, budget: Optional[float] = None) -> go.Figure:
    """Every city on one gallery wall, hanging in tiers.

    Sorted cheapest-space to most-space; past MAX_PER_TIER works the
    roster wraps to a second row, like a real gallery hang. Canvases keep
    true relative areas under one shared shrink factor, and every slot is
    at least as wide as its placard, so labels never collide.
    """
    d = df.copy()
    d["sqft"] = affordable_sqft(d, budget)
    d = d.sort_values("sqft").reset_index(drop=True)
    sides = (K * d["sqft"] ** 0.5).tolist()
    names = [SHORT.get(c, c).upper() for c in d.city]
    subs = [f"{s:,.0f} sq ft" for s in d.sqft]
    n = len(d)

    # wrap the roster into two balanced tiers: the break point is where
    # the left/right canvas sums agree, so neither row stops short of
    # the wall. Both rows stay under MAX_PER_TIER.
    tiers = 1 if n <= MAX_PER_TIER else 2
    cum = [0.0]
    for s in sides:
        cum.append(cum[-1] + s)

    def room(k: int) -> float:
        return WALL_W - 2 * PAD - GAP * (k - 1)

    if tiers == 2:
        best = max(
            range(max(1, n - MAX_PER_TIER), min(MAX_PER_TIER, n - 1) + 1),
            key=lambda k: min(room(k) / cum[k],
                              room(n - k) / (cum[n] - cum[k])),
        )
        idx_tiers = [list(range(best)), list(range(best, n))]
    else:
        idx_tiers = [list(range(n))]
    avail = [room(len(t)) for t in idx_tiers]

    name_font, sub_font = LABEL_FONT, SUB_FONT

    def placard(i: int) -> float:
        return max(_text_width(names[i], name_font),
                   _text_width(subs[i], sub_font))

    # step the type down before placards ever get a chance to touch
    while name_font > 9 and any(
        sum(placard(i) for i in t) > a for t, a in zip(idx_tiers, avail)
    ):
        name_font -= 1
        sub_font = max(9, sub_font - 1)

    # one shared shrink factor for every tier, as large as the wall allows
    def fits(f: float) -> bool:
        return all(
            sum(max(sides[i] * f, placard(i)) for i in t) <= a
            for t, a in zip(idx_tiers, avail)
        )

    ratios = [a / sum(sides[i] for i in t) for t, a in zip(idx_tiers, avail)]
    lo, hi = 0.0, 2.0 * max(ratios)  # hi is guaranteed infeasible
    for _ in range(60):
        mid = (lo + hi) / 2.0
        if fits(mid):
            lo = mid
        else:
            hi = mid
    f = lo

    # top-down vertical layout: title, then each tier with its placards
    tier_max = [max(sides[i] for i in t) * f for t in idx_tiers]
    title_block, pad_top, pad_bottom, label_gap = 96.0, 30.0, 26.0, 14.0
    wall_h = pad_top + title_block + pad_bottom + TIER_GAP * (tiers - 1)
    wall_h += sum(m + label_gap + LABEL_BLOCK for m in tier_max)

    fig = go.Figure()
    labels = []
    rail = wall_h - pad_top - title_block  # first tier hangs from here
    for t, m in zip(idx_tiers, tier_max):
        x = PAD
        for i in t:
            side = sides[i] * f
            w = max(side, placard(i))
            cx = x + w / 2.0
            fig.add_shape(
                type="rect",
                x0=cx - side / 2, y0=rail - side, x1=cx + side / 2, y1=rail,
                fillcolor=CANVAS, line=dict(color="#ffffff", width=1.2),
            )
            labels.append(dict(
                x=cx, y=rail - m - label_gap,
                text=f"<b>{names[i]}</b><br><span style='color:#8a8a93;"
                     f"font-size:{sub_font}px'>{subs[i]}</span>",
                showarrow=False, xanchor="center", yanchor="top",
                font=dict(color="#e8e8ee", size=name_font,
                          family="Georgia, serif"),
            ))
            x += w + GAP
        rail -= m + label_gap + LABEL_BLOCK + TIER_GAP

    title = dict(
        text="<b>WHAT RENT BUYS</b><br>"
             "<span style='color:#8a8a93;font-size:17px'>each canvas = the studio your "
             f"{'monthly rent' if budget is None else f'${budget:,.0f} budget'} buys, drawn to scale</span>",
        x=WALL_W / 2, y=wall_h - pad_top, xanchor="center", yanchor="top",
        font=dict(color="#e8e8ee", size=26, family="Georgia, serif"),
        showarrow=False,
    )

    fig.update_xaxes(visible=False, range=[0, WALL_W], fixedrange=True)
    fig.update_yaxes(visible=False, range=[0, wall_h], fixedrange=True)
    fig.update_layout(
        width=int(WALL_W), height=int(wall_h),
        plot_bgcolor=WALL, paper_bgcolor=WALL,
        margin=dict(l=0, r=0, t=0, b=0),
        annotations=[title] + labels,
    )
    return fig


def bar_figure(df: pd.DataFrame, budget: Optional[float] = None) -> go.Figure:
    """Cities ranked by canvas, biggest space at the top.

    Same palette as the walls — white bars on the dark gallery wall,
    New York flagged in gold because it's the punchline of the dataset.
    """
    d = df.assign(sqft=affordable_sqft(df, budget)).sort_values("sqft")
    colors = [ACCENT if c == "New York" else CANVAS for c in d.city]

    fig = go.Figure(go.Bar(
        x=d.sqft, y=d.city, orientation="h",
        marker=dict(color=colors, line=dict(color=WALL, width=1)),
        text=[f"{s:,.0f}" for s in d.sqft],
        textposition="outside", textfont=dict(color="#b9b9c2", size=12),
        hovertemplate="%{y}: %{x:,.0f} sq ft<extra></extra>",
    ))
    fig.update_layout(
        width=1100, height=880,
        plot_bgcolor=WALL, paper_bgcolor=WALL,
        margin=dict(l=140, r=70, t=90, b=60),
        bargap=0.32,
        xaxis=dict(
            title=dict(text="square feet of studio", font=dict(color="#8a8a93", size=13)),
            gridcolor="#2c2c33", zeroline=False, range=[0, d.sqft.max() * 1.12],
            tickfont=dict(color="#8a8a93", size=12),
        ),
        yaxis=dict(
            tickfont=dict(color="#e8e8ee", size=14, family="Georgia, serif"),
            domain=[0.02, 1], automargin=True,
        ),
        annotations=[dict(
            text="<b>WHAT A MONTH OF RENT BUYS</b> &nbsp;— &nbsp;"
                 "<span style='color:#8a8a93;font-size:14px'>studio square footage by city, "
                 "each city's own median rent</span>",
            xref="paper", yref="paper", x=0, y=1.075, xanchor="left", yanchor="top",
            font=dict(color="#e8e8ee", size=21, family="Georgia, serif"),
            showarrow=False,
        )],
    )
    return fig


def export_all(df: pd.DataFrame, out_dir: Path) -> None:
    """Render every city canvas plus gallery walls for the README."""
    out_dir.mkdir(parents=True, exist_ok=True)

    d = df.copy()
    d["sqft"] = affordable_sqft(d)
    for _, row in d.iterrows():
        slug = row.city.lower().replace(" ", "-")
        fig = canvas_figure(
            float(row.sqft), row.city.upper(),
            f"${row.monthly_rent_usd:,.0f}/mo · {row.sqft:,.0f} sq ft",
        )
        fig.write_image(out_dir / f"canvas-{slug}.png")
        print(f"  canvas-{slug}.png")

    wall_figure(d).write_image(out_dir / "wall-local.png")
    print("  wall-local.png")
    # the money shot: one fixed NYC-sized budget, spent everywhere
    wall_figure(d, budget=3400).write_image(out_dir / "wall-3400.png")
    print("  wall-3400.png")
    bar_figure(d).write_image(out_dir / "chart-ranking.png")
    print("  chart-ranking.png")


def main() -> None:
    p = argparse.ArgumentParser(
        description="Draw what monthly rent buys as a canvas, to scale.",
    )
    p.add_argument("city", nargs="?", help="city name (e.g. 'New York')")
    p.add_argument("--budget", type=float, default=None,
                   help="monthly USD budget (default: each city's own rent)")
    p.add_argument("--wall", action="store_true",
                   help="render the full gallery wall")
    p.add_argument("--bars", action="store_true",
                   help="rank every city by the space its rent buys")
    p.add_argument("--export", metavar="DIR", default=None,
                   help="export every city canvas + walls as PNGs")
    args = p.parse_args()

    df = load_rents()

    if args.export:
        export_all(df, Path(args.export))
        return

    if args.wall:
        wall_figure(df, args.budget).show()
        return

    if args.bars:
        bar_figure(df, args.budget).show()
        return

    if args.city:
        match = df[df.city.str.lower() == args.city.lower()]
        if match.empty:
            p.error(f"unknown city {args.city!r}; try: {', '.join(df.city)}")
        row = match.iloc[0]
        sqft = float(affordable_sqft(match, args.budget).iloc[0])
        spend = args.budget if args.budget else row.monthly_rent_usd
        fig = canvas_figure(
            sqft, row.city.upper(),
            f"${spend:,.0f}/mo · {sqft:,.0f} sq ft",
        )
        fig.show()
        return

    out = df.assign(sqft=affordable_sqft(df, args.budget))
    print(out[["city", "monthly_rent_usd", "sqft"]]
          .sort_values("sqft").to_string(index=False))


if __name__ == "__main__":
    main()
