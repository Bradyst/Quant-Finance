"""Simple I/O helpers
Saves CSV outputs
"""
import os
import pandas as pd

def ensure_output_dir():
    """Ensure output directory exists and if not creates it."""
    os.makedirs("data",exist_ok=True)

def save_csv(df: pd.DataFrame, path: str):
    """Save DataFrame to CSV."""
    df.to_csv(path,index=True)