import pandas as pd
import yfinance as yf
import sys
import numpy as np
import datetime

from fred_treasury_spread import get_treasury_yield_spread
from fib_retracement_levels import get_fibonacci_levels

print("==================================================================================================================")
print(" QUANTITATIVE TRADING RADAR TERMINAL ENGINE v2.3")
print(" -> Type 'EXIT' at the ticker prompt to close the application safely.")
print("==================================================================================================================")

def calculate_atr(data, period=14):
    high_low = data['High'] - data['Low']
    high_close = np.abs(data['High'] - data['Close'].shift())
    low_close = np.abs(data['Low'] - data['Close'].shift())
    tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
    atr = tr.rolling(window=period).mean()
    return atr

def calculate_macd(data):
    """Calculate MACD (12,26,9)"""
    ema12 = data["Close"].ewm(span=12, adjust=False).mean()
    ema26 = data["Close"].ewm(span=26, adjust=False).mean()
    data["MACD_Line"] = ema12 - ema26
    data["MACD_Signal"] = data["MACD_Line"].ewm(span=9, adjust=False).mean()
    data["MACD_Hist"] = data["MACD_Line"] - data["MACD_Signal"]
    return data

def get_next_earnings_date(ticker_obj):
    """Improved next earnings date fetcher"""
    today = datetime.datetime.now().date()
    
    try:
        calendar = ticker_obj.calendar
        if calendar is not None and not calendar.empty:
            if isinstance(calendar, pd.DataFrame):
                if 'Earnings Date' in calendar.index:
                    dates = calendar.loc['Earnings Date']
                    for d in dates:
                        if pd.notna(d):
                            if isinstance(d, (datetime.datetime, pd.Timestamp)):
                                d_date = d.date() if hasattr(d, 'date') else d
                            else:
                                try:
                                    d_date = pd.to_datetime(d).date()
                                except:
                                    continue
                            if d_date > today:
                                return d_date.strftime('%Y-%m-%d')
                for col in calendar.columns:
                    for val in calendar[col]:
                        if pd.notna(val):
                            try:
                                dt = pd.to_datetime(val)
                                if dt.date() > today:
                                    return dt.strftime('%Y-%m-%d')
                            except:
                                continue
            elif isinstance(calendar, dict):
                for key, value in calendar.items():
                    if 'earnings' in str(key).lower() or 'date' in str(key).lower():
                        try:
                            dt = pd.to_datetime(value)
                            if dt.date() > today:
                                return dt.strftime('%Y-%m-%d')
                        except:
                            continue
    except Exception:
        pass

    try:
        earnings_df = ticker_obj.get_earnings_dates(limit=10)
        if earnings_df is not None and not earnings_df.empty:
            for idx in earnings_df.index:
                if isinstance(idx, (datetime.datetime, pd.Timestamp)) and idx.date() > today:
                    return idx.strftime('%Y-%m-%d')
    except:
        pass

    try:
        info = ticker_obj.info
        earnings_keys = ['earningsDate', 'nextEarningsDate', 'earningsTimestamp']
        for key in earnings_keys:
            if key in info and info[key]:
                val = info[key]
                if isinstance(val, list) and val:
                    val = val[0]
                try:
                    if isinstance(val, (int, float)):
                        dt = datetime.datetime.fromtimestamp(val)
                    else:
                        dt = pd.to_datetime(val)
                    if dt.date() > today:
                        return dt.strftime('%Y-%m-%d')
                except:
                    continue
    except:
        pass

    return "N/A"

