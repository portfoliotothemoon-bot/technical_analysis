import yfinance as yf

def get_short_interest(ticker_symbol: str):
    """
    Fetch short interest data for a stock and return it as a dictionary.
    """
    try:
        stock = yf.Ticker(ticker_symbol)
        info = stock.info
        
        short_data = {
            "ticker": ticker_symbol.upper(),
            "shares_short": info.get("sharesShort"),
            "short_percent_float": info.get("shortPercentOfFloat"),
            "short_percent_outstanding": info.get("shortPercentOfSharesOutstanding"),
            "shares_short_prior_month": info.get("sharesShortPriorMonth"),
            "short_ratio": info.get("shortRatio"),           # Days to Cover
            "float_shares": info.get("floatShares"),
            "shares_outstanding": info.get("sharesOutstanding"),
            "last_updated": info.get("lastFiscalYearEnd")    # Not exact, but useful context
        }
        
        return short_data
        
    except Exception as e:
        print(f"Error fetching short interest for {ticker_symbol}: {e}")
        return None


# ============== Example Usage in your main script ==============
if __name__ == "__main__":
    ticker = "GME"   # Change as needed
    
    data = get_short_interest(ticker)
    
    if data:
        print(f"Short Interest for {data['ticker']}:")
        print(f"Shares Short: {data['shares_short']:,}")
        print(f"Short % of Float: {data['short_percent_float']}")
        print(f"Days to Cover: {data['short_ratio']}")
        
        # You can now use the values easily:
        short_percent = data["short_percent_float"]
        if short_percent and short_percent > 0.20:
            print("⚠️ High short interest!")