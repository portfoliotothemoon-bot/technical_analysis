import yfinance as yf
import pandas as pd
from typing import Optional


def get_yoy_dilution(ticker_symbol: str, use_diluted: bool = False) -> Optional[pd.DataFrame]:
    """
    Calculate Year-over-Year stock dilution for a given ticker.
    
    Args:
        ticker_symbol (str): Stock ticker symbol (e.g., 'AAPL')
        use_diluted (bool): If True, use Diluted Average Shares instead of Basic
    
    Returns:
        pd.DataFrame: Table with Shares and YoY Dilution %, or None if failed
    """
    try:
        ticker = yf.Ticker(ticker_symbol)
        
        # Get annual income statement
        income = ticker.income_stmt
        
        # Choose shares column
        shares_key = 'Diluted Average Shares' if use_diluted else 'Basic Average Shares'
        
        if shares_key not in income.index:
            print(f"Warning: {shares_key} not found. Trying fallback...")
            # Try alternative keys
            for key in ['Basic Average Shares', 'Diluted Average Shares']:
                if key in income.index:
                    shares_key = key
                    break
            else:
                print("Shares data not available in income statement.")
                return None
        
        shares = income.loc[shares_key].dropna()
        shares = shares.sort_index()  # Ensure chronological order
        
        if len(shares) < 2:
            print("Not enough historical data to calculate YoY dilution.")
            return None
        
        # Calculate YoY % change
        yoy_dilution = shares.pct_change() * 100
        yoy_dilution.name = "YoY Dilution (%)"
        
        result = pd.DataFrame({
            'Fiscal Year End': shares.index,
            'Shares Outstanding (Avg)': shares,
            'YoY Dilution (%)': yoy_dilution.round(2)
        }).reset_index(drop=True)
        
        # Format shares for readability (e.g., in millions)
        result['Shares Outstanding (Avg)'] = result['Shares Outstanding (Avg)'].apply(
            lambda x: f"{x:,.0f} ({x/1e6:.1f}M)"
        )
        
        return result
        
    except Exception as e:
        print(f"Error fetching data for {ticker_symbol}: {e}")
        return None


def print_dilution_summary(result: pd.DataFrame, ticker_symbol: str):
    """Print the result with warnings for high dilution."""
    if result is None:
        return
    
    print(result.to_string(index=False))
    
    # Check for significant dilution (>10%)
    high_dilution = result[result['YoY Dilution (%)'] > 10]
    if not high_dilution.empty:
        print("\n" + "="*60)
        print("⚠️  WARNING: Significant dilution detected!")
        for _, row in high_dilution.iterrows():
            year = row['Fiscal Year End'].strftime('%Y') if hasattr(row['Fiscal Year End'], 'strftime') else row['Fiscal Year End']
            print(f"   → {year}: +{row['YoY Dilution (%)']}% YoY dilution")
        print("="*60)