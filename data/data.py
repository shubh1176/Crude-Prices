"""
India Fuel Price Transmission Study — Data Fetcher
Run this on YOUR local machine.
"""

import requests
import pandas as pd
from bs4 import BeautifulSoup
from io import BytesIO
import os, time, re

os.makedirs("data", exist_ok=True)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,*/*;q=0.8",
    "Referer": "https://www.petroldieselprice.com/",
}

# ─────────────────────────────────────────────
# 1. FUEL PRICES
# ─────────────────────────────────────────────

def scrape_fuel(fuel_type, city="New-Delhi", state="Delhi"):
    url = (f"https://www.petroldieselprice.com/{fuel_type}-price-previous-"
           f"historical-trend-chart-in-{city}/{state}")
    print(f"  Fetching {fuel_type} prices...")
    r = requests.get(url, headers=HEADERS, timeout=15)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")
    table = soup.find("table")
    rows = []
    for tr in table.find_all("tr")[1:]:
        cols = [td.get_text(strip=True) for td in tr.find_all("td")]
        if len(cols) >= 4:
            price_clean = re.sub(r"[₹,\s]", "", cols[3])
            try:
                rows.append({"date": cols[2], "price": float(price_clean)})
            except ValueError:
                pass
    df = pd.DataFrame(rows)
    df["date"] = pd.to_datetime(df["date"], format="%d %b %y", errors="coerce")
    df = df.dropna(subset=["date"]).sort_values("date").reset_index(drop=True)
    return df.rename(columns={"price": f"{fuel_type}_inr_delhi"})

print("1. Scraping Delhi fuel prices...")
petrol = scrape_fuel("petrol")
time.sleep(2)
diesel = scrape_fuel("diesel")
petrol.to_csv("data/petrol_delhi.csv", index=False)
diesel.to_csv("data/diesel_delhi.csv", index=False)
print(f"   ✓ Petrol: {len(petrol)} rows | Diesel: {len(diesel)} rows")

# ─────────────────────────────────────────────
# 2. BRENT CRUDE — World Bank (fixed parser)
# ─────────────────────────────────────────────

print("2. Fetching World Bank Brent crude prices...")
WB_URL = ("https://thedocs.worldbank.org/en/doc/"
          "18675f1d1639c7a34d463f59263ba0a2-0050012025/related/"
          "CMO-Historical-Data-Monthly.xlsx")

r = requests.get(WB_URL, headers={"User-Agent": HEADERS["User-Agent"]}, timeout=30)
r.raise_for_status()

# Row 4 (0-indexed) is the header, row 5 is units — skip both, use row 4 as header
df_raw = pd.read_excel(BytesIO(r.content), sheet_name="Monthly Prices", header=4)

# Drop the units row (first row after header)
df_raw = df_raw.iloc[1:].reset_index(drop=True)

# Rename first column to 'period', find Brent
df_raw.rename(columns={df_raw.columns[0]: "period"}, inplace=True)
brent_col = next((c for c in df_raw.columns if "Brent" in str(c)), None)
print(f"   Using column: '{brent_col}'")

crude = df_raw[["period", brent_col]].copy()
crude.columns = ["period", "brent_usd"]
crude = crude.dropna(subset=["period"])

# Parse "1960M01" format → datetime
crude["date"] = pd.to_datetime(
    crude["period"].astype(str).str.replace("M", "-", regex=False),
    format="%Y-%m", errors="coerce"
)
crude["brent_usd"] = pd.to_numeric(crude["brent_usd"], errors="coerce")
crude = crude.dropna(subset=["date", "brent_usd"]).sort_values("date")
crude = crude[crude["date"] >= "2014-01-01"][["date", "brent_usd"]].reset_index(drop=True)

crude.to_csv("data/crude_brent.csv", index=False)
print(f"   ✓ Brent crude: {len(crude)} rows "
      f"({crude['date'].min().date()} → {crude['date'].max().date()})")

# ─────────────────────────────────────────────
# 3. INR/USD — World Bank API
# ─────────────────────────────────────────────

print("3. Fetching INR/USD exchange rate...")
FX_URL = ("https://api.worldbank.org/v2/country/IN/indicator/"
          "PA.NUS.FCRF?format=json&per_page=30&mrv=20")
r = requests.get(FX_URL, timeout=15)
records = r.json()[1]
fx = pd.DataFrame([
    {"date": rec["date"], "inr_per_usd": rec["value"]}
    for rec in records if rec["value"]
])
fx["date"] = pd.to_datetime(fx["date"], format="%Y")
fx = fx.sort_values("date").set_index("date")
fx_monthly = fx.resample("MS").interpolate("linear").reset_index()
fx_monthly.to_csv("data/inrusd.csv", index=False)
print(f"   ✓ INR/USD: {len(fx_monthly)} monthly rows")

# ─────────────────────────────────────────────
# 4. MERGE
# ─────────────────────────────────────────────

print("4. Merging to monthly frequency...")

def to_monthly(df, val_col):
    df = df.copy()
    df["date"] = pd.to_datetime(df["date"]).dt.to_period("M").dt.to_timestamp()
    return df.groupby("date")[val_col].mean().reset_index()

p_m = to_monthly(petrol,     "petrol_inr_delhi")
d_m = to_monthly(diesel,     "diesel_inr_delhi")
c_m = to_monthly(crude,      "brent_usd")
f_m = to_monthly(fx_monthly, "inr_per_usd")

merged = (p_m
          .merge(d_m, on="date", how="outer")
          .merge(c_m, on="date", how="left")
          .merge(f_m, on="date", how="left"))

merged["crude_inr_per_barrel"] = merged["brent_usd"] * merged["inr_per_usd"]
merged = merged.sort_values("date").reset_index(drop=True)
merged.to_csv("data/merged.csv", index=False)

print("\n✅ All done! Files saved in ./data/")
print(f"   merged.csv  →  {merged.shape[0]} rows × {merged.shape[1]} cols")
print(f"   Date range  :  {merged['date'].min().date()} → {merged['date'].max().date()}")
print(f"   Brent NaNs  :  {merged['brent_usd'].isna().sum()} / {len(merged)}")
print("\nPreview (last 6 rows):")
print(merged.tail(6).to_string(index=False))