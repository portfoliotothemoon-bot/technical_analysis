import pandas as pd
import yfinance as yf

# 1. Interactive Terminal Input Prompt
ticker_symbol = input("Enter a stock ticker symbol (e.g., AAPL, MRVL, NVDA): ").strip().upper()

if not ticker_symbol:
    print("[Error] Ticker symbol cannot be blank!")
    exit()

print(f"\nFetching institutional market data for {ticker_symbol}...")

try:
    # 2. Extract 2 years of history
    data = yf.download(ticker_symbol, period="2y")
    
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
    
    # Calculate Volume Averages (1-Month vs. 3-Month Macro Framework)
    data["Volume_20_MA"] = data["Volume"].rolling(window=20).mean()   # 1 Month
    data["Volume_63_MA"] = data["Volume"].rolling(window=63).mean()   # 3 Months

    # 4. Isolate recent rows for multi-day calculation sweeps
    latest_3_days = data.tail(3)
    latest_row = latest_3_days.tail(1)
    
    # Current Single-Session Metrics
    current_close = float(latest_row["Close"].iloc)
    current_volume = float(latest_row["Volume"].iloc)
    avg_volume_1m = float(latest_row["Volume_20_MA"].iloc)
    avg_volume_3m = float(latest_row["Volume_63_MA"].iloc)
    
    sma20 = float(latest_row["20_SMA"].iloc)
    sma50 = float(latest_row["50_SMA"].iloc)
    sma100 = float(latest_row["100_SMA"].iloc)
    sma200 = float(latest_row["200_SMA"].iloc)

    # 5. Create a clean display copy and format its cells with '$' strings for printing
    columns_to_keep = ["Close", "20_SMA", "50_SMA", "100_SMA", "200_SMA"]
    print_df = latest_row[columns_to_keep].copy()
    for col in columns_to_keep:
        print_df[col] = print_df[col].map(lambda x: f"${x:,.2f}" if pd.notnull(x) else "$0.00")

    # 6. Print formatted metrics table
    print("\n========================================================")
    print(f" EXPERT TECHNICAL MONITOR FOR: {ticker_symbol}")
    print("========================================================")
    print(print_df.to_string(index=False))
    print("========================================================")
    print(f" Daily Volume : {current_volume:,.0f}")
    print(f" 1-Month Avg  : {avg_volume_1m:,.0f} (20-day window)")
    print(f" 3-Month Avg  : {avg_volume_3m:,.0f} (63-day window)")
    print("--------------------------------------------------------")
    print(" ENHANCED INSIGHT ALERTS:")
    print("--------------------------------------------------------")
    
    # --- ENHANCEMENT 1: The 3-Day Structural Breakout Rule ---
    below_20_3d = all(latest_3_days["Close"] < latest_3_days["20_SMA"])
    above_20_3d = all(latest_3_days["Close"] > latest_3_days["20_SMA"])
    
    if below_20_3d:
        print(" [!] CONFIRMED SHORT-TERM DOWNTURN: Price has closed BELOW its 20 SMA for 3 consecutive days.")
    elif above_20_3d:
        print(" [^] CONFIRMED SHORT-TERM UPTREND: Price has closed ABOVE its 20 SMA for 3 consecutive days.")
    else:
        print(" [-] CHOPPY DRIFT: Price is crossing back and forth over the 20 SMA window.")

    # --- ENHANCEMENT 2: Upgraded Volume Support Filter ---
    # Compare current session volume against the macro 3-month baseline to detect real interest
    volume_surge_macro = current_volume > (avg_volume_3m * 1.5)
    
    if current_close > sma50 and latest_3_days["Close"].iloc[-2] < latest_3_days["50_SMA"].iloc[-2]:
        if volume_surge_macro:
            print(" [^] VALID BULLISH BREAKOUT: Passed above 50 SMA supported by massive 3-month macro volume surge.")
        else:
            print(" [!] WEAK BREAKOUT WARNING: Crossed above 50 SMA on low relative volume. High fakeout risk.")

    # --- ENHANCEMENT 3: Compression vs. Expansion Scanning ---
    ma_spread = abs(sma20 - sma200) / sma200
    
    if ma_spread < 0.03:
        print(" [!] VOLATILITY COIL: Moving averages are compressed under 3%. Big explosive move imminent.")
    elif ma_spread > 0.25:
        print(" [!] OVEREXTENDED WARNING: Moving averages are fanned out wide (>25%). Trend is mature; expect mean reversion.")

    # --- ENHANCEMENT 4: Macro Cross Baseline Status with Price Context ---
    if sma50 > sma200:
        print(" [^] MACRO FRAMEWORK: GOLDEN CROSS Active (Long-term structural bull cycle).")
    else:
        print(" [!] MACRO FRAMEWORK: DEATH CROSS Active (Long-term structural bear market).")
        if current_close > sma200:
            print("     -> NOTE: Price has reclaimed the 200 SMA! Watch for a Bear Market Rally or an early Trend Reversal.")
        
    print("========================================================\n")

except Exception as e:
    print(f"\n[An unexpected error occurred]: {e}")
