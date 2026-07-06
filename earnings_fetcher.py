# earnings_fetcher.py
import pandas as pd
import datetime

def get_next_earnings_date(ticker_obj):
    """Get next earnings date with multiple fallback methods"""
    today = datetime.datetime.now().date()
    
    try:
        calendar = ticker_obj.calendar
        if calendar is not None and not calendar.empty:
            if isinstance(calendar, pd.DataFrame):
                for col in calendar.columns:
                    for val in calendar[col]:
                        if pd.notna(val):
                            try:
                                dt = pd.to_datetime(val)
                                if dt.date() > today:
                                    return dt.strftime('%Y-%m-%d')
                            except:
                                continue
    except:
        pass

    # Fallback 1: get_earnings_dates
    try:
        earnings_df = ticker_obj.get_earnings_dates(limit=10)
        if earnings_df is not None and not earnings_df.empty:
            for idx in earnings_df.index:
                if hasattr(idx, 'date') and idx.date() > today:
                    return idx.strftime('%Y-%m-%d')
    except:
        pass

    # Fallback 2: ticker.info
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