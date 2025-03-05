#!/usr/bin/env python3
"""
Created on Mon Mar  3 20:17:04 2025

@author: Dilaksan Thillaithevan
"""

from datetime import datetime, timedelta


def get_time_24hrs_ago() -> datetime:
    """Returns time 24 hours ago"""
    current_time = datetime.now()
    time_24_hours_ago = current_time - timedelta(days=1)
    return time_24_hours_ago


def dt_to_str(dt: datetime, format: str) -> str:
    return dt.strftime(format)


def str_to_dt(dt_str: datetime, format: str) -> str:
    return datetime.strptime(dt_str, format)
