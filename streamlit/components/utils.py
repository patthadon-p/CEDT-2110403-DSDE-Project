# Standard library
import os
import sys
from collections.abc import Callable
from typing import Any

# External dependencies
import streamlit as st
from shapely.geometry import Point

# Ensure project root is in sys.path for imports
current_file = os.path.abspath(__file__)
project_root = os.path.abspath(os.path.join(current_file, "../../../"))

if project_root not in sys.path:
    sys.path.append(project_root)

# =================================================================
# Check for streamlit_js_eval existence for GPS functionality
# =================================================================
try:
    from streamlit_js_eval import get_geolocation

    _HAS_JS_EVAL = True

except ImportError:

    _HAS_JS_EVAL = False

    # Define a mock if not available, to prevent app crash but show a warning
    def get_geolocation() -> None:
        st.warning(
            "`streamlit_js_eval` not found. GPS functionality disabled. Please use Map/Manual input."
        )
        return None


# ================================================================


# ================================================================
# Check for scikit-learn existence for DBSCAN
# ================================================================
try:
    from sklearn.cluster import DBSCAN  # noqa: F401
    from sklearn.preprocessing import StandardScaler  # noqa: F401

    _HAS_SKLEARN = True

except ImportError:
    import pydeck as pdk

    _HAS_SKLEARN = False

    # Mock function to be used in visualizer.py
    def plot_dbscan_map(**kwargs: Any) -> pdk.Deck:
        st.error(
            "DBSCAN requires scikit-learn. Please install it using: pip install scikit-learn"
        )

        return pdk.Deck(
            initial_view_state=pdk.ViewState(latitude=13.75, longitude=100.51, zoom=9.5)
        )


# ================================================================

# ================================================================
# Mocking read_config_path for self-containment/testing if the actual import fails
# ===============================================================
try:
    from src.utils import read_config_path

except ImportError:
    # Using a simple file to avoid circular dependency in the original file structure
    def read_config_path(key: str, domain: str = "data", filepath: str = "") -> str:
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


# ==============================================================


# HELPER (From Second Block)
def add_margin(
    top: float = 0, right: float = 0, bottom: float = 0, left: float = 0
) -> None:
    st.markdown(
        f"<div style='margin:{top}px {right}px {bottom}px {left}px'></div>",
        unsafe_allow_html=True,
    )


# Helper for reverse geocoding (Requires external load_geo_data)
def find_location_from_coords(
    lat: float,
    lng: float,
    load_geo_data_func: Callable,
) -> tuple[str | None, str | None]:
    gdf = load_geo_data_func()
    if gdf is None:
        return None, None

    point = Point(lng, lat)
    match = gdf[gdf.geometry.contains(point)]

    if not match.empty:
        return match.iloc[0]["district_name"], match.iloc[0]["subdistrict_name"]

    return None, None
