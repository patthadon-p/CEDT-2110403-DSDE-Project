"""
Utilities for handling datetime and calendar conversions.

This module provides utility functions necessary for time-based calculations,
specifically converting the current Gregorian year (ค.ศ.) to the Buddhist year (พ.ศ.).

Functions
---------
get_buddhist_year
    Calculates and returns the current year in the Buddhist calendar (พ.ศ.).
"""

import datetime


def get_buddhist_year() -> str:
    """
    Calculates the current year in the Buddhist calendar (พ.ศ.) and returns it as a 4-digit string.

    The function adds 542 to the current Gregorian year (datetime.datetime.now().year).
    Note: The traditional conversion value for the Thai Buddhist calendar is +543.

    Returns
    -------
    str
        The current Buddhist year as a 4-digit string (e.g., "2567").
    """
    
    current_datetime = datetime.datetime.now()
    buddhist_year = current_datetime.year + 542
    last_two_digits = str(buddhist_year)

    return last_two_digits
