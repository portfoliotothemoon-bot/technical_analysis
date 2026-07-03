import pandas as pd
import yfinance as yf

# 1. Interactive Terminal Input Prompt
ticker_symbol = input("Enter a stock ticker symbol (e.g., AAPL, MRVL, NVDA): ").strip().upper()

if not ticker_symbol:
    print("[Error] Ticker symbol cannot be blank!")
    exit()

print(f"\nFetching institutional market data for {ticker_symbol}...")

try:
    # --- NEW: Fetch Official Corporate Company Name Metadata ---
    try:
        ticker_metadata = yf.Ticker(ticker_symbol)
        company_name = ticker_metadata.info.get("longName", ticker_symbol)
    except Exception:
        # Fallback to ticker symbol if API metadata experiences a temporary network lag
        company_name = ticker_symbol

    # 2. Extract 2 years of history
    data = yf.download(ticker_symbol, period="2y")
    
    if data.empty:
         print(f"[Error] No market data found for ticker '{ticker_symbol}'. Check your spelling.")
         exit()

    # Flatten modern multi-level columns down to single text labels
    data.columns = data.columns.get_level_values(0)

    # 3. CORE TECHNICAL ENGINE CALCULATIONS
    data["20_SMA"] = data["Close"].rolling(window=20).mean()
    data["50_SMA"] = data["Close"].rolling(window=50).mean()
    data["100_SMA"] = data["Close"].rolling(window=100).mean()
    data["200_SMA"] = data["Close"].rolling(window=200).mean()
    
    # Volume Averages 
    data["Volume_20_MA"] = data["Volume"].rolling(window=20).mean()
    data["Volume_63_MA"] = data["Volume"].rolling(window=63).mean()

    # Bollinger Bands (Volatility Monitoring)
    data["20_StdDev"] = data["Close"].rolling(window=20).std()
    data["Upper_Band"] = data["20_SMA"] + (data["20_StdDev"] * 2)
    data["Lower_Band"] = data["20_SMA"] - (data["20_StdDev"] * 2)
    data["Bandwidth"] = (data["Upper_Band"] - data["Lower_Band"]) / data["20_SMA"]

    # 4. ISOLATE TIME INTERVAL MATRICES
    latest_3_days = data.tail(3)
    latest_row = latest_3_days.tail(1)
    
    # Raw Numerical Conversions
    current_close = float(latest_row["Close"].iloc[0])
    current_open = float(latest_row["Open"].iloc[0])
    current_volume = float(latest_row["Volume"].iloc[0])
    avg_volume_1m = float(latest_row["Volume_20_MA"].iloc[0])
    avg_volume_3m = float(latest_row["Volume_63_MA"].iloc[0])
    
    sma20 = float(latest_row["20_SMA"].iloc[0])
    sma50 = float(latest_row["50_SMA"].iloc[0])
    sma100 = float(latest_row["100_SMA"].iloc[0])
    sma200 = float(latest_row["200_SMA"].iloc[0])
    bandwidth = float(latest_row["Bandwidth"].iloc[0])

    # 5. FORMAT AND GENERATE TECHNICAL DASHBOARD
    columns_to_keep = ["Close", "20_SMA", "50_SMA", "100_SMA", "200_SMA"]
    print_df = latest_row[columns_to_keep].copy()
    for col in columns_to_keep:
        print_df[col] = print_df[col].map(lambda x: f"${x:,.2f}" if pd.notnull(x) else "$0.00")

    # 6. Print formatted metrics table (Now dynamically including the full Company Name)
    print("\n========================================================")
    print(f" EXPERT TECHNICAL MONITOR FOR: {company_name} ({ticker_symbol})")
    print("========================================================")
    print(print_df.to_string(index=False))
    print("========================================================")
    print(f" Daily Volume : {current_volume:,.0f}")
    print(f" 1-Month Avg  : {avg_volume_1m:,.0f} (20-day window)")
    print(f" 3-Month Avg  : {avg_volume_3m:,.0f} (63-day window)")
    print("--------------------------------------------------------")
    print(f" QUANTITATIVE MARKET INSIGHT ALERTS:")
    print("--------------------------------------------------------")
    
    # Initialize Scoring Matrix
    signal_score = 0

    # --- INSIGHT 1: Institutional Volume-Price Action Check ---
    is_green_day = current_close > current_open
    heavy_volume = current_volume > (avg_volume_1m * 1.3)
    
    if is_green_day and heavy_volume:
        print(" [^] INSTITUTIONAL ACCUMULATION: Strong green close on heavy volume. Money is flowing in.")
        signal_score += 1
    elif not is_green_day and heavy_volume:
        print(" [!] INSTITUTIONAL DISTRIBUTION: Sharp selling on heavy volume. Big money is exiting.")
        signal_score -= 1
    else:
        print(" [-] RETAIL CHOP: Volume is normal or low. Institutions are sitting out.")

    # --- INSIGHT 2: Price Position vs Short-Term Trend ---
    if current_close > sma20:
        signal_score += 1
    else:
        signal_score -= 1

    # --- INSIGHT 3: The 50/200 SMA Gravity Zone Alert ---
    extension_pct = ((current_close - sma200) / sma200) * 100
    is_overextended = False
    
    if extension_pct > 20:
        print(f" [!] EXTENSION RISK: Price is {extension_pct:.1f}% above the 200 SMA. Overextended risk.")
        is_overextended = True
    elif 0 <= extension_pct <= 3:
        print(" [^] STRUCTURAL SUPPORT: Price has pulled down to within 3% of the 200 SMA. Bounce zone.")
        signal_score += 1

    if current_close > sma200:
        signal_score += 1
    else:
        signal_score -= 1

    # --- INSIGHT 4: Bollinger Band Width Volatility Squeeze ---
    if bandwidth < 0.06:
        print(f" [!] VOLATILITY SQUEEZE ACTIVE: Bands are locked tight ({bandwidth*100:.1f}% spread). Breakout imminent.")

    # --- INSIGHT 5: Core Macro Framework Cross Baseline Status ---
    if sma50 > sma200:
        print(" [^] MACRO FRAMEWORK: GOLDEN CROSS Active (Long-term structural bull cycle).")
        signal_score += 1
    else:
        print(" [!] MACRO FRAMEWORK: DEATH CROSS Active (Long-term structural bear market).")
        signal_score -= 1
        if current_close > sma200:
            print("     -> NOTE: Price has reclaimed the 200 SMA! Watch for a Bear Rally or early reversal.")
            signal_score += 1

    # --- INSIGHT 6: 3-Day Structural Breakout Rule ---
    below_20_3d = all(latest_3_days["Close"] < latest_3_days["20_SMA"])
    above_20_3d = all(latest_3_days["Close"] > latest_3_days["20_SMA"])
    if below_20_3d:
        print(" [!] CONFIRMED SHORT-TERM DOWNTURN: Price closed BELOW 20 SMA for 3 consecutive days.")
        signal_score -= 1
    elif above_20_3d:
        print(" [^] CONFIRMED SHORT-TERM UPTREND: Price closed ABOVE 20 SMA for 3 consecutive days.")
        signal_score += 1

    # --- 8. ALGORITHMIC SIGNAL VERDICT MATRIX ---
    print("--------------------------------------------------------")
    print(" ALGORITHMIC TRADING SIGNAL VERDICT:")
    print("--------------------------------------------------------")
    
    if signal_score >= 3:
        if is_overextended:
            print(f" >>> SIGNAL: HOLD (Score: {signal_score}) <<<\n [Reasoning] Strong uptrend, but the stock is too overextended above its 200 SMA to safely buy here.")
        else:
            print(f" >>> SIGNAL: STRONG BUY (Score: {signal_score}) <<<\n [Reasoning] Indicators are aligned into an aggressive bullish expansion profile with volume support.")
            
    elif 1 <= signal_score <= 2:
        print(f" >>> SIGNAL: BUY / ACCUMULATE (Score: {signal_score}) <<<\n [Reasoning] Moderate upward bias. Good structural momentum baseline.")
        
    elif -1 <= signal_score <= 0:
        print(f" >>> SIGNAL: HOLD / NEUTRAL (Score: {signal_score}) <<<\n [Reasoning] Conflicting signals or choppy sideways market framework. Wait for confirmation.")
        
    elif -3 <= signal_score <= -2:
        print(f" >>> SIGNAL: SELL / LIGHTEN (Score: {signal_score}) <<<\n [Reasoning] Market is breaking down into a short-to-medium-term defensive configuration.")
        
    else: 
        print(f" >>> SIGNAL: STRONG SELL (Score: {signal_score}) <<<\n [Reasoning] Full systemic macro breakdown. Active death cross paired with heavy distribution selling.")
        
    print("========================================================\n")

except Exception as e:
    print(f"\n[An unexpected error occurred]: {e}")
