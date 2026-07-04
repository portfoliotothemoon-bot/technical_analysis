from datetime import datetime, timedelta
import pandas as pd
import yfinance as yf


def get_fibonacci_levels(ticker_symbol):
    # 1. Define the 3-month lookback period
    end_date = datetime.today()
    start_date = end_date - timedelta(days=90)

    # 2. Fetch historical data from Yahoo Finance
    print(f"Fetching data for {ticker_symbol} from {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}...")
    ticker = yf.Ticker(ticker_symbol)
    df = ticker.history(start=start_date, end=end_date)

    if df.empty:
        print(f"No data found for ticker {ticker_symbol}.")
        return

    # 3. Find the 3-month high and low
    period_high = df["High"].max()
    period_low = df["Low"].min()
    price_range = period_high - period_low

    # 4. Standard Fibonacci ratios
    ratios = [0.0, 0.236, 0.382, 0.500, 0.618, 0.786, 1.000]

    # 5. Calculate levels for both market directions
    print(f"\n=== Fibonacci Levels for {ticker_symbol.upper()} ===")
    print(f"3-Month High: ${period_high:.2f}")
    print(f"3-Month Low:  ${period_low:.2f}\n")

    print(f"{'Ratio':<10} | {'Uptrend (Support)':<18} | {'Downtrend (Resistance)':<18}")
    print("-" * 55)

    for r in ratios:
        # Uptrend: Price pulled back from High down toward Low
        uptrend_level = period_high - (r * price_range)
        # Downtrend: Price bounced up from Low toward High
        downtrend_level = period_low + (r * price_range)

        percentage = f"{r * 100:.1f}%"
        print(
            f"{percentage:<10} | ${uptrend_level:<17.2f} | ${downtrend_level:<17.2f}"
        )


# Example usage: Calculate levels for Marvell Technology ($MRVL)
if __name__ == "__main__":
    get_fibonacci_levels("MRVL")
