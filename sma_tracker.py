import pandas as pd
import yfinance as yf

# 1. Interactive Terminal Input Prompt
ticker_symbol = input("Enter a stock ticker symbol (e.g., AAPL, MRVL, NVDA): ").strip().upper()

if not ticker_symbol:
    print("[Error] Ticker symbol cannot be blank!")
    exit()

print(f"\nFetching market data for {ticker_symbol}...")

try:
    # 2. Extract 2 years of history (Needed for a 200 SMA)
    data = yf.download(ticker_symbol, period="2y")
    
    # Check if we actually got valid stock data back
    if data.empty:
         print(f"[Error] No market data found for ticker '{ticker_symbol}'. Check your spelling.")
         exit()

    # Flatten modern multi-level columns down to single text labels
    data.columns = data.columns.get_level_values(0)

    # 3. Calculate all Moving Averages
    data["20_SMA"] = data["Close"].rolling(window=20).mean()
    data["50_SMA"] = data["Close"].rolling(window=50).mean()
    data["100_SMA"] = data["Close"].rolling(window=100).mean()
    data["200_SMA"] = data["Close"].rolling(window=200).mean()

    # 4. Isolate the most recent session's data row
    columns_to_keep = ["Close", "20_SMA", "50_SMA", "100_SMA", "200_SMA"]
    latest_day = data[columns_to_keep].tail(1).copy()

    # 5. Create a clean display copy and format its cells with '$' strings
    print_df = latest_day.copy()
    for col in columns_to_keep:
        print_df[col] = print_df[col].map(lambda x: f"${x:,.2f}" if pd.notnull(x) else "$0.00")

    # 6. Print formatted results directly to the VS Code terminal
    print("\n========================================================")
    print(f" TECHNICAL MOVING AVERAGES FOR: {ticker_symbol}")
    print("========================================================")
    print(print_df.to_string())
    print("========================================================\n")

except Exception as e:
    print(f"\n[An unexpected error occurred]: {e}")
