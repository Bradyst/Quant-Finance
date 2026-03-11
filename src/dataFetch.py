"""Data fetching using yfinance"""
import pandas as pd
import yfinance as yf



def fetch_close(tickers, period = "5y"):
    priceDictionary = {}

    for ticker in tickers:
        t = yf.Ticker(ticker)
        hist = t.history(period = period)

        if hist.empty:
            raise RuntimeError(f"No data found for ticker: {ticker}")
        if "Close" not in hist.columns:
            raise RuntimeError(f"'Close' price not found for ticker: {ticker}")
        priceDictionary[ticker] = hist["Close"]
    
    #combine all tickers into one Dataframe, aligning on date index
    prices = pd.DataFrame(priceDictionary)

    #remove timezone
    prices.index = prices.index.tz_localize(None)
    return prices
    
