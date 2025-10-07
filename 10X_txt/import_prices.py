import yfinance as yf
import numpy as np
from dateutil.relativedelta import relativedelta
import pandas as pd

def price_on_or_after(series: pd.Series, when: pd.Timestamp) -> float:
    i = series.index.searchsorted(when, side="left")
    return float(series.iloc[i]) if i < len(series) else np.nan

data_df = pd.read_csv("Final Dataset.csv")
data_df["date_a"] = pd.to_datetime(data_df["date_a"])

data_df["start_anchor"] = (data_df["date_a"] + pd.offsets.MonthBegin(1)).dt.normalize()
data_df["end_anchor"]   = data_df["start_anchor"] + pd.offsets.DateOffset(months=18)

spx_start = data_df["start_anchor"].min() - pd.Timedelta(days=5)
spx_end   = data_df["end_anchor"].max()   + pd.Timedelta(days=7)
spx_px = yf.download(
    "^GSPC",
    start=spx_start.date().isoformat(),
    end=spx_end.date().isoformat(),
    auto_adjust=True,      # adjusted OHLC; use "Close"
    progress=False,
    interval="1d",
    group_by="column",
)
spx_series = pd.Series(dtype=float)
if not spx_px.empty:
    spx_price_col = "Adj Close" if "Adj Close" in spx_px.columns else "Close"
    spx_series = spx_px[spx_price_col].dropna().sort_index()

rets = []
spx_rets = []
for ticker, g in data_df.groupby("ticker", sort=False):
    start = g["start_anchor"].min() - pd.Timedelta(days=5)   # small buffer for non-trading starts
    end   = g["end_anchor"].max()   + pd.Timedelta(days=7)   # yf 'end' is exclusive; add buffer

    px = yf.download(
        ticker,
        start=start.date().isoformat(),
        end=end.date().isoformat(),
        auto_adjust=True,       # adjusted OHLC; no "Adj Close" column
        progress=False,
        interval="1d",
        group_by="column",      # keep flat columns
    )

    adj = None
    if not px.empty:
        # No data available -> fill NaNs for all rows of this ticker
        price_col = "Adj Close" if "Adj Close" in px.columns else "Close"
        adj = px[price_col].dropna().sort_index()

    for _, row in g.iterrows():
        # Ticker return
        if adj is None:
            ret = np.nan
        else:
            p0  = price_on_or_after(adj, row["start_anchor"])
            p12m = price_on_or_after(adj, row["end_anchor"])
            ret = np.nan if (pd.isna(p0) or pd.isna(p12m) or p0 == 0) else (p12m / p0 - 1.0)
        rets.append(ret)

        # S&P 500 return (same window)
        if spx_series.empty:
            spx_ret = np.nan
        else:
            sp0  = price_on_or_after(spx_series, row["start_anchor"])
            sp12m = price_on_or_after(spx_series, row["end_anchor"])
            spx_ret = np.nan if (pd.isna(sp0) or pd.isna(sp12m) or sp0 == 0) else (sp12m / sp0 - 1.0)
        spx_rets.append(spx_ret)

data_df["ret_18m_next_month"] = rets
data_df["sp500_ret_18m_next_month"] = spx_rets

data_df["excess_ret_18m_next_month"] = (data_df["ret_18m_next_month"] - data_df["sp500_ret_18m_next_month"])
data_df["len_growth_pct"] = (data_df["len_a"] / data_df["len_b"] - 1)*100

def price_on_or_after(series: pd.Series, when: pd.Timestamp) -> float:
    i = series.index.searchsorted(when, side="left")
    return float(series.iloc[i]) if i < len(series) else np.nan

def price_on_or_before(series: pd.Series, when: pd.Timestamp) -> float:
    i = series.index.searchsorted(when, side="right") - 1
    return float(series.iloc[i]) if i >= 0 else np.nan

# Ensure date_a is datetime
data_df["date_a"] = pd.to_datetime(data_df["date_a"], errors="coerce")

# Start of the 12-month lookback window
data_df["start_12m"] = data_df["date_a"] - pd.offsets.DateOffset(months=12)
# If you prefer fixed days instead of month-aware: 
# data_df["start_12m"] = data_df["date_a"] - pd.Timedelta(days=365)

ret12 = []

for ticker, g in data_df.groupby("ticker", sort=False):
    # Download a single window per ticker covering all needed dates
    dl_start = g["start_12m"].min() - pd.Timedelta(days=7)
    dl_end   = g["date_a"].max()    + pd.Timedelta(days=3)

    px = yf.download(
        ticker,
        start=dl_start.date().isoformat(),
        end=dl_end.date().isoformat(),
        auto_adjust=True,       # adjusted OHLC; use Close
        progress=False,
        interval="1d",
        group_by="column",
    )

    if px.empty:
        ret12.extend([np.nan] * len(g))
        continue

    price_col = "Adj Close" if "Adj Close" in px.columns else "Close"
    adj = px[price_col].dropna().sort_index()

    for _, row in g.iterrows():
        p_start = price_on_or_after(adj, row["start_12m"])
        p_end   = price_on_or_before(adj, row["date_a"])
        r = np.nan if (pd.isna(p_start) or pd.isna(p_end) or p_start == 0) else (p_end / p_start - 1.0)
        ret12.append(r)

data_df["ret_12m_prior_to_10k"] = ret12

data_df.to_csv("Final Dataset.csv", index=False)
print(data_df[["ticker","date_a","start_anchor","end_anchor","ret_18m_next_month","sp500_ret_18m_next_month","excess_ret_18m_next_month", "ret_12m_prior_to_10k"]].head())