"""User input + validation """
import pandas as pd

def parse_csv(s: str):
    """Parse a CSV string into a DataFrame."""
    return[x.strip() for x in s.split(",") if x.strip()]

def normalize_weights(df: pd.DataFrame) -> pd.DataFrame:
    """Ensure weights are positive and sum to 1."""
    if (df["weight"] <= 0).any():
        raise ValueError("Weights must be positive.")
    total = df["weight"].sum()
    df["weight"] = df["weight"] / total
    return df

def validate_tickers(tickers):
    """Uppercase and validate tickers. Reject empty lists."""
    cleaned = []
    for t in tickers:
        t = t.upper().strip()
        if t:
            cleaned.append(t)
    if len(cleaned) < 1:
        raise ValueError("At least one valid ticker must be entered.")
    return cleaned
def prompt_portfolio():
    """Prompt user for tickers, mode, weights, shares, and period """

    print("Enter portfolio tickers and either weights OR shares.\n")

    tickers = validate_tickers(parse_csv(input("Tickers (comma-separated, e.g. AAPL,MSFT,TSLA): ")))
    mode = input("Input mode? Type 'w' for weights or 's' for shares [w/s]: ").strip().lower()
    if mode not in("w","s"):
        raise ValueError("Invalid mode. Please enter 'w' for weights or 's' for shares.")
    
    if mode == "w":
        #user inputs weights directly
        weights = [float(x) for x in parse_csv(input("Weights (comma-separated, e.g. 0.5,0.3,0.2): "))]
        if len(weights) != len(tickers):
            raise ValueError("Number of weights must match number of tickers.")
        #build table and merge duplicate tickers by summing weights
        df = pd.DataFrame({"ticker": tickers, "weight": weights})
        df = df.groupby("ticker", as_index=False)["weight"].sum()

        #Normalize weights to sum to 1
        df = normalize_weights(df)

        #sort by ticker and set index
        portfolio = df.set_index("ticker").sort_index()
    else:
        #user inputs shares directly, so convert to weights based on shares
        shares = [float(x) for x in parse_csv(input("Shares (comma-separated, e.g. 10,20,30): "))]
        if len(shares) != len(tickers):
            raise ValueError("Number of shares must match number of tickers.")
        df = pd.DataFrame({"ticker": tickers, "shares": shares})
        if (df["shares"] <= 0).any():
            raise ValueError("Share counts must be positive.")
        
        #Weight = shares / total shares
        total = df["shares"].sum()
        df["weight"] = df["shares"] / total

        portfolio = df[["ticker", "weight"]].set_index("ticker").sort_index()
    
    #Period input
    period = input("Data period? (e.g. 1y, 3y, 5y, 10y [default=5y]: ").strip() or "5y"
    return portfolio, period
    