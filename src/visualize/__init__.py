"""
Visualize Module

This module provides map and geospatial visualization utilities
for the CEDT-2110403-DSDE-Project.

Usage:
    # Import everything
    from visualize import *

    # Import specific functions
    from visualize import MapVisualizer

    # Access directly
    import visualize
    m = visualize.MapVisualizer(df)
"""

# Import specific visualizer functions
from .MapVisualizer import MapVisualizer

# Define what gets imported with "from visualize import *"
__all__ = [
    # Classes
    # MapVisualizer.py
    "MapVisualizer",
]
