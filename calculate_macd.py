# calculate_macd.py
import pandas as pd

def calculate_macd(data):
    """Calculate MACD (12,26,9)"""
    ema12 = data["Close"].ewm(span=12, adjust=False).mean()
    ema26 = data["Close"].ewm(span=26, adjust=False).mean()
    
    data = data.copy()  # Avoid modifying original
    data["MACD_Line"] = ema12 - ema26
    data["MACD_Signal"] = data["MACD_Line"].ewm(span=9, adjust=False).mean()
    data["MACD_Hist"] = data["MACD_Line"] - data["MACD_Signal"]
    
    return data