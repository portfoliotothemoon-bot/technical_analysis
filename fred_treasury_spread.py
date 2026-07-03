# fred_treasury_spread.py
import pandas_datareader.data as pdr
from datetime import datetime, timedelta

def get_treasury_yield_spread():
    """Returns latest Treasury yields and spread. Prints nicely too."""
    try:
        end = datetime.now()
        start = end - timedelta(days=10)
        
        data = pdr.get_data_fred(['DGS10', 'DGS2', 'T10Y2Y'], start, end)
        
        if data.empty:
            print("⚠️  Could not fetch Treasury data.")
            return None
            
        latest_10y = data['DGS10'].dropna().iloc[-1]
        latest_2y = data['DGS2'].dropna().iloc[-1]
        latest_spread = data['T10Y2Y'].dropna().iloc[-1]
        latest_date = data['T10Y2Y'].dropna().index[-1].date()
        
        print("\n" + "="*70)
        print("📈 MACRO CONTEXT - U.S. TREASURY YIELD CURVE")
        print("="*70)
        print(f"Latest Update : {latest_date}")
        print(f"10-Year Yield : {latest_10y:.3f}%")
        print(f"2-Year Yield  : {latest_2y:.3f}%")
        print(f"10Y - 2Y Spread: {latest_spread:.3f}%")
        
        if latest_spread < 0:
            print("🚨 YIELD CURVE INVERTED → Potential Recession Signal")
        elif latest_spread < 0.50:
            print("⚠️  Yield Curve is Flat")
        else:
            print("✅ Yield Curve Positive")
            
        return {
            '10y': latest_10y,
            '2y': latest_2y,
            'spread': latest_spread,
            'date': latest_date
        }
        
    except Exception as e:
        print(f"⚠️  Treasury data unavailable: {e}")
        return None