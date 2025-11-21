"""
Core module of the 'scrapping' package.

This module provides direct access to the main utility classes
for fetching and processing external data.

Classes
-------
PopulationScrapping
    Handles the process of scraping and cleaning DOPA population data.
"""

# Import specific classes and functions for direct access
from .BangkokIndexScrapping import BangkokIndexScrapping
from .PopulationScrapping import PopulationScrapping

# Define what gets imported with 'from scrapping import *'
__all__ = [
    # Classes
    # BangkokIndexScrapping.py"
    "BangkokIndexScrapping",
    # PopulationScrapping.py
    "PopulationScrapping",
]
