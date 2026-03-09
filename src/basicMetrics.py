"""Basic calculations (daily returns for asset and portfolio, basic summary stats)"""

import pandas as pd

def compute_daily_returns(prices: pd.DataFrame) -> pd.DataFrame:
    """Compute daily returns from price data.
    return[t] = (price[t] / price[t-1]) - 1
    """
    return prices.pct_change().dropna(how = "any")

def compute_portfolio_returns(returns: pd.DataFrame, portfolio_weights: pd.DataFrame) -> pd.Series:
    """Compute daily portfolio returns as weighted sum of asset returns."""
    tickers = portfolio_weights.index.tolist()
    missing = [t for t in tickers if t not in returns.columns] #checks if any tickers in portfolio_weights are missing from returns
    if missing:
        raise RuntimeError(f"Missing return data for tickers: {missing}") #shows which tickers are missing
    w = portfolio_weights.loc[tickers, "weight"].to_numpy(dtype=float) #get weights as numpy array, ensuring order matches returns columns

    #multiply each ticker's return column by its weight and sum across columns to get portfolio return
    portfolio_returns = returns[tickers].mul(w, axis = 1).sum(axis = 1)
    return portfolio_returns

def basic_summary(returns: pd.DataFrame, portfolio_returns: pd.Series, benchmark: str = "SPY") -> dict:
    """Basic summary includes mean, std dev of daily returns + day count"""
    if benchmark not in returns.columns:
        raise RuntimeError(f"Benchmark ticker '{benchmark}' not found in returns data.")
    
    summary = { #Define summary dictionary with basic stats for portfolio and benchmark
        "num_days": int(len(portfolio_returns)),
        "portfolio_mean_daily": float(portfolio_returns.mean()),
        "portfolio_std_daily": float(portfolio_returns.std(ddof=1)),
        "benchmark_mean_daily": float(returns[benchmark].mean()),
        "benchmark_std_daily": float(returns[benchmark].std(ddof=1)),
    }
    return summary