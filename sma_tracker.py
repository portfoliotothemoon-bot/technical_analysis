import pandas as pd
import yfinance as yf
import sys

print("==================================================================================================================")
print(" QUANTITATIVE TRADING RADAR TERMINAL ENGINE INITIALIZED")
print(" -> Type 'EXIT' at the ticker prompt to close the application safely.")
print("==================================================================================================================")

def main():
    while True:
        # 1. Interactive Terminal Input Prompt
        ticker_symbol = input("\nEnter a stock ticker symbol (or type EXIT): ").strip().upper()

        # Graceful exit handle clause
        if ticker_symbol == "EXIT":
            print("\nClosing terminal connection safely... Good luck trading!\n")
            break

        if not ticker_symbol:
            print("[Error] Ticker symbol cannot be blank!")
            continue

        print(f"Fetching institutional market data for {ticker_symbol}...")

        try:
            # Fetch Official Corporate Company Name Metadata
            try:
                ticker_metadata = yf.Ticker(ticker_symbol)
                company_name = ticker_metadata.info.get("longName", ticker_symbol)
            except Exception:
                company_name = ticker_symbol

            # 2. Extract 2 years of history
            data = yf.download(ticker_symbol, period="2y", progress=False)
            
            if data.empty:
                 print(f"[Error] No market data found for ticker '{ticker_symbol}'. Check spelling or connection.")
                 continue

            if len(data) < 200:
                print(f"[Warning] Limited historical data ({len(data)} days). Some indicators may be unreliable.")

            # Flatten modern multi-level columns
            if isinstance(data.columns, pd.MultiIndex):
                data.columns = data.columns.get_level_values(0)

            # 3. CORE TECHNICAL ENGINE CALCULATIONS
            # Moving Averages
            data["20_SMA"] = data["Close"].rolling(window=20).mean()
            data["50_SMA"] = data["Close"].rolling(window=50).mean()
            data["100_SMA"] = data["Close"].rolling(window=100).mean()
            data["200_SMA"] = data["Close"].rolling(window=200).mean()
            
            # Volume Averages
            data["Volume_10_MA"] = data["Volume"].rolling(window=10).mean()
            data["Volume_20_MA"] = data["Volume"].rolling(window=20).mean()
            data["Volume_63_MA"] = data["Volume"].rolling(window=63).mean()

            # Bollinger Bands
            data["20_StdDev"] = data["Close"].rolling(window=20).std()
            data["Upper_Band"] = data["20_SMA"] + (data["20_StdDev"] * 2)
            data["Median_Band"] = data["20_SMA"]  
            data["Lower_Band"] = data["20_SMA"] - (data["20_StdDev"] * 2)
            data["Bandwidth"] = (data["Upper_Band"] - data["Lower_Band"]) / data["20_SMA"]

            # 14-Period RSI
            delta = data["Close"].diff()
            gain = delta.where(delta > 0, 0).copy()
            loss = (-delta.where(delta < 0, 0)).copy()
            avg_gain = gain.ewm(com=13, adjust=False).mean()
            avg_loss = loss.ewm(com=13, adjust=False).mean()
            rs = avg_gain / avg_loss.replace(0, float('nan'))
            data["RSI"] = 100 - (100 / (1 + rs))

            # Ensure enough clean data for indicators
            data = data.dropna(subset=['20_SMA', '200_SMA', 'RSI', 'Upper_Band'])
            if data.empty:
                print(f"[Error] Insufficient data after calculations for '{ticker_symbol}'.")
                continue

            # 4. ISOLATE LATEST DATA
            latest_3_days = data.tail(3)
            latest_row = data.tail(1)
            
            # Safe numerical extraction
            current_close = float(latest_row["Close"].iloc[0])
            current_open = float(latest_row["Open"].iloc[0])
            current_volume = float(latest_row["Volume"].iloc[0])
            avg_volume_10d = float(latest_row["Volume_10_MA"].iloc[0] if pd.notna(latest_row["Volume_10_MA"].iloc[0]) else 0)
            avg_volume_1m = float(latest_row["Volume_20_MA"].iloc[0] if pd.notna(latest_row["Volume_20_MA"].iloc[0]) else 0)
            avg_volume_3m = float(latest_row["Volume_63_MA"].iloc[0] if pd.notna(latest_row["Volume_63_MA"].iloc[0]) else 0)
            
            sma20 = float(latest_row["20_SMA"].iloc[0])
            sma50 = float(latest_row["50_SMA"].iloc[0] if pd.notna(latest_row["50_SMA"].iloc[0]) else current_close)
            sma100 = float(latest_row["100_SMA"].iloc[0] if pd.notna(latest_row["100_SMA"].iloc[0]) else current_close)
            sma200 = float(latest_row["200_SMA"].iloc[0])
            
            upper_bb = float(latest_row["Upper_Band"].iloc[0])
            median_bb = float(latest_row["Median_Band"].iloc[0])
            lower_bb = float(latest_row["Lower_Band"].iloc[0])
            bandwidth = float(latest_row["Bandwidth"].iloc[0] if pd.notna(latest_row["Bandwidth"].iloc[0]) else 0.1)
            rsi_val = float(latest_row["RSI"].iloc[0])

            # 5. FORMAT DASHBOARD — Reordered: MAs first, then Bollinger Bands 2 lines below
            columns_to_format = [
                "Close", 
                "20_SMA", "50_SMA", "100_SMA", "200_SMA",   # Moving Averages
                "Upper_Band", "Median_Band", "Lower_Band"   # Bollinger Bands (moved down)
            ]
            
            print_df = latest_row[columns_to_format].copy()
            for col in columns_to_format:
                print_df[col] = print_df[col].map(lambda x: f"${x:,.2f}" if pd.notnull(x) else "$N/A")

            print_df["14_RSI"] = f"{rsi_val:.2f}"

            # 6. OUTPUT
            print("\n==================================================================================================================")
            print(f" EXPERT TECHNICAL MONITOR FOR: {company_name} ({ticker_symbol})")
            print("==================================================================================================================")
            print(print_df.to_string(index=False))
            print("==================================================================================================================")
            print(f" Daily Volume     : {current_volume:,.0f}")
            print(f" 10-Day Avg Vol   : {avg_volume_10d:,.0f}")
            print(f" 1-Month Avg Vol  : {avg_volume_1m:,.0f} (20-day window)")
            print(f" 3-Month Avg Vol  : {avg_volume_3m:,.0f} (63-day window)")
            print("------------------------------------------------------------------------------------------------------------------")
            print(" QUANTITATIVE MARKET INSIGHT ALERTS:")
            print("------------------------------------------------------------------------------------------------------------------")
            
            signal_score = 0

            # Insight 1: Volume-Price Action
            is_green_day = current_close > current_open
            heavy_volume = current_volume > (avg_volume_10d * 1.5) if avg_volume_10d > 0 else False
            
            if is_green_day and heavy_volume:
                print(" [^] INSTITUTIONAL ACCUMULATION: Strong green close on heavy volume.")
                signal_score += 2
            elif not is_green_day and heavy_volume:
                print(" [!] INSTITUTIONAL DISTRIBUTION: Sharp selling on heavy volume.")
                signal_score -= 2
            else:
                print(" [-] RETAIL CHOP: Normal/low volume.")

            # Insight 2: Short-term trend
            if current_close > sma20:
                print(" [^] ABOVE 20 SMA: Bullish short-term momentum.")
                signal_score += 1
            else:
                print(" [!] BELOW 20 SMA: Bearish short-term pressure.")
                signal_score -= 1

            # Insight 3: Long-term position
            extension_pct = ((current_close - sma200) / sma200) * 100 if sma200 != 0 else 0
            is_overextended = extension_pct > 20
            
            if is_overextended:
                print(f" [!] EXTENSION RISK: {extension_pct:.1f}% above 200 SMA.")
            elif 0 <= extension_pct <= 3:
                print(" [^] STRUCTURAL SUPPORT: Near 200 SMA bounce zone.")
                signal_score += 1

            if current_close > sma200:
                signal_score += 1
            else:
                signal_score -= 1

            # Insight 4: Bollinger Bands
            if bandwidth < 0.06:
                print(f" [!] VOLATILITY SQUEEZE: Tight bands ({bandwidth*100:.1f}% spread).")
            if current_close >= upper_bb:
                print(" [!] UPPER BAND TAG: Overbought stretch.")
            elif current_close <= lower_bb:
                print(" [^] LOWER BAND TAG: Oversold reversion.")

            # Insight 5: Golden/Death Cross
            if sma50 > sma200:
                print(" [^] GOLDEN CROSS: Long-term bull structure.")
                signal_score += 1
            else:
                print(" [!] DEATH CROSS: Long-term bear structure.")
                signal_score -= 1
                if current_close > sma200:
                    print("     -> Price reclaimed 200 SMA (potential reversal).")
                    signal_score += 1

            # Insight 6: 3-day trend
            below_20_3d = all(latest_3_days["Close"] < latest_3_days["20_SMA"])
            above_20_3d = all(latest_3_days["Close"] > latest_3_days["20_SMA"])
            if below_20_3d:
                print(" [!] 3-DAY DOWNTREND CONFIRMED.")
                signal_score -= 1
            elif above_20_3d:
                print(" [^] 3-DAY UPTREND CONFIRMED.")
                signal_score += 1
            else:
                print(" [-] Mixed 3-day action.")

            # Insight 7: RSI
            if rsi_val >= 70:
                print(f" [!] OVERBOUGHT: RSI at {rsi_val:.2f}.")
                signal_score -= 1
            elif rsi_val <= 30:
                print(f" [^] OVERSOLD: RSI at {rsi_val:.2f}.")
                signal_score += 1
            else:
                print(f" [-] Neutral RSI: {rsi_val:.2f}.")

            # Final Verdict
            print("------------------------------------------------------------------------------------------------------------------")
            print(" ALGORITHMIC TRADING SIGNAL VERDICT:")
            print("------------------------------------------------------------------------------------------------------------------")
            
            if signal_score >= 5:
                verdict = "STRONG BUY"
                strength = "HIGH CONVICTION"
            elif signal_score >= 3:
                verdict = "BUY"
                strength = "MODERATE"
            elif signal_score >= 1:
                verdict = "CAUTIOUS BUY"
                strength = "WEAK"
            elif signal_score <= -5:
                verdict = "STRONG SELL"
                strength = "HIGH CONVICTION"
            elif signal_score <= -3:
                verdict = "SELL"
                strength = "MODERATE"
            elif signal_score <= -1:
                verdict = "CAUTIOUS SELL"
                strength = "WEAK"
            else:
                verdict = "NEUTRAL"
                strength = "SIDEWAYS"

            if is_overextended and "BUY" in verdict:
                verdict = "BUY but WATCH FOR PULLBACK"
            if rsi_val >= 75 or current_close >= upper_bb * 1.02:
                verdict = "OVERBOUGHT - CONSIDER TAKING PROFITS"

            print(f" OVERALL SIGNAL: {verdict}")
            print(f" STRENGTH: {strength} | Score: {signal_score}")
            print("\n==================================================================================================================")

        except Exception as e:
            print(f"[Critical Error] Failed to process {ticker_symbol}: {str(e)}")
            continue

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nTerminal session terminated.")
        sys.exit(0)