def main():
    while True:
        ticker_symbol = input("\nEnter a stock ticker symbol (or type EXIT): ").strip().upper()

        if ticker_symbol == "EXIT":
            print("\nClosing terminal connection safely... Good luck trading!\n")
            break

        if not ticker_symbol:
            print("[Error] Ticker symbol cannot be blank!")
            continue

        print(f"\nFetching institutional market data for {ticker_symbol}...")

        try:
            try:
                ticker_metadata = yf.Ticker(ticker_symbol)
                company_name = ticker_metadata.info.get("longName", ticker_symbol)
            except Exception:
                company_name = ticker_symbol

            next_earnings = get_next_earnings_date(ticker_metadata)

            print("\nFetching Macro Context (Treasury Yields)...")
            get_treasury_yield_spread()

            data = yf.download(ticker_symbol, period="2y", progress=False)
            
            if data.empty:
                print(f"[Error] No market data found for ticker '{ticker_symbol}'.")
                continue

            if isinstance(data.columns, pd.MultiIndex):
                data.columns = data.columns.get_level_values(0)

            # === CORE TECHNICAL CALCULATIONS ===
            data["9_EMA"] = data["Close"].ewm(span=9, adjust=False).mean()
            data["20_SMA"] = data["Close"].rolling(window=20).mean()
            data["50_SMA"] = data["Close"].rolling(window=50).mean()
            data["100_SMA"] = data["Close"].rolling(window=100).mean()
            data["200_SMA"] = data["Close"].rolling(window=200).mean()
            
            data["Volume_10_MA"] = data["Volume"].rolling(window=10).mean()
            data["Volume_20_MA"] = data["Volume"].rolling(window=20).mean()
            data["Volume_63_MA"] = data["Volume"].rolling(window=63).mean()

            data["Candle_Spread"] = data["High"] - data["Low"]
            data["Spread_20_MA"] = data["Candle_Spread"].rolling(window=20).mean()

            data["20_StdDev"] = data["Close"].rolling(window=20).std()
            data["Upper_Band"] = data["20_SMA"] + (data["20_StdDev"] * 2)
            data["Median_Band"] = data["20_SMA"]
            data["Lower_Band"] = data["20_SMA"] - (data["20_StdDev"] * 2)
            data["Bandwidth"] = (data["Upper_Band"] - data["Lower_Band"]) / data["20_SMA"]

            delta = data["Close"].diff()
            gain = delta.where(delta > 0, 0).copy()
            loss = (-delta.where(delta < 0, 0)).copy()
            avg_gain = gain.ewm(com=13, adjust=False).mean()
            avg_loss = loss.ewm(com=13, adjust=False).mean()
            rs = avg_gain / avg_loss.replace(0, float('nan'))
            data["RSI"] = 100 - (100 / (1 + rs))

            data["ATR"] = calculate_atr(data)
            data = calculate_macd(data)

            data = data.dropna(subset=['9_EMA', '20_SMA', '200_SMA', 'RSI', 'Upper_Band', 'Spread_20_MA', 'ATR', 'MACD_Line'])
            if data.empty:
                print(f"[Error] Insufficient data after calculations for '{ticker_symbol}'.")
                continue

            latest_row = data.tail(1)
            latest_3_days = data.tail(3)
            
            current_close = float(latest_row["Close"].iloc[0])
            current_open = float(latest_row["Open"].iloc[0])
            current_high = float(latest_row["High"].iloc[0])
            current_low = float(latest_row["Low"].iloc[0])
            current_volume = float(latest_row["Volume"].iloc[0])
            
            avg_volume_10d = float(latest_row["Volume_10_MA"].iloc[0] if pd.notna(latest_row["Volume_10_MA"].iloc[0]) else 0)
            avg_volume_1m = float(latest_row["Volume_20_MA"].iloc[0] if pd.notna(latest_row["Volume_20_MA"].iloc[0]) else 0)
            avg_volume_3m = float(latest_row["Volume_63_MA"].iloc[0] if pd.notna(latest_row["Volume_63_MA"].iloc[0]) else 0)
            
            ema9 = float(latest_row["9_EMA"].iloc[0])
            sma20 = float(latest_row["20_SMA"].iloc[0])
            sma50 = float(latest_row["50_SMA"].iloc[0] if pd.notna(latest_row["50_SMA"].iloc[0]) else current_close)
            sma200 = float(latest_row["200_SMA"].iloc[0])
            
            upper_bb = float(latest_row["Upper_Band"].iloc[0])
            lower_bb = float(latest_row["Lower_Band"].iloc[0])
            bandwidth = float(latest_row["Bandwidth"].iloc[0] if pd.notna(latest_row["Bandwidth"].iloc[0]) else 0.1)
            rsi_val = float(latest_row["RSI"].iloc[0])
            atr_val = float(latest_row["ATR"].iloc[0])

            macd_line = float(latest_row["MACD_Line"].iloc[0])
            macd_signal = float(latest_row["MACD_Signal"].iloc[0])
            macd_hist = float(latest_row["MACD_Hist"].iloc[0])

            heavy_volume = current_volume > (avg_volume_10d * 1.5) if avg_volume_10d > 0 else False
            is_green_day = current_close > current_open

            # ==================== VOLUME PARTICIPATION LOGIC ====================
            low_volume_threshold = 0.70
            is_low_volume = (current_volume < (avg_volume_10d * low_volume_threshold) and 
                           current_volume < (avg_volume_1m * low_volume_threshold) and 
                           current_volume < (avg_volume_3m * low_volume_threshold)) if avg_volume_10d > 0 else False

            is_retail_up_move = is_green_day and is_low_volume

            # NEW: Institutional participation (above average but not extreme)
            is_institutional_up_move = (is_green_day and 
                                       current_volume > avg_volume_10d and 
                                       not heavy_volume) if avg_volume_10d > 0 else False
            # =================================================================

            # ==================== OUTPUT DASHBOARD ====================
            print("\n===================================================================================================================================")
            print(f" EXPERT TECHNICAL MONITOR FOR: {company_name} ({ticker_symbol}) | Next Earnings: {next_earnings} -  ⚠️ TRADE WITH THE TREND")
            print("====================================================================================================================================")
            
            ma_columns = ["Close", "9_EMA", "20_SMA", "50_SMA", "100_SMA", "200_SMA"]
            ma_df = latest_row[ma_columns].copy()
            for col in ma_columns:
                ma_df[col] = ma_df[col].map(lambda x: f"${x:,.2f}" if pd.notnull(x) else "$N/A")
            ma_df["14_RSI"] = f"{rsi_val:.2f}"

            print("PRICE & MOVING AVERAGES:")
            print(ma_df.to_string(index=False))
            print("------------------------------------------------------------------------------------------------------------------")
            
            bb_columns = ["Upper_Band", "Median_Band", "Lower_Band", "Bandwidth"]
            bb_df = latest_row[bb_columns].copy()
            for col in bb_columns:
                if col == "Bandwidth":
                    bb_df[col] = bb_df[col].map(lambda x: f"{x:.4f}" if pd.notnull(x) else "N/A")
                else:
                    bb_df[col] = bb_df[col].map(lambda x: f"${x:,.2f}" if pd.notnull(x) else "$N/A")

            print("BOLLINGER BANDS (20-period):")
            print(bb_df.to_string(index=False))
            print("------------------------------------------------------------------------------------------------------------------")

            print("MACD (12,26,9):")
            print(f"  MACD Line   : {macd_line:.4f}")
            print(f"  Signal Line : {macd_signal:.4f}")
            print(f"  Histogram   : {macd_hist:.4f}")
            
            if macd_line > macd_signal and macd_hist > 0:
                print("  [^] BULLISH MOMENTUM: MACD above Signal + positive histogram")
            elif macd_line < macd_signal and macd_hist < 0:
                print("  [!] BEARISH MOMENTUM: MACD below Signal + negative histogram")
            else:
                print("  [-] NEUTRAL: MACD near Signal line or flat histogram")
            print("==================================================================================================================")

            try:
                fib_result = get_fibonacci_levels(ticker_symbol)
                if fib_result is not None and fib_result[0] is not None:
                    fib_df, extreme_prices = fib_result
                    high_val, low_val = extreme_prices
                    print(f"FIBONACCI 3-MONTH RETRACEMENT LEVELS (High: ${high_val:,.2f} | Low: ${low_val:,.2f}):")
                    print(fib_df.to_string(index=False))
                else:
                    print("FIBONACCI LEVELS: [Warning] No data found for this ticker over the last 3 months.")
            except Exception as fib_err:
                print(f"FIBONACCI LEVELS: [Error] Failed to calculate: {str(fib_err)}")

            print("==================================================================================================================")
            print(f" Daily Volume     : {current_volume:,.0f}")
            print(f" 10-Day Avg Vol   : {avg_volume_10d:,.0f}")
            print(f" 1-Month Avg Vol  : {avg_volume_1m:,.0f}")
            print(f" 3-Month Avg Vol  : {avg_volume_3m:,.0f}")
            print("------------------------------------------------------------------------------------------------------------------")
            print(" QUANTITATIVE MARKET INSIGHT ALERTS:")
            print("------------------------------------------------------------------------------------------------------------------")
            
            # New Institutional + Retail alerts
            if is_retail_up_move:
                print(" 🚨 RETAIL-DRIVEN MOVE: Price UP on LOW VOLUME (retail participation dominant)")
            elif is_institutional_up_move:
                print(" 🏦 INSTITUTIONAL PARTICIPATION: Price UP on ABOVE-AVERAGE volume (healthy institutional buying)")
            
            # YOUR ORIGINAL LOGIC (fully preserved)
            signal_score = 0

            if is_green_day and heavy_volume:
                print(" [^] INSTITUTIONAL ACCUMULATION: Strong green close on heavy volume.")
                signal_score += 2
            elif not is_green_day and heavy_volume:
                print(" [!] INSTITUTIONAL DISTRIBUTION: Sharp selling on heavy volume.")
                signal_score -= 2
            else:
                print(" [-] RETAIL CHOP: Normal/low volume.")

            if current_close > ema9:
                print(" [^] ABOVE 9 EMA: Strong short-term bullish momentum.")
                signal_score += 2
            else:
                print(" [!] BELOW 9 EMA: Short-term bearish pressure.")
                signal_score -= 2

            if current_close > sma20:
                print(" [^] ABOVE 20 SMA: Bullish short-term momentum.")
                signal_score += 1
            else:
                print(" [!] BELOW 20 SMA: Bearish short-term pressure.")
                signal_score -= 1

            if macd_line > macd_signal and macd_hist > 0:
                print(" [^] MACD BULLISH CROSSOVER")
                signal_score += 2
            elif macd_line < macd_signal and macd_hist < 0:
                print(" [!] MACD BEARISH CROSSOVER")
                signal_score -= 2
            else:
                print(" [-] MACD Neutral")

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

            if bandwidth < 0.06:
                print(f" [!] VOLATILITY SQUEEZE: Tight bands ({bandwidth*100:.1f}% spread).")
            if current_close >= upper_bb:
                print(" [!] UPPER BAND TAG: Overbought stretch.")
            elif current_close <= lower_bb:
                print(" [^] LOWER BAND TAG: Oversold reversion.")

            if sma50 > sma200:
                print(" [^] GOLDEN CROSS: Long-term bull structure.")
                signal_score += 1
            else:
                print(" [!] DEATH CROSS: Long-term bear structure.")
                signal_score -= 1
                if current_close > sma200:
                    print("     -> Price reclaimed 200 SMA (potential reversal).")
                    signal_score += 1

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

            if rsi_val >= 70:
                print(f" [!] OVERBOUGHT: RSI at {rsi_val:.2f}.")
                signal_score -= 1
            elif rsi_val <= 30:
                print(f" [^] OVERSOLD: RSI at {rsi_val:.2f}.")
                signal_score += 1
            else:
                print(f" [-] Neutral RSI: {rsi_val:.2f}.")

            # Final Verdict + Trade Recommendation (unchanged)
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
            print(" NEXT TRADE SETUP RECOMMENDATION")
            print("==================================================================================================================")

            bullish_bias = (current_close > ema9 and current_close > sma20 and signal_score >= 2)
            bearish_bias = (current_close < ema9 and current_close < sma20 and signal_score <= -2)

            if bullish_bias and rsi_val < 72:
                direction = "LONG"
            elif bearish_bias and rsi_val > 28:
                direction = "SHORT"
            else:
                direction = "NEUTRAL"

            if direction == "LONG":
                stop_loss = max(current_low * 0.985, current_close - atr_val * 1.8)
                risk = current_close - stop_loss
                tp1 = current_close + (risk * 2)
                tp2 = current_close + (risk * 3.5)

                print(f" DIRECTION      : 🟢 LONG")
                print(f" ENTRY          : ${current_close:,.2f}")
                print(f" STOP LOSS      : ${stop_loss:,.2f}")
                print(f" TAKE PROFIT 1  : ${tp1:,.2f} (2R)")
                print(f" TAKE PROFIT 2  : ${tp2:,.2f} (3.5R)")
                print(f" RISK:REWARD    : 1:2.75")
                print(" Bias           : Bullish momentum + positive signal score")

            elif direction == "SHORT":
                stop_loss = min(current_high * 1.015, current_close + atr_val * 1.8)
                risk = stop_loss - current_close
                tp1 = current_close - (risk * 2)
                tp2 = current_close - (risk * 3.5)

                print(f" DIRECTION      : 🔴 SHORT")
                print(f" ENTRY          : ${current_close:,.2f}")
                print(f" STOP LOSS      : ${stop_loss:,.2f}")
                print(f" TAKE PROFIT 1  : ${tp1:,.2f} (2R)")
                print(f" TAKE PROFIT 2  : ${tp2:,.2f} (3.5R)")
                print(f" RISK:REWARD    : 1:2.75")

            else:
                print(" DIRECTION      : ⚪ NEUTRAL / WAIT")
                print(" RECOMMENDATION : No clear high-conviction setup right now.")

            print("------------------------------------------------------------------------------------------------------------------")
            print(f" ATR (14)       : ${atr_val:,.2f}")
            print("==================================================================================================================")

            # ==================== NEW: NEXT BULLISH & BEARISH TRADING IDEAS ====================
            print("\n==================================================================================================================")
            print(" NEXT BULLISH & BEARISH TRADING IDEAS")
            print("==================================================================================================================")

            bullish_ideas = []
            bearish_ideas = []

            # Bullish Ideas
            if current_close > sma20 and macd_hist > 0:
                bullish_ideas.append("• Bullish continuation above 20 SMA with positive MACD histogram → Look for pullback to 9 EMA or 20 SMA as entry.")
            if is_institutional_up_move:
                bullish_ideas.append("• Institutional buying on above-average volume → Stronger conviction upside. Target next Fibonacci extension or resistance.")
            if rsi_val < 60 and current_close > ema9:
                bullish_ideas.append("• RSI not overbought + above short-term EMAs → Momentum trade long with tight stop below recent low.")
            if current_close > sma200 and sma50 > sma200:
                bullish_ideas.append("• Golden Cross structure intact → Swing long toward upper Bollinger Band or previous highs.")

            # Bearish Ideas
            if current_close < sma20 and macd_hist < 0:
                bearish_ideas.append("• Bearish momentum below 20 SMA with negative MACD → Consider short or stay in cash.")
            if rsi_val > 70 or current_close >= upper_bb:
                bearish_ideas.append("• Overbought conditions (high RSI or Upper BB tag) → Potential mean reversion or short setup.")
            if is_retail_up_move and current_close > sma200 * 1.15:
                bearish_ideas.append("• Retail-driven rally on low volume near extension zone → High risk of reversal. Watch for distribution.")
            if sma50 < sma200:
                bearish_ideas.append("• Death Cross environment → Favor bearish bias or defensive positioning.")

            if bullish_ideas:
                print(" 🟢 BULLISH TRADING IDEAS:")
                for idea in bullish_ideas[:3]:   # Limit to top 3
                    print(idea)
            else:
                print(" 🟢 BULLISH TRADING IDEAS: Limited bullish signals at the moment.")

            print("---")
            if bearish_ideas:
                print(" 🔴 BEARISH TRADING IDEAS:")
                for idea in bearish_ideas[:3]:
                    print(idea)
            else:
                print(" 🔴 BEARISH TRADING IDEAS: No strong bearish signals currently.")

            print("==================================================================================================================")

            # ==================== NEW: SPECIFIC BULLISH & BEARISH TRADE EXAMPLES ====================
            print("\n==================================================================================================================")
            print(" CONCRETE BULLISH & BEARISH TRADE SETUPS")
            print("==================================================================================================================")

            atr = atr_val
            price = current_close

            # === BULLISH TRADE SETUP ===
            print(" 🟢 BULLISH TRADE EXAMPLE (Long Setup)")
            
            if current_close > ema9 and macd_hist > 0:
                bullish_entry = price * 1.002   # slight premium for limit order
                bullish_stop = max(current_low * 0.982, price - atr * 2.0)
                bullish_tp1 = price + (price - bullish_stop) * 2.0
                bullish_tp2 = price + (price - bullish_stop) * 3.5
                
                risk = price - bullish_stop
                reward = bullish_tp2 - price
                
                print(f" Entry (Limit)     : ${bullish_entry:,.2f}")
                print(f" Stop Loss         : ${bullish_stop:,.2f}  (-{((price - bullish_stop)/price*100):.2f}%)")
                print(f" Take Profit 1     : ${bullish_tp1:,.2f}  (2R)")
                print(f" Take Profit 2     : ${bullish_tp2:,.2f}  (3.5R)")
                print(f" Risk:Reward       : 1:{(reward/risk):.2f}")
                print(" Rationale         : Bullish momentum (above 9EMA + positive MACD). Good for swing trade.")
            else:
                print(" No strong bullish setup at the moment. Wait for better alignment.")

            print("---")

            # === BEARISH TRADE SETUP ===
            print(" 🔴 BEARISH TRADE EXAMPLE (Short Setup)")
            
            if current_close < ema9 and macd_hist < 0:
                bearish_entry = price * 0.998   # slight discount for limit
                bearish_stop = min(current_high * 1.018, price + atr * 2.0)
                bearish_tp1 = price - (bearish_stop - price) * 2.0
                bearish_tp2 = price - (bearish_stop - price) * 3.5
                
                risk = bearish_stop - price
                reward = price - bearish_tp2
                
                print(f" Entry (Limit)     : ${bearish_entry:,.2f}")
                print(f" Stop Loss         : ${bearish_stop:,.2f}  (+{((bearish_stop - price)/price*100):.2f}%)")
                print(f" Take Profit 1     : ${bearish_tp1:,.2f}  (2R)")
                print(f" Take Profit 2     : ${bearish_tp2:,.2f}  (3.5R)")
                print(f" Risk:Reward       : 1:{(reward/risk):.2f}")
                print(" Rationale         : Bearish momentum (below 9EMA + negative MACD).")
            else:
                print(" No strong bearish setup at the moment. Wait for confirmation.")

            print("==================================================================================================================")
            print(" ⚠️  Always use proper position sizing. These are algorithmic suggestions based on current signals.")
            print("==================================================================================================================")

        except Exception as e:
            print(f"[Critical Error] Failed to process {ticker_symbol}: {str(e)}")
            continue

if __name__ == "__main__":
    try:        
        main()
    except KeyboardInterrupt:
        print("\n\nTerminal session terminated.")
        sys.exit(0)