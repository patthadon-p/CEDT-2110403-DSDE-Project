"""
Visualize Module

This module provides map and geospatial visualization utilities
for the CEDT-2110403-DSDE-Project.

It provides direct access to the main visualizer classes used for
creating interactive plots and geospatial maps within Streamlit applications.

Classes
-------
LineChartVisualizer
    A class for generating interactive line charts (e.g., using Plotly).
MapVisualizer
    A class for creating dynamic and interactive map visualizations (e.g., using Folium or Plotly).

Usage:
    # Import everything
    from visualize import *

    # Import specific classes
    from visualize import MapVisualizer

    # Access directly
    import visualize
    m = visualize.MapVisualizer(df)
"""

# Import specific visualizer functions
from .LineChartVisualizer import LineChartVisualizer
from .MapVisualizer import MapVisualizer

# Define what gets imported with "from visualize import *"
__all__ = [
    # Classes
    # LineChartVisualizer.py
    "LineChartVisualizer",
    # MapVisualizer.py
    "MapVisualizer",
]
