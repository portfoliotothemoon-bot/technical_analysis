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
    
    # Calculate a 20-day Volume Average to check institutional support
    data["Volume_20_MA"] = data["Volume"].rolling(window=20).mean()

    # 4. Isolate recent rows for multi-day calculation sweeps
    latest_3_days = data.tail(3)
    latest_row = latest_3_days.tail(1)
    
    # Current Single-Session Metrics
    current_close = float(latest_row["Close"].iloc[0])
    current_volume = float(latest_row["Volume"].iloc[0])
    avg_volume = float(latest_row["Volume_20_MA"].iloc[0])
    
    sma20 = float(latest_row["20_SMA"].iloc[0])
    sma50 = float(latest_row["50_SMA"].iloc[0])
    sma100 = float(latest_row["100_SMA"].iloc[0])
    sma200 = float(latest_row["200_SMA"].iloc[0])

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
    print(f" Daily Volume: {current_volume:,.0f} | 20-Day Avg Volume: {avg_volume:,.0f}")
    print("--------------------------------------------------------")
    print(" ENHANCED INSIGHT ALERTS:")
    print("--------------------------------------------------------")
    
    # --- ENHANCEMENT 1: The 3-Day Structural Breakout Rule ---
    # Check if the close has stayed under the 20 SMA for 3 continuous daily frames
    below_20_3d = all(latest_3_days["Close"] < latest_3_days["20_SMA"])
    above_20_3d = all(latest_3_days["Close"] > latest_3_days["20_SMA"])
    
    if below_20_3d:
        print(" [!] CONFIRMED SHORT-TERM DOWNTURN: Price has closed BELOW its 20 SMA for 3 consecutive days.")
    elif above_20_3d:
        print(" [^] CONFIRMED SHORT-TERM UPTREND: Price has closed ABOVE its 20 SMA for 3 consecutive days.")
    else:
        print(" [-] CHOPPY DRIFT: Price is crossing back and forth over the 20 SMA window.")

    # --- ENHANCEMENT 2: Volume Support Filter ---
    # Trigger volume verification alerts on major moving average tests
    volume_surge = current_volume > (avg_volume * 1.5)
    
    # Check if the price crossed above the 50 SMA specifically during the most recent session
    if current_close > sma50 and latest_3_days["Close"].iloc[-2] < latest_3_days["50_SMA"].iloc[-2]:
        if volume_surge:
            print(" [^] VALID BULLISH BREAKOUT: Passed above 50 SMA supported by heavy institutional volume.")
        else:
            print(" [!] WEAK BREAKOUT WARNING: Crossed above 50 SMA on low volume. High fakeout risk.")

    # --- ENHANCEMENT 3: Compression vs. Expansion Scanning ---
    # Calculate the percentage spread between the fast (20) and slow (200) averages
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
        # Sub-alert verifying if price has broken out above macro structural resistance
        if current_close > sma200:
            print("     -> NOTE: Price has reclaimed the 200 SMA! Watch for a Bear Market Rally or an early Trend Reversal.")
        
    print("========================================================\n")

except Exception as e:
    print(f"\n[An unexpected error occurred]: {e}")
