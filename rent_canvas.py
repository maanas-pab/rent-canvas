"""Rent = Canvas. What your monthly rent buys, drawn to scale."""

import argparse
from pathlib import Path
from typing import Optional

import pandas as pd
import plotly.graph_objects as go

DATA = Path(__file__).parent / "data" / "rents.csv"

WALL = "#1a1a1e"
CANVAS = "#f4f2ed"
VIEW_W, VIEW_H = 1000.0, 720.0
WALL_W, WALL_H = 1600.0, 440.0
# Shared scale: pixels per sqrt(sqft). 1000 sqft -> ~600px mural.
K = 600.0 / (1000.0 ** 0.5)

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


def wall_figure(df: pd.DataFrame, budget: Optional[float] = None) -> go.Figure:
    """Every city on one gallery wall, sharing a baseline.

    Sorted cheapest-space to most-space. Canvases keep true relative
    areas, scaled down to fit the wall.
    """
    d = df.copy()
    d["sqft"] = affordable_sqft(d, budget)
    d = d.sort_values("sqft").reset_index(drop=True)

    sides = K * d["sqft"] ** 0.5
    gap = 26.0
    pad = 48.0
    natural = sides.sum() + gap * (len(d) - 1) + 2 * pad
    fit = WALL_W / natural  # squeeze the whole hang to wall width
    sides, gap = sides * fit, gap * fit

    fig = go.Figure()
    x = pad * fit
    rail = 300.0  # canvases hang from this line (plotly y grows up)
    labels = []
    for (_, row), side in zip(d.iterrows(), sides):
        fig.add_shape(
            type="rect",
            x0=x, y0=rail - side, x1=x + side, y1=rail,
            fillcolor=CANVAS, line=dict(color="#ffffff", width=1.2),
        )
        name = SHORT.get(row.city, row.city).upper()
        labels.append(dict(
            x=x + side / 2, y=rail - max(sides) - 22,
            text=f"<b>{name}</b><br>"
                 f"<span style='color:#8a8a93'>{row.sqft:,.0f} sq ft</span>",
            showarrow=False, xanchor="center", yanchor="top",
            font=dict(color="#e8e8ee", size=12, family="Georgia, serif"),
        ))
        x += side + gap

    title = dict(
        text="<b>WHAT RENT BUYS</b><br>"
             "<span style='color:#8a8a93'>each canvas = the studio your "
             f"{'monthly rent' if budget is None else f'${budget:,.0f} budget'} buys, drawn to scale</span>",
        x=WALL_W / 2, y=WALL_H - 12, xanchor="center", yanchor="top",
        font=dict(color="#e8e8ee", size=26, family="Georgia, serif"),
        showarrow=False,
    )

    fig.update_xaxes(visible=False, range=[0, WALL_W], fixedrange=True)
    fig.update_yaxes(visible=False, range=[0, WALL_H], fixedrange=True)
    fig.update_layout(
        width=WALL_W, height=WALL_H,
        plot_bgcolor=WALL, paper_bgcolor=WALL,
        margin=dict(l=0, r=0, t=0, b=0),
        annotations=[title] + labels,
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


def main() -> None:
    p = argparse.ArgumentParser(
        description="Draw what monthly rent buys as a canvas, to scale.",
    )
    p.add_argument("city", nargs="?", help="city name (e.g. 'New York')")
    p.add_argument("--budget", type=float, default=None,
                   help="monthly USD budget (default: each city's own rent)")
    p.add_argument("--wall", action="store_true",
                   help="render the full gallery wall")
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
