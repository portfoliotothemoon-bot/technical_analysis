import yfinance as yf
import pandas as pd

def get_fibonacci_analysis(ticker, period="6mo"):
    try:
        data = yf.download(ticker, period=period, progress=False, auto_adjust=True)
        
        if data.empty or len(data) < 10:
            print(f"❌ Insufficient data for {ticker}")
            return
        
        high = data['High'].max()
        low = data['Low'].min()
        current = data['Close'].iloc[-1]
        diff = high - low
        
        print(f"\n📊 Enhanced Fibonacci Analysis → {ticker.upper()} ({period})")
        print("=" * 70)
        print(f"High     : ${high:,.2f}")
        print(f"Low      : ${low:,.2f}")
        print(f"Current  : ${current:,.2f}   |   Range: ${diff:,.2f}")
        print("=" * 70)

        # === FIBONACCI LEVELS ===
        print("\n🔼 UPTREND Retracements (Support)")
        up_levels = {
            "0% (High)": high,
            "23.6%": high - diff * 0.236,
            "38.2%": high - diff * 0.382,
            "50%": high - diff * 0.5,
            "61.8%": high - diff * 0.618,
            "78.6%": high - diff * 0.786,
            "100% (Low)": low,
        }
        for name, price in up_levels.items():
            print(f"{name:12} → ${price:,.2f}")

        print("\n🔽 DOWNTREND Retracements (Resistance)")
        down_levels = {
            "0% (Low)": low,
            "23.6%": low + diff * 0.236,
            "38.2%": low + diff * 0.382,
            "50%": low + diff * 0.5,
            "61.8%": low + diff * 0.618,
            "78.6%": low + diff * 0.786,
            "100% (High)": high,
        }
        for name, price in down_levels.items():
            print(f"{name:12} → ${price:,.2f}")

        # === RED FLAG WARNINGS ===
        print("\n🚨 RED FLAGS & SIGNALS:")
        warnings = []

        # 1. Proximity to key levels
        for name, price in {**up_levels, **down_levels}.items():
            distance_pct = abs(current - price) / price * 100
            if distance_pct < 1.0:   # Within 1%
                warnings.append(f"🔴 Price very close to {name} level (${price:,.2f})")

        # 2. Near major levels (50%, 61.8%)
        major_levels = [up_levels["50%"], up_levels["61.8%"], down_levels["50%"], down_levels["61.8%"]]
        for lvl in major_levels:
            if abs(current - lvl) / lvl * 100 < 2.0:
                warnings.append(f"🔴 Approaching strong Fibonacci level at ${lvl:,.2f}")

        # 3. Current position in range
        position = (current - low) / diff * 100
        if position < 25:
            warnings.append("🔴 Price near bottom of recent range (possible support test)")
        elif position > 75:
            warnings.append("🔴 Price near top of recent range (possible resistance test)")

        # 4. Recent momentum
        data['Return'] = data['Close'].pct_change()
        recent_return = data['Return'].tail(5).mean() * 100
        if recent_return < -3:
            warnings.append(f"🔴 Strong downward momentum last 5 days ({recent_return:.1f}%)")

        # Show warnings
        if warnings:
            for w in warnings:
                print(w)
        else:
            print("✅ No major red flags detected.")

        return warnings

    except Exception as e:
        print(f"❌ Error: {e}")


# Interactive
if __name__ == "__main__":
    print("🚀 Enhanced Fibonacci Technical Analyzer with Red Flags")
    while True:
        ticker = input("\nEnter ticker (or 'quit'): ").strip().upper()
        if ticker.lower() in ['quit','q','exit']: break
        period = input("Period [3mo/6mo/1y/max]: ").strip() or "6mo"
        get_fibonacci_analysis(ticker, period)