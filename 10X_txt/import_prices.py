import yfinance as yf
import numpy as np
from dateutil.relativedelta import relativedelta
import pandas as pd

def price_on_or_after(series: pd.Series, when: pd.Timestamp) -> float:
    """Return the first price on/after 'when' from a Series indexed by trading days."""
    i = series.index.searchsorted(when, side="left")
    return float(series.iloc[i]) if i < len(series) else np.nan

# --- Load your data ---
data_df = pd.read_csv("Final Dataset.csv")
data_df["date_a"] = pd.to_datetime(data_df["date_a"])

# --- Anchor to first day of next month, then +6 months ---
data_df["start_anchor"] = (data_df["date_a"] + pd.offsets.MonthBegin(1)).dt.normalize()
data_df["end_anchor"]   = data_df["start_anchor"] + pd.offsets.DateOffset(months=6)

# --- Download S&P 500 (^GSPC) once for the full window ---
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

# --- Compute 6-month returns per ticker with a single download each ---
rets = []
spx_rets = []
for ticker, g in data_df.groupby("ticker", sort=False):
    # Download one window that covers all needed dates for this ticker
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
            p18m = price_on_or_after(adj, row["end_anchor"])
            ret = np.nan if (pd.isna(p0) or pd.isna(p18m) or p0 == 0) else (p18m / p0 - 1.0)
        rets.append(ret)

        # S&P 500 return (same window)
        if spx_series.empty:
            spx_ret = np.nan
        else:
            sp0  = price_on_or_after(spx_series, row["start_anchor"])
            sp18m = price_on_or_after(spx_series, row["end_anchor"])
            spx_ret = np.nan if (pd.isna(sp0) or pd.isna(sp18m) or sp0 == 0) else (sp18m / sp0 - 1.0)
        spx_rets.append(spx_ret)

data_df["ret_18m_next_month"] = rets
data_df["sp500_ret_18m_next_month"] = spx_rets

data_df["excess_ret_18m_next_month"] = (data_df["ret_18m_next_month"] - data_df["sp500_ret_18m_next_month"])

# Save and quick peek
data_df.to_csv("Final Dataset.csv", index=False)
print(data_df[["ticker","date_a","start_anchor","end_anchor","ret_18m_next_month","sp500_ret_18m_next_month","excess_ret_18m_next_month"]].head())