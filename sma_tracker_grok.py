import pandas as pd
import yfinance as yf
import sys

print("==================================================================================================================")
print(" QUANTITATIVE TRADING RADAR TERMINAL ENGINE v2.0")
print(" -> Type 'EXIT' to close safely.")
print("==================================================================================================================")

def calculate_fibonacci(high, low):
    diff = high - low
    return {
        "High": high,
        "Fib_236": high - diff * 0.236,
        "Fib_382": high - diff * 0.382,
        "Fib_500": high - diff * 0.500,
        "Fib_618": high - diff * 0.618,
        "Fib_786": high - diff * 0.786,
        "Low": low,
        # Extensions
        "Ext_127": high + diff * 1.272,
        "Ext_161": high + diff * 1.618,
    }

def main():
    while True:
        ticker_symbol = input("\nEnter stock ticker (or EXIT): ").strip().upper()
        
        if ticker_symbol == "EXIT":
            print("\nClosing terminal... Good luck!")
            break
        if not ticker_symbol:
            continue

        print(f"Fetching data for {ticker_symbol}...")

        try:
            ticker_meta = yf.Ticker(ticker_symbol)
            company_name = ticker_meta.info.get("longName", ticker_symbol)

            data = yf.download(ticker_symbol, period="2y", progress=False)
            
            if data.empty or len(data) < 100:
                print(f"[Warning] Insufficient data for {ticker_symbol}")
                continue

            # Flatten columns if needed
            if isinstance(data.columns, pd.MultiIndex):
                data.columns = data.columns.get_level_values(0)

            # === CORE INDICATORS ===
            data["20_SMA"] = data["Close"].rolling(20).mean()
            data["50_SMA"] = data["Close"].rolling(50).mean()
            data["200_SMA"] = data["Close"].rolling(200).mean()
            
            # RSI
            delta = data["Close"].diff()
            gain = delta.where(delta > 0, 0)
            loss = -delta.where(delta < 0, 0)
            avg_gain = gain.ewm(com=13, adjust=False).mean()
            avg_loss = loss.ewm(com=13, adjust=False).mean()
            rs = avg_gain / avg_loss.replace(0, float('nan'))
            data["RSI"] = 100 - (100 / (1 + rs))

            # Bollinger Bands
            data["20_Std"] = data["Close"].rolling(20).std()
            data["Upper_BB"] = data["20_SMA"] + (data["20_Std"] * 2)
            data["Lower_BB"] = data["20_SMA"] - (data["20_Std"] * 2)
            data["BB_Width"] = (data["Upper_BB"] - data["Lower_BB"]) / data["20_SMA"]

            data = data.dropna(subset=['20_SMA', '200_SMA', 'RSI'])

            latest = data.iloc[-1]
            high_2y = data["High"].max()
            low_2y = data["Low"].min()

            current = float(latest["Close"])
            rsi = float(latest["RSI"])
            bb_width = float(latest["BB_Width"])

            fib = calculate_fibonacci(high_2y, low_2y)

            # === DASHBOARD ===
            print("\n" + "="*100)
            print(f" ANALYSIS FOR: {company_name} ({ticker_symbol})")
            print("="*100)

            print(f"Current Price : ${current:,.2f} | RSI: {rsi:.1f} | BB Width: {bb_width:.4f}")
            print(f"52w High/Low  : ${high_2y:,.2f} / ${low_2y:,.2f}")

            # Fibonacci Table
            print("\nFIBONACCI LEVELS:")
            for name, price in fib.items():
                dist = ((current - price) / price * 100)
                marker = " ← CURRENT" if abs(dist) < 1.5 else ""
                print(f"  {name:8} → ${price:,.2f}   ({dist:+6.1f}%) {marker}")

            print("\n🚨 RED FLAG ALERTS:")
            alerts = []

            # Proximity to Fib levels
            for name, price in fib.items():
                if abs(current - price) / price < 0.015:   # Within 1.5%
                    alerts.append(f"🔴 Very close to {name} Fibonacci level")

            if rsi > 70: alerts.append("🔴 OVERBOUGHT (RSI > 70)")
            if rsi < 30: alerts.append("🟢 OVERSOLD (RSI < 30)")
            if current > fib["Ext_161"]: alerts.append("🔴 Highly extended above range")
            if bb_width < 0.05: alerts.append("🔴 Volatility Squeeze detected")

            if latest["Close"] > latest["Upper_BB"]: alerts.append("🔴 Price above Upper Bollinger Band")
            if latest["Close"] < latest["Lower_BB"]: alerts.append("🟢 Price below Lower Bollinger Band")

            if not alerts:
                print("   ✅ No major red flags")
            else:
                for alert in alerts:
                    print("   " + alert)

            print("="*100)

        except Exception as e:
            print(f"[Error] {str(e)}")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nSession terminated.")
        sys.exit(0)