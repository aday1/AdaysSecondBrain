#!/usr/bin/env python3
from datetime import datetime

MONTH_NAMES = [
    'January', 'February', 'March', 'April',
    'May', 'June', 'July', 'August',
    'September', 'October', 'November', 'December'
]

def format_timestamp(dt=None):
    """Format timestamp with month name (e.g., 'January' instead of '01')"""
    if dt is None:
        dt = datetime.now()
    month_name = MONTH_NAMES[dt.month - 1]
    return f"{dt.year}_{month_name}_{dt.day:02d}_{dt.hour:02d}{dt.minute:02d}{dt.second:02d}"

def parse_timestamp(timestamp):
    """Parse timestamp with month name back to datetime object"""
    try:
        # Split into parts
        year, month, day, time = timestamp.split('_')
        
        # Convert month name to number
        if month in MONTH_NAMES:
            month_num = MONTH_NAMES.index(month) + 1
        else:
            # Try to parse as a number for backward compatibility
            month_num = int(month)
        
        # Parse year and day
        year = int(year)
        day = int(day)
        
        # Parse time (HHMMSS)
        hour = int(time[:2])
        minute = int(time[2:4])
        second = int(time[4:]) if len(time) > 4 else 0
        
        return datetime(year, month_num, day, hour, minute, second)
    except (ValueError, IndexError):
        # For backward compatibility, try the old format
        try:
            return datetime.strptime(timestamp, '%Y%m%d_%H%M%S')
        except ValueError:
            raise ValueError("Invalid timestamp format")

def sort_timestamps(timestamps):
    """Sort timestamps in reverse chronological order"""
    return sorted(timestamps, key=parse_timestamp, reverse=True)
