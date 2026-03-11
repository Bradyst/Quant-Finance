"""Risk metrics for Milestone 2"""

import numpy as np
import pandas as pd

TRADING_DAYS = 252

def annualized_return(portfolio_returns: pd.Series) -> float:
    """ Calculate Annualized return from the mean daily return"""
    return float(portfolio_returns.mean() * TRADING_DAYS)

def annualized_volatility(portfolio_returns: pd.Series) -> float:
    """Calculate annualized volatility from daily standard deviation"""
    return float(portfolio_returns.std(ddof=1) * np.sqrt(TRADING_DAYS))

def sharpe_ratio(portfolio_returns: pd.Series, risk_free_rate: float = 0.035) -> float:
    """Calculate annualized sharpe ratio. risk_free_rate is annualized"""
    annualizedReturn = annualized_return(portfolio_returns)
    annualizedVolatility = annualized_volatility(portfolio_returns)

    if annualizedVolatility == 0:
        return float("nan")
    return float((annualizedReturn - risk_free_rate) / annualizedVolatility)

def correlation_matrix(returns: pd.DataFrame, tickers: list[str]) -> pd.DataFrame:
    """Calculate the Correlation matrix for portfolio asset returns"""
    missing = [t for t in tickers if t not in returns.columns]
    if missing:
        raise ValueError(f"Missing tickers in DataFrame columns: {missing}")

    return returns[tickers].corr()

def covariance_matrix(returns: pd.DataFrame, tickers: list[str]) -> pd.DataFrame:
    """Calculate the Covariance matrix for portfolio asset returns"""
    missing = [t for t in tickers if t not in returns.columns]
    if missing:
        raise ValueError(f"Missing tickers in DataFrame columns: {missing}")

    return returns[tickers].cov()

def asset_volatility(returns: pd.DataFrame, tickers: list[str]) -> pd.Series:
    """Calculate the annualized volatility for each asset in the portfolio"""
    missing = [t for t in tickers if t not in returns.columns]
    if missing:
        raise ValueError(f"Missing tickers in DataFrame columns: {missing}")

    return returns[tickers].std(ddof=1) * np.sqrt(TRADING_DAYS)

def portfolio_risk_summary(
        returns: pd.DataFrame,
        portfolio_returns: pd.Series,
        tickers: list[str],
        risk_free_rate: float = 0.035,
) -> dict:
    """Return a summary of portfolio risk metrics (Milestone 2)"""

    return {
        "annualized_return": annualized_return(portfolio_returns),
        "annualized_volatility": annualized_volatility(portfolio_returns),
        "sharpe_ratio": sharpe_ratio(portfolio_returns, risk_free_rate=risk_free_rate),
        "correlation_matrix": correlation_matrix(returns, tickers),
        "covariance_matrix": covariance_matrix(returns, tickers),
        "asset_volatility": asset_volatility(returns, tickers),
    }