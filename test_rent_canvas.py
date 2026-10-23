"""Sanity checks for the rent → canvas math."""

from rent_canvas import affordable_sqft, load_rents


def test_new_york_is_a_postage_stamp():
    df = load_rents()
    nyc = df[df.city == "New York"]
    assert float(affordable_sqft(nyc).iloc[0]) == 400.0  # 3400 / 8.50


def test_tulsa_outranks_new_york():
    df = load_rents()
    sqft = affordable_sqft(df)
    assert sqft[df.city == "Tulsa"].iloc[0] > sqft[df.city == "New York"].iloc[0]


def test_fixed_budget_scales_inversely_with_psf():
    df = load_rents()
    rich = affordable_sqft(df, budget=3400)
    cheap = affordable_sqft(df, budget=1700)
    # rounding to whole sqft can drift by 1
    assert ((rich - cheap * 2).abs() <= 1).all()
