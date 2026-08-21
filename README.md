# Olist Dashboard

## Run
```bash
cd olist_dashboard
pip install -r requirements.txt
streamlit run home.py
```

## Populating the data
`EXPORT_CELLS.md` has the export cells to paste into each of the 5 notebooks.
Paste each one at the bottom of its notebook and run it — CSVs get written under `data/`.

Any section without a CSV just shows a placeholder message; the rest of the app works normally.

## Screens
Every screen follows the same order: problem definition -> findings (diagnosis) -> action items.

- **Revenue** — month-end pacing (headline), 7-day forecast + interval, performance by horizon, feature importance, by region
- **Customers** — radar/PCA/map, engagement vs. repeat purchase, Delivery-Disappointed segment, voucher effect
- **Products & Delivery** — funnel bottlenecks, regional gaps, category comparison, weight vs. delay, SLA table
