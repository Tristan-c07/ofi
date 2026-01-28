"""
Time Utilities
"""

from datetime import datetime, timedelta
from typing import List


def get_trading_days(start_date: datetime, end_date: datetime) -> List[datetime]:
    """
    Get trading days between start and end date
    
    Args:
        start_date: Start date
        end_date: End date
        
    Returns:
        list: List of trading days
    """
    # Placeholder implementation
    days = []
    current = start_date
    while current <= end_date:
        # Skip weekends (simplified, doesn't account for holidays)
        if current.weekday() < 5:
            days.append(current)
        current += timedelta(days=1)
    return days


def format_datetime(dt: datetime, fmt: str = "%Y-%m-%d %H:%M:%S") -> str:
    """
    Format datetime object to string
    
    Args:
        dt: Datetime object
        fmt: Format string
        
    Returns:
        str: Formatted datetime string
    """
    return dt.strftime(fmt)
