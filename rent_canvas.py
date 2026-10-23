"""Rent = Canvas. What your monthly rent buys, drawn to scale."""

from pathlib import Path
from typing import Optional

import pandas as pd

DATA = Path(__file__).parent / "data" / "rents.csv"


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


if __name__ == "__main__":
    df = load_rents()
    df["sqft"] = affordable_sqft(df)
    print(df[["city", "monthly_rent_usd", "sqft"]].to_string(index=False))
