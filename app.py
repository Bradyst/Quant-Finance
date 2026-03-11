"""Main script

MILESTONE 1 FEATURES:
Prompts user
Download historical data
Clean and align price
Compute daily returns for each asset + benchmark
Compute daily returns for portfolio (weighted sum of asset returns)
Prints a basic summary and saves CSV outputs to data/


MILESTONE 2 FEATURES:
Compute advanced risk metrics:
Annualized return, Annualized volatility, Sharpe ratio, Correlation matrix,
Covariance matrix, Asset volatility

To Run: python app.py
"""

from src.portfolioInput import prompt_portfolio
from src.dataFetch import fetch_close
from src.cleaning import align_and_clean_prices
from src.basicMetrics import (
    compute_daily_returns,
    compute_portfolio_returns,
    basic_summary,
)
from src.ioUtils import ensure_output_dir, save_csv
from src.riskMetrics import portfolio_risk_summary #Milestone 2

#Benchmark ticker used for comparisons
BENCHMARK = "SPY"


def main():
    print(" --- Portfolio Risk Tool ---\n")
    #Step 1: Get user input for portfolio
    #portfolio is a df indexed by ticker with a "weight" column
    portfolio, period = prompt_portfolio()

    #Build list of tickers to fetch (portfolio tickers + benchmark)
    tickers = portfolio.index.tolist()
    allTickers = tickers + [BENCHMARK]

    #Step 2: Fetch historical close price data for all tickers
    print(f"\nFetching historical data (period = {period}) for: {', '.join(allTickers)}")
    prices = fetch_close(allTickers, period = period)

    #Step 3: Clean and align price data (remove rows with missing data for any ticker)
    print("Cleaning and aligning price data...")
    prices_clean = align_and_clean_prices(prices)

    #Step 4: Compute daily returns for each asset (pct_change)
    print("Computing daily returns...")
    returns = compute_daily_returns(prices_clean)

    #Step 5: Compute daily portfolio returns using weights
    print("Computing portfolio returns...")
    portfolio_returns = compute_portfolio_returns(returns, portfolio)

    #Step 6: Print basic summary stats
    stats = basic_summary(returns, portfolio_returns, benchmark = BENCHMARK)

    #Step 7: Compute advanced risk metrics (MILESTONE 2)
    risk_stats = portfolio_risk_summary(
        returns = returns,
        portfolio_returns = portfolio_returns,
        tickers = tickers,
        risk_free_rate = 0.035
    )

    #Save outputs to data/ directory
    ensure_output_dir()
    save_csv(prices_clean, "data/prices_clean.csv")
    save_csv(returns, "data/daily_returns.csv")
    save_csv(portfolio_returns.to_frame("portfolio_return"), "data/portfolio_returns.csv")
    save_csv(portfolio.reset_index(), "data/portfolio_input_clean.csv")
    #Milestone 2 csv:
    save_csv(risk_stats["correlation_matrix"], "data/correlation_matrix.csv")
    save_csv(risk_stats["covariance_matrix"], "data/covariance_matrix.csv")
    save_csv(risk_stats["asset_volatility"].to_frame("annualized_volatility"), "data/asset_volatility.csv")

    # Print summary stats to console
    print("\n --- Portfolio Summary (Milestone 1)---")
    print(f"Valid trading days analyzed: {stats['num_days']}")
    print(f"Portfolio mean daily return: {stats['portfolio_mean_daily']:.6f}")
    print(f"Portfolio daily return std dev: {stats['portfolio_std_daily']:.6f}")
    print(f"{BENCHMARK} mean daily return: {stats['benchmark_mean_daily']:.6f}")
    print(f"{BENCHMARK} daily return std dev: {stats['benchmark_std_daily']:.6f}")

    print("\nSaved Files:")
    print("- Cleaned price data: data/prices_clean.csv")
    print("- Daily returns for all tickers: data/daily_returns.csv")
    print("- Portfolio returns: data/portfolio_returns.csv")
    print("- Portfolio input (cleaned): data/portfolio_input_clean.csv")
    print("\nDone. (Milestone 1)")

    print("\n --- Portfolio Summary (Milestone 2)---")
    print(f"Annualized portfolio return: {risk_stats['annualized_return']:.2%}")
    print(f"Annualized portfolio volatility: {risk_stats['annualized_volatility']:.2%}")
    print(f"Sharpe ratio (rf = 3.5%): {risk_stats['sharpe_ratio']:.4f}")

    print("\nAsset Annualized Volatility:")
    for ticker, vol in risk_stats["asset_volatility"].items():
        print(f"  {ticker}: {vol:.2%}")

    print("\nCorrelation Matrix:")
    print(risk_stats["correlation_matrix"].round(3))

    print("\nSaved Additional Files:")
    print("- Correlation matrix: data/correlation_matrix.csv")
    print("- Covariance matrix: data/covariance_matrix.csv")
    print("- Asset volatility: data/asset_volatility.csv")
    print("\nDone. (Milestone 2)")

if __name__ == "__main__":
    main()



