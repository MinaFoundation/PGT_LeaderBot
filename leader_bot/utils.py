"""
Utility functions shared across the leader_bot package.
"""

from datetime import datetime


def convert_to_iso8601(date_str):
    """Convert a date string to ISO8601 format."""
    date_obj = datetime.strptime(date_str, "%Y-%m-%d")
    iso8601_str = date_obj.strftime("%Y-%m-%dT%H:%M:%SZ")
    return iso8601_str
