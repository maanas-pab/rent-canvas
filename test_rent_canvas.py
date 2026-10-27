"""Sanity checks for the rent → canvas math and the figures around it."""

from rent_canvas import (
    ACCENT,
    CANVAS,
    affordable_sqft,
    bar_figure,
    load_rents,
    scatter_figure,
    wall_figure,
)


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


def test_roster_is_clean():
    df = load_rents()
    assert len(df) == 23
    assert df.city.is_unique
    assert df.country.notna().all() and (df.country.str.len() == 2).all()
    assert (df.monthly_rent_usd > 0).all()
    assert df.price_per_sqft_usd.between(0.3, 12).all()


def test_wall_labels_every_city_plus_a_title():
    df = load_rents()
    labels = [a.text for a in wall_figure(df).layout.annotations]
    assert len(labels) == len(df) + 1
    assert any("WHAT RENT BUYS" in t for t in labels)


def test_bar_chart_ranks_every_city_and_flags_new_york():
    df = load_rents()
    bar = bar_figure(df).data[0]
    cities, sqft = list(bar.y), list(bar.x)
    assert len(cities) == len(df)
    assert sqft == sorted(sqft)  # smallest canvas at the bottom
    colors = list(bar.marker.color)
    assert colors[cities.index("New York")] == ACCENT
    assert set(colors) <= {CANVAS, ACCENT}


def test_scatter_shows_title_and_reference_line():
    fig = scatter_figure(load_rents())
    assert len(fig.data) == 2  # markers + $3/sqft iso-line
    texts = [a.text for a in fig.layout.annotations]
    assert any("THE PRICE OF SPACE" in t for t in texts)
    assert sum("$3 / sq ft" in t for t in texts) == 1
