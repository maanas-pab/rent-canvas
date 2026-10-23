# Rent = Canvas

**What your rent buys, drawn to scale.**

Every white square below is a studio apartment — its area is exactly the
square footage a month of rent buys in that city. New York's $3,400 is a
postage stamp. Cairo's $450 is a full mural. Same medium, wildly different
canvas.

<p align="center">
  <img src="images/wall-3400.png" alt="Gallery wall: what $3,400/mo rents in 16 cities, drawn to scale" width="100%">
</p>

*One $3,400 budget — New York's median studio rent — spent in every city.
Each canvas is true-area scaled: side length grows with √sqft.*

---

## The art

Rent is abstract until you can hang it on a wall. This project treats
monthly rent as a **budget for canvas**: divide the dollars by the local
price per square foot, and you get the size of the blank rectangle you're
paying for. The bigger the rent, the smaller the canvas. The cheaper the
city, the more wall you get.

No photos, no floor plans — just white rectangles on a dark wall, like
works in a gallery. The geometry does the arguing.

| City | Rent | Canvas |
|:-----|-----:|-------:|
| Tokyo | $1,400/mo | 350 sq ft |
| New York | $3,400/mo | 400 sq ft |
| Berlin | $1,300/mo | 591 sq ft |
| Tulsa | $950/mo | 950 sq ft |

<p align="center">
  <img src="images/canvas-new-york.png" width="32%">
  <img src="images/canvas-berlin.png" width="32%">
  <img src="images/canvas-tulsa.png" width="32%">
</p>

<p align="center"><em>New York · Berlin · Tulsa — each at its own local rent.</em></p>

## How it works

```
sqft = monthly_rent_usd / price_per_sqft_usd
side = K × √sqft        # true-area scaling, shared K across every render
```

- **Data** — `data/rents.csv` holds 16 cities: median studio/1-bed asking
  rent in USD and an indicative price per square foot.
- **Render** — `rent_canvas.py` draws each city as a Plotly rectangle on a
  gallery-dark wall. One shared pixel scale (`K`) means every image is
  directly comparable: Tokyo's stamp is a stamp in every frame.
- **Two readings** — the default wall uses *each city's own rent* (what
  locals actually get). Pass `--budget 3400` to hold dollars fixed and
  move cities instead.

## Usage

```bash
pip install -r requirements.txt

python rent_canvas.py                    # ranked table of what rent buys
python rent_canvas.py "New York"         # single canvas in the browser
python rent_canvas.py "Berlin" --budget 3400   # $3,400 spent in Berlin
python rent_canvas.py --wall             # full gallery wall
python rent_canvas.py --export images/   # PNGs (what README uses)
```

The `--export` pass writes one canvas per city plus both walls:

<p align="center">
  <img src="images/wall-local.png" alt="Wall: each city at its own local rent" width="100%">
</p>

*Each city at its own local rent — what a resident actually gets for the
price they pay. Tokyo, paying more than Berlin, gets less than half the canvas.*

## Data & caveats

Figures in `data/rents.csv` are **indicative late-2025 asking rents** for
studios / 1-bedrooms in central-ish neighborhoods, in USD, with rounded
price-per-sqft estimates. They are meant for comparison, not for lease
negotiation. Real rents vary by neighborhood, building, and mood of the
market. Currencies are flattened to USD for a single wall.

## Layout

```
rent_canvas.py       # load → sqft → draw → export (~190 lines)
data/rents.csv       # city, monthly_rent_usd, price_per_sqft_usd
images/              # exported PNGs used in this README
```

## License

MIT
