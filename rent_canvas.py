"""Rent = Canvas. What your monthly rent buys, drawn to scale."""

from pathlib import Path
from typing import Optional

import pandas as pd
import plotly.graph_objects as go

DATA = Path(__file__).parent / "data" / "rents.csv"

INK = "#111114"
WALL = "#1a1a1e"
CANVAS = "#f4f2ed"
VIEW_W, VIEW_H = 1000.0, 720.0
# Shared scale: pixels per sqrt(sqft). 1000 sqft -> ~600px mural.
K = 600.0 / (1000.0 ** 0.5)


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


if __name__ == "__main__":
    df = load_rents()
    df["sqft"] = affordable_sqft(df)
    nyc = df[df.city == "New York"].iloc[0]
    fig = canvas_figure(
        nyc.sqft,
        "NEW YORK",
        f"${nyc.monthly_rent_usd:,.0f}/mo · {nyc.sqft:,.0f} sq ft",
    )
    fig.write_image("canvas_nyc.png")
