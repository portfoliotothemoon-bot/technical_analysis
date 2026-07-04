from datetime import datetime, timedelta
import pandas as pd
import yfinance as yf


def get_fibonacci_levels(ticker_symbol):
    # 1. Define the 3-month lookback period
    end_date = datetime.today()
    start_date = end_date - timedelta(days=90)

    # 2. Fetch historical data from Yahoo Finance
    ticker = yf.Ticker(ticker_symbol)
    df = ticker.history(start=start_date, end=end_date)

    if df.empty:
        return None, None

    # 3. Find the 3-month high and low
    period_high = float(df["High"].max())
    period_low = float(df["Low"].min())
    price_range = period_high - period_low

    # 4. Standard Fibonacci ratios
    ratios = [0.0, 0.236, 0.382, 0.500, 0.618, 0.786, 1.000]
    fib_rows = []

    # 5. Populate and format the structured rows for export
    for r in ratios:
        uptrend_level = period_high - (r * price_range)
        downtrend_level = period_low + (r * price_range)

        fib_rows.append(
            {
                "Ratio": f"{r * 100:.1f}%",
                "Uptrend (Support)": f"${uptrend_level:,.2f}",
                "Downtrend (Resistance)": f"${downtrend_level:,.2f}",
            }
        )

    # 6. Return values to the main script to fix the NoneType unpack crash
    return pd.DataFrame(fib_rows), (period_high, period_low)


# Example usage for testing when running this file directly
if __name__ == "__main__":
    df, extremes = get_fibonacci_levels("MRVL")
    if df is not None:
        high_val, low_val = extremes
        print(
            f"=== Standalone Test for MRVL ===\nHigh: ${high_val:.2f} | Low: ${low_val:.2f}\n"
        )
        print(df.to_string(index=False))
