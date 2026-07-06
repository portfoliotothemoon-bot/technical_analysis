#!/usr/bin/env python3
"""
Reusable FOMC Warning Module
"""

import requests
from bs4 import BeautifulSoup
from datetime import datetime, date
import re


def get_fomc_warning():
    """
    Returns a dictionary with FOMC warning information.
    
    Returns:
        dict: Contains warning message and details, or None if failed.
    """
    url = "https://www.federalreserve.gov/monetarypolicy/fomccalendars.htm"
    headers = {'User-Agent': 'Mozilla/5.0 (compatible; FOMC-Warning/1.0)'}
    
    try:
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
    except requests.RequestException:
        return {"error": "Failed to fetch FOMC calendar. Check internet connection."}

    soup = BeautifulSoup(response.text, 'html.parser')
    today = datetime.now().date()
    current_month = today.month
    current_year = today.year
    
    upcoming = []
    
    # Parse the calendar
    year_sections = soup.find_all(string=re.compile(r'(\d{4})\s+FOMC Meetings', re.I))
    
    for year_str in year_sections:
        year_match = re.search(r'(\d{4})', year_str)
        if not year_match:
            continue
        year = int(year_match.group(1))
        
        section = year_str.find_parent(['h3', 'h4', 'div']) or year_str.parent
        month = None
        
        for elem in section.find_all_next(True):
            if elem.name in ['h4', 'h3'] and re.search(r'FOMC Meetings', elem.get_text(), re.I):
                break
            
            text = elem.get_text(strip=True)
            if not text:
                continue
                
            month_match = re.match(r'^(January|February|March|April|May|June|July|August|September|October|November|December)', text)
            if month_match:
                month = month_match.group(1)
                continue
            
            date_match = re.match(r'^(\d{1,2})(?:-(\d{1,2}))?', text)
            if date_match and month:
                start_day = int(date_match.group(1))
                try:
                    month_num = datetime.strptime(month, '%B').month
                    meeting_date = datetime(year, month_num, start_day).date()
                    
                    if meeting_date >= today:
                        upcoming.append({
                            'date': meeting_date.strftime('%Y-%m-%d'),
                            'description': f"{month} {text}",
                            'full_date': meeting_date,
                            'month_num': month_num,
                            'year': year
                        })
                except ValueError:
                    pass
    
    # Deduplicate + sort
    seen = set()
    unique = []
    for m in upcoming:
        if m['date'] not in seen:
            seen.add(m['date'])
            unique.append(m)
    
    unique.sort(key=lambda x: x['full_date'])
    
    # Find meetings in current month
    same_month = [m for m in unique 
                  if m['year'] == current_year and m['month_num'] == current_month]
    
    warning = {
        "is_in_fomc_month": bool(same_month),
        "same_month_meetings": same_month,
        "today": today.strftime('%Y-%m-%d'),
        "upcoming_meetings": unique[:5]  # next 5 meetings
    }
    
    return warning


def print_fomc_warning():
    """Print the formatted warning (for standalone use)."""
    warning = get_fomc_warning()
    
    if not warning or "error" in warning:
        print("⚠️  Could not fetch FOMC data.")
        return
    
    print("="*70)
    print("⚠️  FOMC IMPORTANT WARNINGS")
    print("="*70)
    
    same_month = warning["same_month_meetings"]
    today = datetime.now().date()
    
    if same_month:
        print("🚨 HIGH ALERT: TODAY IS IN AN FOMC MEETING MONTH!\n")
        
        for m in same_month:
            days_until = (m['full_date'] - today).days
            
            if days_until == 0:
                print(f"   🔥 TODAY is the FOMC meeting day! ({m['date']})")
            elif days_until == 1:
                print(f"   ⚡ Tomorrow is the FOMC meeting ({m['date']})")
            else:
                print(f"   📅 Today is {days_until} days from the FOMC meeting on {m['date']}")
            
            print(f"      Announcement typically at 2:00 PM ET.")
    else:
        print("✅ No FOMC meeting this month.")
    
    print("\n" + "-"*70)
    print("• Dates are tentative until confirmed.")
    print("• Always verify at federalreserve.gov")
    print("="*70)


# For testing when running directly
if __name__ == "__main__":
    print_fomc_warning()