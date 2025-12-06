# src/utils.py

import os
import sys

import streamlit as st
from shapely.geometry import Point

# NOTE: load_geo_data must be defined/imported in this scope or called from data_loader
# We'll rely on importing it from data_loader later for dependency management.

# Check for streamlit_js_eval existence for the second block's dependency
try:
    from streamlit_js_eval import get_geolocation

    _HAS_JS_EVAL = True
except ImportError:
    # Define a mock if not available, to prevent app crash but show a warning
    def get_geolocation():
        st.warning(
            "`streamlit_js_eval` not found. GPS functionality disabled. Please use Map/Manual input."
        )
        return None

    _HAS_JS_EVAL = False

# Check for scikit-learn existence for DBSCAN
try:
    from sklearn.cluster import DBSCAN
    from sklearn.preprocessing import StandardScaler

    _HAS_SKLEARN = True
except ImportError:
    _HAS_SKLEARN = False

    # Mock function to be used in visualizer.py
    def plot_dbscan_map(**kwargs):
        st.error(
            "DBSCAN requires scikit-learn. Please install it using: pip install scikit-learn"
        )
        import pydeck as pdk

        return pdk.Deck(
            initial_view_state=pdk.ViewState(latitude=13.75, longitude=100.51, zoom=9.5)
        )


# Fallback/Utility functions for data path (Kept Mocking for self-containment)
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.append(project_root)
# Mocking read_config_path for self-containment/testing if the actual import fails
try:
    from src.utils import read_config_path
except ImportError:
    # Using a simple file to avoid circular dependency in the original file structure
    def read_config_path(domain, key):
        MOCK_PATHS = {
            "cleansed_data_path": "./data/processed/cleansed_data.csv",
            "cleansed_geographic_data_path": "./data/processed/cleansed_geo.csv",
            "population_2565_scrapped_path": "./data/scrapped/population_subdistrict_2565.csv",
            "population_2566_scrapped_path": "./data/scrapped/population_subdistrict_2566.csv",
            "population_2567_scrapped_path": "./data/scrapped/population_subdistrict_2567.csv",
            "bangkok_index_scrapped_path": "./data/scrapped/bangkok_index_district_final.csv",
        }
        # Attempt to read from an environment variable if you have one set up for the data path
        return os.environ.get(key, MOCK_PATHS.get(key, f"path/to/{key}.csv"))


# HELPER (From Second Block)
def add_margin(t=0, r=0, b=0, l=0):
    """Adds vertical/horizontal margin using HTML markdown."""
    st.markdown(
        f"<div style='margin:{t}px {r}px {b}px {l}px'></div>", unsafe_allow_html=True
    )


# Helper for reverse geocoding (Requires external load_geo_data)
def find_location_from_coords(lat, lng, load_geo_data_func):
    """Performs reverse geocoding using the loaded GeoDataFrame."""
    gdf = load_geo_data_func()
    if gdf is None:
        return None, None
    point = Point(lng, lat)
    match = gdf[gdf.geometry.contains(point)]
    if not match.empty:
        return match.iloc[0]["district_name"], match.iloc[0]["subdistrict_name"]
    return None, None
