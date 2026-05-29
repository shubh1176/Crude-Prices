# Crude Prices & Indian Fuel Pass-Through

An empirical analysis of how international crude oil prices transmit to retail petrol and diesel prices in India.

## Background

India is the world's third-largest oil consumer, importing over 85% of its crude oil requirements. Despite this heavy import dependence, the pass-through from global crude prices to domestic retail fuel prices is neither automatic nor symmetric. In India, petrol and diesel retail prices are determined by oil marketing companies (OMCs) — IOCL, BPCL, HPCL — and are influenced by:

- **Crude oil cost** (Brent USD/barrel)
- **Exchange rates** (INR/USD)
- **Excise duty & VAT** (central and state taxes)
- **Dealer commissions & transportation costs**
- **Political considerations** (price revisions are often delayed before elections)

Since the deregulation of petrol (2010) and diesel (2014), OMCs are theoretically free to set prices daily. In practice, prices change infrequently and in irregular increments, raising questions about the speed and symmetry of pass-through.

## What This Analysis Does

This project scrapes historical data and runs econometric tests to quantify:

1. **Correlation structure** — How do retail prices co-move with crude prices at different lags?
2. **Stationarity** — Are the price series mean-reverting or random walk-like?
3. **Asymmetric pass-through (Houck decomposition)** — Do retail prices respond differently when crude rises vs. when it falls?

### Data Sources

| Variable | Source |
|---|---|
| Petrol price (₹/L), Delhi | [petroldieselprice.com](https://www.petroldieselprice.com/) |
| Diesel price (₹/L), Delhi | Same as above |
| Brent crude ($/bbl) | World Bank Commodity Price Data |
| INR/USD exchange rate | World Bank API |

## Key Findings

- **Diesel** shows borderline statistically significant asymmetry (Wald p=0.052): retail prices fall more sharply when crude drops than they rise when crude increases.
- **Petrol** shows no statistically significant asymmetry (Wald p=0.685).
- Both pass-through models have very low explanatory power (R² < 8%), meaning crude price changes alone explain little of the variation in retail price changes — taxes and administered pricing dominate.
- Both retail price series are non-stationary (ADF test), consistent with a random-walk-like pricing process with occasional discrete jumps.

## Repository Structure

```
├── data/
│   ├── data.py                 # Data fetching & merging script
│   ├── petrol_delhi.csv        # Scraped petrol prices
│   ├── diesel_delhi.csv        # Scraped diesel prices
│   ├── crude_brent.csv         # Brent crude prices (World Bank)
│   ├── inrusd.csv              # INR/USD exchange rates (World Bank)
│   └── merged.csv              # Final merged panel dataset
├── notebooks/
│   └── analysis.ipynb          # Main analysis notebook
├── requirements.txt
└── README.md
```
