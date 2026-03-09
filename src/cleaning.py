"""Cleaning and alignment of price time series"""

import pandas as pd

def align_and_clean_prices(prices: pd.DataFrame, max_ffill_days: int = 2) -> pd.DataFrame:
    """Align price data on date index, forward-fill missing values, and drop any remaining NaNs."""
    prices = prices.sort_index()

    #Fill small gaps with forward fill
    prices = prices.ffill(limit=max_ffill_days)

    #Drop any rows with NaN values (ensures tickers are aligned properly)
    prices = prices.dropna(how="any")

    #Basic sanity: ensure we have than enough data points
    if prices.shape[0] < 30:
        raise RuntimeError("Not enough clean observations after alignment (<30 days). Use a longer period.")
    return prices

