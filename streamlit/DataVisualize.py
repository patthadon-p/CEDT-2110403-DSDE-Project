# -----------------------------------------------------------------------------
# UNIFIED STREAMLIT APPLICATION: Bangkok Traffy Dashboard (MERGED)
# -----------------------------------------------------------------------------

# Import necessary libraries
import datetime
import os
import sys

import pandas as pd
import streamlit as st
import altair as alt
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pydeck as pdk
from streamlit_folium import st_folium
import geopandas as gpd
from shapely import wkt
from matplotlib.figure import Figure
import matplotlib.pyplot as plt
from matplotlib import rcParams # Import rcParams
import numpy as np
import folium
from shapely.geometry import Point

# Check for streamlit_js_eval existence for the second block's dependency
try:
    from streamlit_js_eval import get_geolocation
    _HAS_JS_EVAL = True
except ImportError:
    # Define a mock if not available, to prevent app crash but show a warning
    def get_geolocation():
        st.warning("`streamlit_js_eval` not found. GPS functionality disabled. Please use Map/Manual input.")
        return None
    _HAS_JS_EVAL = False

# Check for scikit-learn existence for DBSCAN
try:
    from sklearn.cluster import DBSCAN
    from sklearn.preprocessing import StandardScaler
    _HAS_SKLEARN = True
except ImportError:
    _HAS_SKLEARN = False
    def plot_dbscan_map(**kwargs):
        st.error("DBSCAN requires scikit-learn. Please install it using: pip install scikit-learn")
        return pdk.Deck(initial_view_state=pdk.ViewState(latitude=13.75, longitude=100.51, zoom=9.5))

rcParams["font.family"] = "Tahoma" # Set font family

# -----------------------------------------------------------------------------
# SETUP & CONFIGURATION
# -----------------------------------------------------------------------------

# Fallback/Utility functions (kept minimal for environment robustness)
# NOTE: The dependency on `src.utils.read_config_path` is assumed to be met 
# or mocked to return valid paths for the application to run.
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.append(project_root)
# Mocking read_config_path for self-containment/testing if the actual import fails
try:
    from src.utils import read_config_path
except ImportError:
    st.error("Cannot import `read_config_path`. Using mock paths.")
    def read_config_path(domain, key):
        MOCK_PATHS = {
            "cleansed_data_path": "./data/processed/mock_cleansed_data.csv",
            "cleansed_geographic_data_path": "./data/processed/mock_subdistrict_geo.csv",
            "population_2565_scrapped_path": "./data/scrapping/mock_pop_2022.csv",
            "population_2566_scrapped_path": "./data/scrapping/mock_pop_2023.csv",
            "population_2567_scrapped_path": "./data/scrapping/mock_pop_2024.csv",
            "bangkok_index_scrapped_path": "./data/scrapping/mock_bangkok_index.csv",
        }
        # Attempt to read from an environment variable if you have one set up for the data path
        return os.environ.get(key, MOCK_PATHS.get(key, f"path/to/{key}.csv"))


# --- LINECHARTVISUALIZER CLASS (Updated with Custom Hover Data) ---
class LineChartVisualizer:
    def __init__(self, df):
        self.df = df.copy()
        
        # 1. Expand data to handle multiple types per ticket
        self.df = self.df.explode("type_cleaned")
        self.df["type_cleaned"] = self.df["type_cleaned"].str.strip()
        
        # Ensure required columns are available (using the renamed 'year'/'month' columns)
        if "year" not in self.df.columns or "month" not in self.df.columns:
             # Fallback check for old column names just in case the rename failed in DataLoader
             if "timestamp_year" in self.df.columns:
                 self.df.rename(columns={"timestamp_year": "year", "timestamp_month": "month"}, inplace=True)
             else:
                 raise ValueError("DataFrame must have 'year' and 'month' columns for monthly grouping.")
        
        # 2. Create date column for sorting and grouping
        self.df['date_ts'] = pd.to_datetime(self.df[['year', 'month']].assign(day=1))
        
        # Filter out empty types
        self.df = self.df[self.df['type_cleaned'] != '']

    def plot(self, figsize: tuple = (12, 6)) -> go.Figure:
        
        # 3. Group by Year-Month and Type
        monthly_counts = (
            self.df.groupby([self.df['date_ts'].dt.to_period("M"), "type_cleaned"])
            .size()
            .reset_index(name="Count")
        )
        # Convert Period back to Timestamp for Plotly plotting
        monthly_counts['Date'] = monthly_counts['date_ts'].dt.to_timestamp()

        if monthly_counts.empty:
            fig = go.Figure()
            fig.update_layout(title="No data available for plotting.")
            return fig

        # 4. Create Plotly Line Chart (multi-series plot)
        # --- FIX: Use hover_data to specify only the important columns ---
        fig = px.line(
            monthly_counts, 
            x="Date", 
            y="Count", 
            color="type_cleaned", 
            title="Monthly Problem Counts by Type (All Types)",
            labels={"Count": "Number of Problems", "type_cleaned": "Problem Type"},
            height=600,
            # Specify the columns to appear in the hover box
            hover_data={
                "type_cleaned": True
            }
        )

        # 5. Customize Layout
        fig.update_traces(mode='lines', line=dict(width=2))
        fig.update_layout(
            legend_title_text='Problem Type',
            xaxis_title=None,
            hovermode="x", # Use 'x' to show combined tooltips for all series at a single date
            margin=dict(l=20, r=20, t=50, b=20)
        )

        return fig


# Streamlit page configuration
st.set_page_config(layout="wide", page_title="Bangkok Traffy Unified Dashboard")
st.markdown("""
    <style>
    section[data-testid="stSidebar"] .css-1d391kg {
        padding-bottom: 200px !important;
    }
    </style>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 0. HELPER (From Second Block)
# -----------------------------------------------------------------------------
def add_margin(t=0, r=0, b=0, l=0):
    """Adds vertical/horizontal margin using HTML markdown."""
    st.markdown(f"<div style='margin:{t}px {r}px {b}px {l}px'></div>", unsafe_allow_html=True)


# -----------------------------------------------------------------------------
# 1. DATA LOADER CLASS (Combined and Enhanced)
# -----------------------------------------------------------------------------
class TraffyDataLoader:
    
    default_start = datetime.date(2021, 9, 19)
    default_end = datetime.date(2025, 1, 16)
    
    @staticmethod
    @st.cache_data
    def load_cleansed() -> pd.DataFrame:
        path = read_config_path(domain="processed", key="cleansed_data_path")
        df = pd.read_csv(path)
        
        # Clean and split types
        df["type_cleaned"] = (
            df["type"].astype(str)
            .str.replace("{", "", regex=False)
            .str.replace("}", "", regex=False)
            .str.split(",").apply(tuple)
        )
        
        # 'type_clean' is the first type (for single type filtering)
        df["type_clean"] = df["type_cleaned"].apply(
            lambda x: x[0].strip() if isinstance(x, tuple) and len(x) > 0 else None
        )
        
        # Build datetime column for easy comparison
        df.rename(columns={
            "timestamp_year": "year",
            "timestamp_month": "month",
            "timestamp_date": "day"
        }, inplace=True)
        df["date"] = pd.to_datetime(df[["year", "month", "day"]])
        
        # Ensure numeric coordinates
        df["latitude"] = pd.to_numeric(df["latitude"], errors="coerce")
        df["longitude"] = pd.to_numeric(df["longitude"], errors="coerce")
        df = df.dropna(subset=["latitude", "longitude"])
        
        return df

    @staticmethod
    @st.cache_data
    def load_pop_data() -> dict[int, pd.DataFrame]:
        # Loads population data for 2022, 2023, 2024
        pop_data = {}
        for year, key in [(2022, "population_2565_scrapped_path"), 
                              (2023, "population_2566_scrapped_path"), 
                              (2024, "population_2567_scrapped_path")]:
            try:
                path = read_config_path(domain="scrapping", key=key)
                pop_data[year] = pd.read_csv(path)
            except Exception as e:
                st.error(f"Could not load population data for {year}: {e}")
                pop_data[year] = pd.DataFrame()
        return pop_data

    @staticmethod
    @st.cache_data
    def load_scores() -> pd.DataFrame:
        path = read_config_path(domain="scrapping", key="bangkok_index_scrapped_path")
        return pd.read_csv(path)

    @staticmethod
    @st.cache_data
    def get_unique_types(df: pd.DataFrame) -> list:
        clean_list = []
        for row in df["type_cleaned"]:
            for t in row:
                if pd.notna(t) and str(t).strip() != "":
                    clean_list.append(t.strip())
        return sorted(set(clean_list))

# --- Data Loading Helpers for Time Predictor (From Second Block) ---

@st.cache_data(show_spinner=False)
def load_and_process_predictor_data():
    """Loads a minimal set of data for the Time Predictor's dropdowns."""
    path = read_config_path(domain="processed", key="cleansed_data_path")
    # Added 'timestamp_month', 'timestamp_year' to help the hash in prepare_features
    cols = ["district", "subdistrict", "type", "organization", "timestamp_month", "timestamp_year"]
    df = pd.read_csv(path, usecols=lambda c: c in cols)
    
    district_map = (
        df.dropna(subset=["district", "subdistrict"])
        .groupby("district")["subdistrict"]
        .apply(lambda x: sorted(list(set(x))))
        .to_dict()
    )
    
    def clean_explode(c):
        s = df[c].astype(str).str.replace(r"[{}]", "", regex=True).str.split(",").explode().str.strip()
        return sorted(s[s != ""].unique().tolist())

    return district_map, clean_explode("type"), clean_explode("organization")

@st.cache_data(show_spinner=False)
def load_geo_data():
    """Loads the GeoDataFrame for reverse geocoding/map highlighting."""
    try:
        path = read_config_path(domain="processed", key="cleansed_geographic_data_path") 
        df = pd.read_csv(path)
        df['geometry'] = df['geometry'].apply(wkt.loads)
        gdf = gpd.GeoDataFrame(df, geometry='geometry')
        gdf.set_crs(epsg=4326, inplace=True)
        return gdf
    except Exception as e: 
        st.warning(f"Failed to load geographic data for reverse geocoding: {e}")
        return None

def find_location_from_coords(lat, lng):
    """Performs reverse geocoding using the loaded GeoDataFrame."""
    gdf = load_geo_data()
    if gdf is None: return None, None
    point = Point(lng, lat)
    match = gdf[gdf.geometry.contains(point)]
    if not match.empty:
        return match.iloc[0]['district_name'], match.iloc[0]['subdistrict_name']
    return None, None

# -----------------------------------------------------------------------------
# 2. FILTER & LOGIC CLASS (Centralized)
# -----------------------------------------------------------------------------
class TraffyFilter:
    
    def __init__(self, df: pd.DataFrame):
        self.df = df
        self.type_list = TraffyDataLoader.get_unique_types(df)
        self.default_start = TraffyDataLoader.default_start
        self.default_end = TraffyDataLoader.default_end

    def render_sidebar(self):
        st.sidebar.title("🛠️ Navigation & Filters")
        
        # --- Navigation ---
        page_options = {
            "Spatial Analysis": "Map",
            "Scatter Analysis": "Scatter",
            "Line Chart": "Line",
            "Time Predictor": "Predictor" # <--- ADDED PAGE
        }
        selected_page = st.sidebar.radio(
            "Select View", 
            list(page_options.keys())
        )
        st.sidebar.markdown("---")
        
        # Filter settings are only necessary for the first three pages
        if selected_page != "Time Predictor":
            st.sidebar.header("Filter Settings")

            # --- Filter Form ---
            with st.sidebar.form("filter_form"):
                selected_type = st.selectbox("เลือกประเภทปัญหา", options=["ทั้งหมด"] + self.type_list)
                date_range = st.date_input(
                    "เลือกช่วงวัน",
                    value=[self.default_start, self.default_end],
                    min_value=self.default_start,
                    max_value=self.default_end,
                )
                
                # Normalize date range
                if isinstance(date_range, tuple) and len(date_range) == 2:
                    start_date, end_date = date_range
                else:
                    start_date = end_date = date_range[0]
                    
                submit = st.form_submit_button("Apply Filter")

            # Store filter values in session state
            if submit or "type_filter" not in st.session_state:
                st.session_state["type_filter"] = selected_type
                st.session_state["start_date"] = start_date
                st.session_state["end_date"] = end_date

            self.current_type = st.session_state.get("type_filter", "ทั้งหมด")
            self.current_start = st.session_state.get("start_date", self.default_start)
            self.current_end = st.session_state.get("end_date", self.default_end)
        else:
            # Predictor page doesn't need data filtering here
            self.current_type = "ทั้งหมด"
            self.current_start = self.default_start
            self.current_end = self.default_end
            start_date = self.default_start
            end_date = self.default_end
            
        return page_options[selected_page], self.current_type, self.current_start, self.current_end

    def apply_filters(self, filter_type: bool = True, filter_date: bool = True) -> pd.DataFrame:
        df_filtered = self.df.copy()
        
        if filter_date:
            start_ts = pd.Timestamp(self.current_start)
            end_ts = pd.Timestamp(self.current_end)
            
            # Apply date mask
            date_mask = (df_filtered["date"] >= start_ts) & (df_filtered["date"] <= end_ts)
            df_filtered = df_filtered[date_mask]
        
        if filter_type and self.current_type != "ทั้งหมด":
            # Apply type mask (using the list of types)
            type_mask = df_filtered["type_cleaned"].apply(lambda x: self.current_type in x)
            df_filtered = df_filtered[type_mask]

        return df_filtered

# -----------------------------------------------------------------------------
# 3. MODEL LOGIC (Time Predictor - From Second Block)
# -----------------------------------------------------------------------------
class TraffyTimePredictor:
    """Mock-up predictor model logic."""
    def __init__(self):
        self.d_map, self.p_types, self.orgs = load_and_process_predictor_data()

    def _sparse_vec(self, size, idx):
        u = sorted(list(set(idx)))
        return f"({size}, {u}, {[1.0]*len(u)})"

    def prepare_features(self, district, subdistrict, types, orgs, date, lat, long):
        tm = int(date.month); ty = int(date.year)
        dh = hash(district)%2048; sh = hash(subdistrict)%2048
        ti = [self.p_types.index(t) for t in types if t in self.p_types]
        oi = [hash(o)%1786 for o in orgs]
        
        return {
            "timestamp_month": tm, "timestamp_year": ty,
            "address_encoded": self._sparse_vec(2048, [dh, sh]),
            "latlong_encoded": [float(lat), float(long)],
            "organization_encoded": self._sparse_vec(1786, oi),
            "type_encoded": self._sparse_vec(25, ti)
        }

    def predict(self, model_input):
        base = 3.0
        # Mock logic: odd-indexed problem types (like 'ความสะอาด', 'PM2.5') increase base time
        try:
            # Extract the indices from the sparse vector string
            ts_str = model_input["type_encoded"].split('[')[1].split(']')[0]
            if ts_str: 
                # Check if any index (before the comma, as a string) is odd-indexed. 
                # This is a very rough mock and depends on the specific p_types list.
                # Simplified for demonstration purposes only.
                indices = [int(x.strip()) for x in ts_str.split(',') if x.strip() and x.strip().isdigit()]
                if any(i % 2 != 0 for i in indices): 
                    base += 5.0
        except: 
            # Fallback if parsing fails
            pass
            
        # Add random variation to mock the prediction
        val = max(1, base + np.random.uniform(-1, 5))
        lvl = "Fast (เร็ว)" if val < 3 else "Normal (ปกติ)" if val < 10 else "Slow (ช้า)"
        return round(val, 1), lvl

# --- State Management & Callbacks (Time Predictor - From Second Block) ---

def handle_pending_updates():
    """Applies pending coordinate updates and runs reverse geocoding."""
    if "pending_coords" in st.session_state:
        lat = st.session_state.pending_coords["lat"]
        lng = st.session_state.pending_coords["lng"]
        src = st.session_state.pending_coords["source"]
        
        # 1. Update Coordinates
        st.session_state["confirmed_lat"] = lat
        st.session_state["confirmed_long"] = lng
        st.session_state["location_source"] = src
        
        # 2. Reverse Geocode (Fix: Explicitly set dropdown values)
        d, s = find_location_from_coords(lat, lng)
        if d and s:
            st.session_state["sb_district"] = d
            st.session_state["sb_subdistrict"] = s
            st.session_state["geo_match_found"] = True
        else:
            st.session_state["geo_match_found"] = False
            
        del st.session_state["pending_coords"]

def clear_coordinates():
    """Resets all coordinate-related session state."""
    st.session_state["confirmed_lat"] = None
    st.session_state["confirmed_long"] = None
    st.session_state["location_source"] = None
    st.session_state["geo_match_found"] = None
    # Reset Dropdowns to default
    st.session_state["sb_district"] = "--- Select District ---"
    st.session_state["sb_subdistrict"] = None


# -----------------------------------------------------------------------------
# 4. PLOTTING FUNCTIONS (Copied from original for functionality)
# -----------------------------------------------------------------------------

# --- Plotting Helpers for Map Visualizer ---
# Note: These functions require geopandas and shapely to run.

import pandas as pd
import geopandas as gpd
from shapely import wkt
import pydeck as pdk
import json # Import json for GeoJSON conversion

def plot_choroplethmap(df: pd.DataFrame, region_path: str, type_filter: str | None = None, value_column: str = "count"):
    df_points = df.copy()
    if type_filter and type_filter != "ทั้งหมด":
        # Need to use the full 'type_cleaned' tuple column to filter
        df_points = df_points[df_points["type_cleaned"].apply(lambda x: type_filter in x)]
    
    # 1. Prepare data
    gdf_points = gpd.GeoDataFrame(
        df_points,
        geometry=gpd.points_from_xy(df_points["longitude"], df_points["latitude"]),
        crs="EPSG:4326",
    )
    df_region = pd.read_csv(region_path)
    df_region["geometry"] = df_region["geometry"].map(wkt.loads)
    gdf_region = gpd.GeoDataFrame(df_region, geometry="geometry", crs="EPSG:4326")
    joined = gpd.sjoin(gdf_points, gdf_region, how="left", predicate="within")

    # 2. Aggregate counts
    # Ensure the column name used for grouping is correct from the joined GeoDataFrame
    agg_df = joined.groupby("subdistrict_name").size().reset_index(name="count")

    # 3. Merge and fill
    gdf_merged = gdf_region.merge(agg_df, on="subdistrict_name", how="left")
    gdf_merged["count"] = gdf_merged["count"].fillna(0)

    # --- Pydeck Specific Steps ---

    # 4. Compute map center
    # Use the centroid of the combined area for initial view
    center_latlon = gdf_merged.to_crs(epsg=3857).geometry.unary_union.centroid
    center_latlon = gpd.GeoSeries([center_latlon], crs="EPSG:3857").to_crs(epsg=4326).geometry[0]
    
    # Convert GeoDataFrame to GeoJSON
    # Set the coloring column as the GeoJSON feature property
    geojson_data = json.loads(gdf_merged.to_json())

    # 5. Define the Pydeck Layer
    # Use GeoJsonLayer for the choropleth
    # Pydeck uses a JavaScript expression for coloring. A simple way is to use a color scale function.
    # Note: Pydeck doesn't have a direct equivalent to Folium's explore/colormap, so color scale creation is simplified here.
    
    # Simple color function (using an expression) - This will need fine-tuning for a proper choropleth scale
    # For a basic choropleth, we can use a fixed orange color and vary opacity or use a utility if available.
    # A cleaner approach is pre-calculating the color or using a library like colorcet/palettable if available.
    
    # Placeholder for a gradient color expression based on 'count'
    # This is a very basic example; for a real production choropleth, you'd define bins/scales better.
    # Using 'get_fill_color' to map the 'count' property to a color (e.g., [R, G, B, A] array)
    max_count = gdf_merged["count"].max()
    
    if max_count == 0:
        max_count = 1 # Avoid division by zero
    
    # Simple color expression: higher count -> more opaque orange ([255, 140, 0] is DarkOrange)
    # The A (alpha) channel will scale from 0 to 255 based on the count value.
    color_expression = f"[255, 140, 0, (properties.count / {max_count}) * 255]"

    geojson_layer = pdk.Layer(
        "GeoJsonLayer",
        geojson_data,
        opacity=0.8,
        stroked=True,
        filled=True,
        extruded=False,
        wireframe=True,
        get_fill_color=color_expression,
        get_line_color=[100, 100, 100],
        line_width_min_pixels=1,
        pickable=True, # Enable hover/tooltip
        auto_highlight=True,
    )

    # 6. Define the View State
    view_state = pdk.ViewState(
        latitude=center_latlon.y,
        longitude=center_latlon.x,
        zoom=9,
        min_zoom=9,
        max_zoom=16,
    )

    # 7. Create the Deck
    r = pdk.Deck(
        layers=[geojson_layer],
        initial_view_state=view_state,
        map_style='light',
        tooltip={
            "html": "<b>Subdistrict:</b> {subdistrict_name}<br/><b>District:</b> {district_name}<br/><b>Count:</b> {count}",
            "style": {"color": "white"},
        }
    )

    return r

def plot_choroplethmap_perpop(df: pd.DataFrame, region_path: str, type_filter: str | None = None, value_column: str = "probperpop"):
    df_region = pd.read_csv(region_path)
    df_region["geometry"] = df_region["geometry"].map(wkt.loads)
    gdf_region = gpd.GeoDataFrame(df_region, geometry="geometry", crs="EPSG:4326")
    region_geom = gdf_region[["subdistrict_name", "geometry"]].copy()

    df_points = df.copy()
    if type_filter and type_filter != "ทั้งหมด":
        df_points = df_points[df_points["type_cleaned"].apply(lambda x: type_filter in x)]

    # Aggregate counts and mean population (using 'subdistrict-name' from pop data)
    # NOTE: Assuming 'subdistrict-name' is correctly named for pop data in df
    agg_df = df_points.groupby("subdistrict-name").agg(
        count=("subdistrict-name", "size"),
        total=("total", "mean") 
    ).reset_index()
    agg_df.rename(columns={"subdistrict-name": "subdistrict_name"}, inplace=True)
    agg_df["probperpop"] = agg_df["count"] / agg_df["total"].fillna(1) 

    # Merge aggregated data back to region GeoDataFrame
    gdf_merged = region_geom.merge(agg_df, on="subdistrict_name", how="left")
    gdf_merged["probperpop"] = gdf_merged["probperpop"].fillna(0)
    gdf_merged["count"] = gdf_merged["count"].fillna(0) 

    # --- Pydeck Specific Steps ---
    
    # 1. Compute map center
    center_latlon = gdf_merged.to_crs(epsg=3857).geometry.unary_union.centroid
    center_latlon = gpd.GeoSeries([center_latlon], crs="EPSG:3857").to_crs(epsg=4326).geometry[0]

    # Convert GeoDataFrame to GeoJSON
    geojson_data = json.loads(gdf_merged.to_json())

    # 2. Define the Pydeck Layer
    max_probperpop = gdf_merged["probperpop"].max()
    
    if max_probperpop == 0:
        max_probperpop = 1 # Avoid division by zero

    # Simple color expression: higher probperpop -> more opaque orange
    color_expression = f"[255, 140, 0, (properties.probperpop / {max_probperpop}) * 255]"

    geojson_layer = pdk.Layer(
        "GeoJsonLayer",
        geojson_data,
        opacity=0.8,
        stroked=True,
        filled=True,
        extruded=False,
        wireframe=True,
        get_fill_color=color_expression,
        get_line_color=[100, 100, 100],
        line_width_min_pixels=1,
        pickable=True, # Enable hover/tooltip
        auto_highlight=True,
    )

    # 3. Define the View State
    view_state = pdk.ViewState(
        latitude=center_latlon.y,
        longitude=center_latlon.x,
        zoom=9,
        min_zoom=9,
        max_zoom=16,
    )

    # 4. Create the Deck
    r = pdk.Deck(
        layers=[geojson_layer],
        initial_view_state=view_state,
        map_style='light',
        tooltip={
            "html": "<b>Subdistrict:</b> {subdistrict_name}<br/><b>Incidents per Pop:</b> {probperpop}",
            "style": {"color": "white"},
        }
    )

    return r

# Heatmap function (assuming Pydeck/Pandas is installed)
def plot_heatmap(
    df: pd.DataFrame,
    lon_col: str = "longitude",
    lat_col: str = "latitude",
    max_points: int = 100_000,
):
    """Creates a Pydeck HeatmapLayer visualization."""
    
    # --- 1. Sampling and Data Preparation ---
    if len(df) > max_points:
        st.warning(f"Dataset too large ({len(df):,} rows). Showing a sample of {max_points:,} points.")
        df_plot = df.sample(max_points).copy()
    else:
        df_plot = df.copy()
        
    # Ensure coordinates are numeric
    df_plot = df_plot.dropna(subset=[lat_col, lon_col])

    cols_to_select = [lon_col, lat_col, "subdistrict", "district", "day", "month", "year", "comment", 'type_cleaned']
    df_small = df_plot[[col for col in cols_to_select if col in df_plot.columns]]

    # --- 2. Pydeck Layer Configuration ---
    heatmap_layer = pdk.Layer(
        "HeatmapLayer",
        data=df_small,
        opacity=1,
        # Get coordinates for the heatmap
        get_position=[lon_col, lat_col],
        radius_pixels=25, 
        threshold=0.5,
    )

    # --- 3. View State and Deck ---
    if df_plot.empty:
        # Default view state if no data
        view_state = pdk.ViewState(latitude=13.75, longitude=100.51, zoom=9.5, pitch=0)
    else:
        # Center the map on the data
        view_state = pdk.ViewState(
            latitude=df_plot[lat_col].mean(),
            longitude=df_plot[lon_col].mean(),
            zoom=9.5,
            pitch=0,
        )

    deck = pdk.Deck(
        layers=[heatmap_layer],
        initial_view_state=view_state,
        map_style="dark",
    )
    return deck

# Scatter Map function
def plot_scatter_map(
    df: pd.DataFrame,
    max_points: int = 100_000,
    lon_col: str = "longitude",
    lat_col: str = "latitude",
    type_col: str = "type_clean", # Use 'type_clean' for single-type coloring
):
    # --- 1. Sampling and Data Preparation ---
    if len(df) > max_points:
        st.warning(f"Dataset too large ({len(df):,} rows). Showing a sample of {max_points:,} points.")
        df_plot = df.sample(max_points).copy()
    else:
        df_plot = df.copy()

    # --- 2. Color Mapping Setup ---
    COLOR_MAP = {
        # โครงสร้างพื้นฐาน/ถนน - ส้มเข้ม
        "ถนน": [255, 140, 0], "ทางเท้า": [255, 140, 0], "สะพาน": [255, 140, 0], 
        "กีดขวาง": [255, 140, 0], "ป้าย": [255, 140, 0], "ป้ายจราจร": [255, 140, 0],
        
        # สิ่งแวดล้อม/สุขภาวะ - เขียวเข้ม
        "ความสะอาด": [34, 139, 34], "ห้องน้ำ": [34, 139, 34], "คลอง": [34, 139, 34], 
        "PM2.5": [34, 139, 34], "เสียงรบกวน": [34, 139, 34],

        # น้ำ/สาธารณูปโภค - ฟ้าอ่อน
        "น้ำท่วม": [0, 191, 255], "ท่อระบายน้ำ": [0, 191, 255], "สายไฟ": [0, 191, 255], 
        "แสงสว่าง": [0, 191, 255],

        # สังคม/ความปลอดภัย - แดง
        "ความปลอดภัย": [255, 0, 0], "สัตว์จรจัด": [255, 0, 0], "คนจรจัด": [255, 0, 0],

        # การบริการ/อื่นๆ - ชมพูเข้ม
        "การเดินทาง": [255, 20, 147], "ต้นไม้": [255, 20, 147],

        # การสื่อสาร - น้ำเงินอมเทา
        "ร้องเรียน": [70, 130, 180], "สอบถาม": [70, 130, 180], "เสนอแนะ": [70, 130, 180],
        
        # ค่าว่าง
        "nan": [192, 192, 192],      
        "Other": [128, 128, 128],    
    }

    # Function to get color from the map, defaulting to 'Other' color
    def get_color(type_value):
        if pd.isna(type_value):
            return COLOR_MAP["Other"]
        return COLOR_MAP.get(str(type_value).strip(), COLOR_MAP["Other"])

    df_plot["color_rgb"] = df_plot[type_col].apply(get_color)

    # Select the columns needed for the map and tooltip
    cols_to_select = [lon_col, lat_col, "subdistrict", "district", "day", "month", "year", "comment", "color_rgb", type_col]
    df_small = df_plot[[col for col in cols_to_select if col in df_plot.columns]]

    # --- 3. Pydeck Layer Configuration ---
    scatter_layer = pdk.Layer(
        "ScatterplotLayer",
        df_small,
        get_position=[lon_col, lat_col],
        get_radius=100,
        # **Use the 'color_rgb' column for coloring**
        get_fill_color="color_rgb",
        pickable=True,
        opacity=0.7, 
    )

    # --- 4. View State and Deck ---
    view_state = pdk.ViewState(
        latitude=df_plot[lat_col].mean(),
        longitude=df_plot[lon_col].mean(),
        zoom=9.5,
        pitch=0,
    )

    # Update tooltip to include the 'type_clean' information
    deck = pdk.Deck(
        layers=[scatter_layer],
        initial_view_state=view_state,
        tooltip={
            "html": (
                "<b>Type:</b> {" + type_col + "}<br/>"
                "<b>Location:</b> {subdistrict} {district}<br/>"
                "<b>Date:</b> {day}/{month}/{year}<br/>"
                "<b>Comment:</b> {comment}"
            ),
            "style": {"color": "white"}
        },
    )
    return deck

def plot_dbscan_map(
    df: pd.DataFrame,
    eps: float,
    min_samples: int,
    top_n: int = 5,  # Kept top_n but your logic colors all non-noise clusters
    lon_col: str = "longitude",
    lat_col: str = "latitude",
    max_points: int = 100_000,
):
    """
    Performs DBSCAN clustering on spatial data using user-defined parameters
    and visualizes all non-noise clusters using a dynamic continuous colormap.
    """
    try:
        from sklearn.cluster import DBSCAN
        from sklearn.preprocessing import StandardScaler
        import matplotlib.pyplot as plt # Required for colormap
    except ImportError:
        # This error handling is already done at the top of the file via _HAS_SKLEARN check
        st.error("DBSCAN requires scikit-learn and matplotlib. Please install them.")
        return pdk.Deck(initial_view_state=pdk.ViewState(latitude=13.75, longitude=100.51, zoom=9.5))

    if df.empty or len(df) < min_samples:
        st.info("Insufficient data for clustering with current filters/parameters.")
        return pdk.Deck(initial_view_state=pdk.ViewState(latitude=13.75, longitude=100.51, zoom=9.5))

    # --- 1. Data Preparation and Scaling (Same as original) ---
    if len(df) > max_points:
        df_plot = df.sample(max_points, random_state=42).copy()
        st.warning(f"Dataset too large ({len(df):,} rows). Showing a sample of {max_points:,} points.")
    else:
        df_plot = df.copy()

    cols_to_keep = [lon_col, lat_col, "subdistrict", "district", 'type_cleaned', "type_clean"]
    optional_cols = ["day", "month", "year", "comment"] 
    for col in optional_cols:
        if col in df_plot.columns and col not in cols_to_keep:
            cols_to_keep.append(col)

    df_plot = df_plot[[col for col in cols_to_keep if col in df_plot.columns]].copy()

    # Prepare coordinates for clustering
    coords = df_plot[[lat_col, lon_col]]
    scaler = StandardScaler()
    coords_scaled = scaler.fit_transform(coords)

    # --- 2. DBSCAN Clustering (Your Logic) ---
    # Use unscaled coordinates for final output, scaled for clustering fit
    db = DBSCAN(eps=eps, min_samples=min_samples).fit(coords_scaled)
    df_plot['cluster'] = db.labels_

    # Filter out noise points, as requested
    df_clustered = df_plot[df_plot['cluster'] != -1].copy()

    if df_clustered.empty:
        st.info("DBSCAN found no clusters (all points classified as noise) with current parameters.")
        return pdk.Deck(initial_view_state=pdk.ViewState(latitude=13.75, longitude=100.51, zoom=9.5))

    # --- 3. Dynamic Coloring (Your Logic) ---
    # Count the number of points in each cluster
    # NOTE: clusters_count is now based only on non-noise points
    unique_clusters = sorted(df_clustered['cluster'].unique())
    num_clusters = len(unique_clusters)
    
    # Use a continuous colormap to generate colors
    colormap = plt.get_cmap('hsv')
    # Generate an RGB color list for each unique cluster ID
    cluster_colors = {
        cluster: [int(x * 255) for x in colormap(i / num_clusters)[:3]] + [255] # Added Alpha=255
        for i, cluster in enumerate(unique_clusters)
    }
    
    # Map cluster ID to color for each row in the dataframe
    df_clustered['color'] = df_clustered['cluster'].map(cluster_colors)
    # Ensure color column is a list of [R, G, B, A] for pydeck
    
    # --- 4. Pydeck Layer Configuration (Your Logic) ---
    scatter_layer = pdk.Layer(
        "ScatterplotLayer",
        df_clustered,
        get_position="[longitude, latitude]",
        get_color='color',
        # Adjusted radius from 200 (meters, as per your code) to 50 for better visual density in Streamlit example
        get_radius=50, 
        opacity=0.8,
        pickable=True,
    )
    
    # --- 5. View State and Deck ---
    view_state = pdk.ViewState(
        latitude=df_clustered['latitude'].mean(),
        longitude=df_clustered['longitude'].mean(),
        zoom=10,
        pitch=0,
    )

    # Use the requested tooltip, ensuring all columns are available in df_clustered
    deck = pdk.Deck(
        layers=[scatter_layer],
        initial_view_state=view_state,
        map_style="dark", # Use a dark map style for better visibility
        tooltip={
            "html": "<b>Cluster:</b> {cluster}<br/><b>Location:</b> {subdistrict} {district}<br/><b>Date:</b> {day}/{month}/{year}<br/><b>Type:</b> {type_clean}",
            "style": {"color": "white"}
        },
    )
    return deck 

# --- Plotting Helpers for Data Analysis ---
class TraffyVisualizer:
    
    @staticmethod
    def plot_daily_counts(df: pd.DataFrame, type_label: str):
        label = type_label if type_label != "ทั้งหมด" else "ทั้งหมด"
        st.subheader(f"Timeline: {label}")
        
        daily_counts = (
            df.groupby(["year", "month", "day"]).size().reset_index(name="count")
        )

        if daily_counts.empty:
            st.warning("No data for this selection.")
            return

        daily_counts["date"] = pd.to_datetime(daily_counts[["year", "month", "day"]])
        daily_counts["year_month"] = daily_counts["date"].dt.to_period("M").astype(str)

        fig = px.scatter(
            daily_counts, x="date", y="count", color="year_month",
            labels={"date": "Date", "count": "Issues", "year_month": "Month"},
            hover_data=["date", "count"],
        )
        fig.add_trace(px.line(daily_counts, x="date", y="count").data[0])
        fig.update_traces(marker=dict(size=6, opacity=0.8))
        fig.update_layout(
            height=380, margin=dict(l=20, r=20, t=30, b=20),
            legend_title_text=None, hovermode="x unified"
        )
        st.plotly_chart(fig, use_container_width=True)

    @staticmethod
    def plot_score_vs_complaints(df_filtered: pd.DataFrame, df_score: pd.DataFrame):
        if "district" not in df_filtered.columns or df_score.empty: return
        
        complaints = df_filtered.groupby("district").size().reset_index(name="complaints")
        merged = df_score.merge(complaints, on="district", how="left")
        merged["complaints"] = merged["complaints"].fillna(0)

        if merged["complaints"].sum() == 0:
            st.info("No complaints found.")
            return

        low_score_th = merged["total_score"].quantile(0.3)
        high_complaints_th = merged["complaints"].quantile(0.7)

        def get_zone(row):
            if row["total_score"] < low_score_th and row["complaints"] > high_complaints_th: return "Danger"
            elif row["total_score"] >= low_score_th and row["complaints"] > high_complaints_th: return "Active"
            elif row["total_score"] < low_score_th and row["complaints"] <= high_complaints_th: return "Silent Risk"
            else: return "Good"

        merged["zone"] = merged.apply(get_zone, axis=1)
        zone_order = ["Danger", "Active", "Silent Risk", "Good"]
        color_map = {"Danger": "red", "Active": "#ff7f0e", "Silent Risk": "#2ca02c", "Good": "#1f77b4"}

        fig = px.scatter(
            merged, x="total_score", y="complaints", color="zone",
            category_orders={"zone": zone_order}, color_discrete_map=color_map,
            hover_data=["district", "total_score", "complaints"],
            title="Total Score vs Complaints"
        )
        
        fig.update_traces(marker=dict(size=12, opacity=0.8))
        fig.add_vline(x=float(low_score_th), line_dash="dash", line_color="gray", opacity=0.5)
        fig.add_hline(y=float(high_complaints_th), line_dash="dash", line_color="gray", opacity=0.5)
        
        fig.update_layout(
            height=510 , margin=dict(l=20, r=20, t=60, b=20),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1, title=None)
        )
        st.plotly_chart(fig, use_container_width=True)
        


    @staticmethod
    def plot_quality_dimensions(df_filtered: pd.DataFrame, df_score: pd.DataFrame):
        if "district" not in df_filtered.columns or df_score.empty: return

        complaints = df_filtered.groupby("district").size().reset_index(name="complaints")
        merged = df_score.merge(complaints, on="district", how="left")
        merged["complaints"] = merged["complaints"].fillna(0)

        metrics = ["public_service", "economy", "welfare", "environment"]
        titles = {m: m.replace("_", " ").title() for m in metrics}

        fig = make_subplots(rows=2, cols=2, subplot_titles=[titles[m] for m in metrics])

        for i, m in enumerate(metrics):
            row, col = i // 2 + 1, i % 2 + 1
            fig.add_trace(
                go.Scatter(
                    x=merged[m], y=merged["complaints"], mode="markers",
                    marker=dict(size=10, opacity=1, color=merged["complaints"], colorscale="RdYlBu", reversescale=True, showscale=False),
                    text=merged["district"],
                    hovertemplate=f"<b>%{{text}}</b><br>{titles[m]}: %{{x}}<br>Complaints: %{{y}}<extra></extra>"
                ), row=row, col=col
            )
            fig.update_xaxes(title_text=None, row=row, col=col, showgrid=True)
            fig.update_yaxes(showgrid=True, row=row, col=col)

        fig.update_yaxes(matches="y")
        fig.update_layout(
            height=500, showlegend=False, title_text="Dimensions vs Complaints",
            margin=dict(l=40, r=20, t=60, b=40),
        )
        st.plotly_chart(fig, use_container_width=True)
        

    @staticmethod
    def plot_heatmap_metric_vs_type(df_base: pd.DataFrame, df_score: pd.DataFrame):
        df = df_base.dropna(subset=["type_clean"]).copy()
        df = df[df["type_clean"].astype(str).str.strip() != ""]
        if df.empty or df_score.empty: return

        pivot_types = (
            df.groupby(["district", "type_clean"]).size()
            .reset_index(name="complaints")
            .pivot(index="district", columns="type_clean", values="complaints")
            .fillna(0).reset_index()
        )
        corr_df = df_score.merge(pivot_types, on="district", how="left").fillna(0)
        
        metric_cols = ["total_score", "public_service", "economy", "welfare", "environment"]
        type_cols = [c for c in corr_df.columns if c not in metric_cols + ["district"]]
        if not type_cols: return

        corr_matrix = corr_df[metric_cols + type_cols].corr(method="pearson")
        corr_sub = corr_matrix.loc[metric_cols, type_cols].reset_index().melt(
            id_vars="index", var_name="problem_type", value_name="corr"
        ).rename(columns={"index": "metric"})

        heatmap = alt.Chart(corr_sub).mark_rect().encode(
            x=alt.X("problem_type:N", title=None, sort=type_cols),
            y=alt.Y("metric:N", title=None, sort=metric_cols),
            color=alt.Color("corr:Q", scale=alt.Scale(scheme="redblue", domain=[-1, 0, 1])),
            tooltip=["metric", "problem_type", alt.Tooltip("corr", format=".2f")]
        ).properties(
            height=350, title="Correlation: Metric x Type"
        )
        st.altair_chart(heatmap, use_container_width=True)
        

    @staticmethod
    def plot_heatmap_type_vs_type(df_base: pd.DataFrame):
        triangle_mode = st.radio(
            "Mode:", ["Full", "Upper", "Lower"], 
            index=2, horizontal=True, key="heat_mode"
        )

        df = df_base.dropna(subset=["type_clean"]).copy()
        df = df[df["type_clean"].astype(str).str.strip() != ""]
        if df.empty: return

        pivot_problems = (
            df.groupby(["district", "type_clean"]).size()
            .reset_index(name="complaints")
            .pivot(index="district", columns="type_clean", values="complaints")
            .fillna(0)
        )
        if pivot_problems.shape[1] < 2: 
            st.info("Not enough problem types selected for correlation.")
            return

        corr_matrix = pivot_problems.corr(method="pearson")
        corr_long = corr_matrix.reset_index().melt(
            id_vars="type_clean", var_name="problem_type_2", value_name="corr"
        ).rename(columns={"type_clean": "problem_type_1"})

        problem_list = list(corr_matrix.index)
        idx_map = {p: i for i, p in enumerate(problem_list)}
        corr_long["i"] = corr_long["problem_type_1"].map(idx_map)
        corr_long["j"] = corr_long["problem_type_2"].map(idx_map)

        if triangle_mode == "Upper": corr_long = corr_long[corr_long["i"] < corr_long["j"]]
        elif triangle_mode == "Lower": corr_long = corr_long[corr_long["i"] > corr_long["j"]]

        cell_size = 25 if len(problem_list) > 15 else 35
        
        heatmap = alt.Chart(corr_long).mark_rect().encode(
            x=alt.X("problem_type_2:N", title=None),
            y=alt.Y("problem_type_1:N", title=None),
            color=alt.Color("corr:Q", scale=alt.Scale(scheme="redblue", domain=[-1, 0, 1])),
            tooltip=["problem_type_1", "problem_type_2", alt.Tooltip("corr", format=".2f")]
        ).properties(
            width=cell_size * (len(problem_list)*1.5),
            height=cell_size * (len(problem_list)*1.5),
            title="Correlation: Type x Type"
        )
        st.altair_chart(heatmap, use_container_width=False)

    @staticmethod
    def plot_scatter_matrix(df_time_filtered: pd.DataFrame):
        df = df_time_filtered.dropna(subset=["type_clean"]).copy()
        df = df[df["type_clean"].astype(str).str.strip() != ""]
        
        options = sorted(df["type_clean"].unique())
        selected = st.multiselect(
            "Select Types (2-4 recommended)", options=options,
            default=options[:3] if len(options) >= 3 else options,
            key="matrix_select"
        )

        if len(selected) < 2:
            st.warning("Select at least 2 types.")
            return

        matrix_df = (
            df[df["type_clean"].isin(selected)]
            .groupby(["district", "type_clean"]).size()
            .reset_index(name="count")
            .pivot_table(index="district", columns="type_clean", values="count", aggfunc="sum", fill_value=0)
            .reset_index()
        )

        dim_cols = [t for t in selected if t in matrix_df.columns]
        
        fig = px.scatter_matrix(
            matrix_df, dimensions=dim_cols, color="district",
            hover_data=["district"], title=None
        )
        fig.update_traces(marker=dict(size=8, opacity=0.9))
        fig.update_layout(
            height=600, margin=dict(l=30, r=30, t=30, b=30),
            plot_bgcolor="#FFFFFF", paper_bgcolor="white"
        )
        st.plotly_chart(fig, use_container_width=True)


# -----------------------------------------------------------------------------
# 5. PAGE RENDERERS
# -----------------------------------------------------------------------------

# --- Page 1: Map Visualizer (Traffy Map Visualize) ---
def render_map_visualizer(df_cleansed: pd.DataFrame, pop_data: dict, type_filter: str, start_date: datetime.date, end_date: datetime.date):
    st.title("🗺️ Bangkok Traffy Spatial Analysis")
    st.markdown("---")
    
    # --- New: Map Selection Radio Button ---
    map_mode = st.radio(
        "Select Map Visualization Mode:",
        ("Choropleth/Top 10", "Heatmap", "Scatter Plot", "DBSCAN Clustering"),
        horizontal=True
    )
    st.markdown("---")
    
    # 1. Filter dataset and merge with population data
    df_filtered_raw = df_cleansed[
        (df_cleansed["date"] >= pd.Timestamp(start_date)) & 
        (df_cleansed["date"] <= pd.Timestamp(end_date))
    ].copy()
    
    if type_filter != "ทั้งหมด":
        type_mask = df_filtered_raw["type_cleaned"].apply(lambda x: type_filter in x)
        df_filtered_raw = df_filtered_raw[type_mask].copy()

    dfs_with_pop = []
    for year, pop_df in pop_data.items():
        df_year = df_filtered_raw[df_filtered_raw['year'] == year]
        if not df_year.empty and not pop_df.empty:
            df_merged = pd.merge(
                df_year, pop_df, 
                left_on=["district", "subdistrict"], 
                right_on=["district-name", "subdistrict-name"], 
                how="left"
            )
            dfs_with_pop.append(df_merged)
    
    dfwithpop = pd.concat(dfs_with_pop, ignore_index=True)
    
    if dfwithpop.empty:
        st.info("No data available for the selected filters.")
        return

    # --- Core Metric Calculation (Always needed for Top 10) ---
    total_issues = len(dfwithpop)
    unique_districts = dfwithpop['district'].nunique()
    type_label = type_filter if type_filter != "ทั้งหมด" else ""
    region_path = read_config_path(domain="processed", key="cleansed_geographic_data_path")
    
    # --- Section 1: Key Metrics (KPIs) ---
    st.header("🎯 Key Spatial Metrics")
    kpi1, kpi2, kpi3 = st.columns(3)
    
    with kpi1:
        st.metric("จำนวนปัญหาทั้งหมด", f"{total_issues:,}")
    with kpi2:
        st.metric("ช่วงเวลาการวิเคราะห์", f"{start_date.strftime('%Y-%m-%d')} - {end_date.strftime('%Y-%m-%d')}")
    with kpi3:
        st.metric("เขตที่ได้รับผลกระทบ", f"{unique_districts:,} เขต")
    st.markdown("---")

    # --- CONDITIONAL MAP RENDERING ---
    
    if map_mode == "Choropleth/Top 10":
        st.header(f"🌎 แผนที่วิเคราะห์ปัญหา{type_label}ตามพื้นที่")
        
        # Compute Top 10 Tables
        top10_district = (
            dfwithpop.groupby("subdistrict")
            .size()
            .sort_values(ascending=False)
            .head(10)
            .reset_index(name="จำนวนปัญหา")
        )
        top10_district.columns = ["แขวง", "จำนวนปัญหา"] 
        
        agg_rate_df = dfwithpop.groupby("subdistrict-name").agg(
            count=("subdistrict-name", "size"), 
            total=("total", "mean") 
        ).reset_index()
        agg_rate_df["probperpop"] = (agg_rate_df["count"] / agg_rate_df["total"].fillna(1) * 1000).round(2) 
        
        top10_perpop = (
            agg_rate_df.sort_values(by="probperpop", ascending=False)
            .head(10)
            [["subdistrict-name", "probperpop"]]
        )
        top10_perpop.columns = ["แขวง", "ความรุนแรง"] 
        
        col1, col2 = st.columns([3, 1])

        with col1:
            st.subheader("จำนวนปัญหาต่อแขวง (Choropleth: Count)")
            choroplethmap = plot_choroplethmap(df=dfwithpop, region_path=region_path, type_filter=type_filter)
            st.pydeck_chart(choroplethmap, use_container_width=True, height=380)
            
            
            st.markdown("---") 
            
            st.subheader("ความรุนแรงของปัญหาต่อแขวง (Choropleth: Per Population)")
            choroplethmapperpop = plot_choroplethmap_perpop(df=dfwithpop, region_path=region_path, type_filter=type_filter)
            st.pydeck_chart(choroplethmapperpop, use_container_width=True, height=380)
            

        with col2:      
            st.subheader(f"1. แขวงที่มีจำนวนปัญหา{type_label}มากที่สุด")
            st.dataframe(top10_district.style.format({"จำนวนปัญหา": "{:,.0f}"}), use_container_width=True)
            st.subheader(f"2. แขวงที่มีความรุนแรงของปัญหา{type_label}สูงที่สุด")
            st.dataframe(top10_perpop.style.format({"ความรุนแรง": "{:,.2f}"}), use_container_width=True)

    elif map_mode == "DBSCAN Clustering":
        st.header(f"🌀 DBSCAN Cluster Analysis of Problems {type_label}")
        st.caption("DBSCAN groups dense points together, identifying key hotspots.")
        
        # --- DBSCAN Controls ---
        col_db1, col_db2, col_db3 = st.columns(3)
        with col_db1:
            eps_val = st.slider("1. Cluster Radius (EPS)", 
                                 min_value=0.01, max_value=0.5, 
                                 value=0.05, step=0.01, format="%.2f")
        with col_db2:
            min_samples_val = st.slider("2. Min Cluster Size", 
                                         min_value=5, max_value=100, 
                                         value=25, step=5)
        with col_db3:
            top_n_val = st.slider("3. Top Clusters to Highlight (N)", 
                                 min_value=1, max_value=10, 
                                 value=5, step=1)
        
        st.markdown("---") 
        
        # --- DBSCAN Map ---
        if _HAS_SKLEARN:
            dbscan_map = plot_dbscan_map(
                df=dfwithpop, 
                eps=eps_val, 
                min_samples=min_samples_val, 
                top_n=top_n_val
            ) 
            st.pydeck_chart(dbscan_map, use_container_width=True, height=600)
            
        else:
            plot_dbscan_map() # This calls the error message

    elif map_mode == "Heatmap":
        st.header(f"🔥 แผนที่ความหนาแน่นของปัญหา{type_label} (Heatmap)")
        heatmap = plot_heatmap(dfwithpop) 
        st.pydeck_chart(heatmap, use_container_width=True, height=600)
        

    elif map_mode == "Scatter Plot":
        st.header(f"📍 แผนที่แสดงจุดที่เกิดปัญหา{type_label} (Scatter Map)")
        scatter_map = plot_scatter_map(dfwithpop) 
        st.pydeck_chart(scatter_map, use_container_width=True, height=600)
        

    st.markdown("---")
    
# --- Page 2: Data Analysis (Datascatter) ---
def render_analysis_page(df_filtered: pd.DataFrame, df_score: pd.DataFrame, type_filter: str, df_time_only: pd.DataFrame):
    st.title("📊 Bangkok Traffy Data Analysis")
    visualizer = TraffyVisualizer()

    # 1. Score vs Complaints & Quality Dimensions (Applies type and date filter)
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("📌 Overview: Score vs Complaints")
        visualizer.plot_score_vs_complaints(df_filtered, df_score)
    
    with c2:
        st.subheader("📌 Quality Dimensions")
        visualizer.plot_quality_dimensions(df_filtered, df_score)
    
    st.markdown("---")

    # 2. Correlations & Scatter Matrix (Applies date filter only - uses df_time_only)
    t1, t2, t3 = st.tabs(["🔥 Correlation (Metric)", "🔥 Correlation (Type)", "📊 Scatter Matrix"])

    with t1:
        st.subheader("Correlation: Metric x Problem Type")
        visualizer.plot_heatmap_metric_vs_type(df_time_only, df_score)
    
    with t2:
        st.subheader("Correlation: Problem Type x Problem Type")
        visualizer.plot_heatmap_type_vs_type(df_time_only)
        
    with t3:
        st.subheader("Multi-Type Scatter Matrix")
        visualizer.plot_scatter_matrix(df_time_only)

# --- Page 3: Line Chart (Line Chart Viewer) ---
def render_line_chart_page(df_cleansed: pd.DataFrame, df_filtered: pd.DataFrame, type_filter: str):
    st.title("📈 Bangkok Traffy Line Chart Viewer")
    
    # 1. Daily Counts (Timeline)
    visualizer = TraffyVisualizer()
    visualizer.plot_daily_counts(df_filtered, type_filter)
    st.markdown("---")
    

    # 2. Monthly Trend by Type (Original LineChartVisualizer)
    st.subheader("Monthly Problem Counts by Type (All Types)")
    try:
        # Renaming columns back is still necessary if the external class is being used
        # We rename 'year' back to the name the original LineChartVisualizer expected: 'timestamp_year'
        df_for_viz = df_cleansed.copy()
        
        col_map = {
            'year': 'timestamp_year',
            'month': 'timestamp_month',
            'day': 'timestamp_date'
        }
        
        cols_to_rename = {old: new for old, new in col_map.items() if old in df_for_viz.columns}
        if cols_to_rename:
            df_for_viz.rename(columns=cols_to_rename, inplace=True)
        
        # Now instantiate and plot
        viz = LineChartVisualizer(df_for_viz)
        fig = viz.plot()
        
        # Display using Plotly command (as defined by the updated LineChartVisualizer)
        st.plotly_chart(fig, use_container_width=True) 
        
        
    except Exception as e:
        st.error(f"Error rendering Line Chart: {e}. Please check the `LineChartVisualizer` definition.")
        st.info("Debugging note: The DataFrame passed has columns: " + ", ".join(df_cleansed.columns))


# --- Page 4: Time Predictor (New Page) ---
def render_prediction_page():
    st.title("🔮📅 Time Predictor Model 📅🔮")
    add_margin(b=10)
    st.subheader("Estimate Resolution Time for a New Report")
    
    # Initialize the predictor inside the page render, so it reloads on session reset (if cached)
    try: 
        p = TraffyTimePredictor()
    except Exception as e: 
        st.error(f"Prediction Model Initialization Error: {e}. Check data paths or dependencies.")
        return
        
    # UI Logic for input and prediction
    render_input_section(p)

def render_input_section(predictor):
    """Renders the entire input and prediction UI."""
    handle_pending_updates()
    
    # Ensure session state is initialized for coordinates
    if "confirmed_lat" not in st.session_state:
        st.session_state.update({"confirmed_lat": None, "confirmed_long": None, "location_source": None, "geo_match_found": None, "sb_district": "--- Select District ---", "sb_subdistrict": None})

    # --- 1. GENERAL INFORMATION ---
    st.subheader("1. Date selection")
    c1, _ = st.columns([1, 1])
    with c1:
        report_date = st.date_input(
            "Report Date", 
            value=datetime.date.today(),
            max_value=datetime.date.today()
        )
    
    add_margin(t=20); st.markdown("---")

    # --- 2. EXACT LOCATION ---
    st.subheader("2. Exact Location & Area")
    
    # Toggle Input Method
    input_mode = st.radio("Input Method:", ["📍 Use Current Location (GPS)", "🗺️ Select on Map / Manual"], horizontal=True, label_visibility="collapsed")
    add_margin(t=10)

    col_map, col_info = st.columns([1, 1], gap="large")

    current_district_val = None
    current_subdistrict_val = None

    # --- RIGHT COLUMN: INFO & DROPDOWNS (Logic Priority) ---
    with col_info:
        if input_mode == "🗺️ Select on Map / Manual":
            st.markdown("##### Identified Area")
            st.caption("Select manually or click map to auto-fill.")
            
            d_opts = ["--- Select District ---"] + sorted(list(predictor.d_map.keys()))
            
            # District Dropdown
            sb_d_val = st.session_state.get("sb_district", "--- Select District ---")
            d_idx = d_opts.index(sb_d_val) if sb_d_val in d_opts else 0
            
            # Use a key to force the widget to use the session state value
            sel_d = st.selectbox("District", d_opts, index=d_idx, key="sb_district_widget")
            
            # Update session state *after* the widget value is confirmed (Streamlit's mechanics)
            if sel_d != st.session_state.get("sb_district"):
                st.session_state["sb_district"] = sel_d
                st.session_state["sb_subdistrict"] = None 
                st.rerun() # Rerun to update subdistrict options

            # Subdistrict Dropdown
            if sel_d == "--- Select District ---":
                st.selectbox("Subdistrict", ["(Select District first)"], disabled=True)
                sel_s = None
            else:
                s_opts = sorted(predictor.d_map[sel_d])
                # Ensure the stored value is valid for the current district
                sb_s_val = st.session_state.get("sb_subdistrict")
                if sb_s_val not in s_opts: sb_s_val = s_opts[0] if s_opts else None
                
                s_idx = s_opts.index(sb_s_val) if sb_s_val in s_opts else 0
                
                sel_s = st.selectbox("Subdistrict", s_opts, index=s_idx, key="sb_subdistrict_widget")
                
                if sel_s != st.session_state.get("sb_subdistrict"):
                    st.session_state["sb_subdistrict"] = sel_s
                    st.rerun() # Rerun to update map zoom
            
            # Set the current area for prediction/map logic
            current_district_val = sel_d
            current_subdistrict_val = sel_s

        else:
            # GPS Mode: Hide Dropdowns
            st.markdown("##### Identified Area (GPS)")
            if st.session_state.get("location_source") == "Current GPS" and st.session_state.get("geo_match_found"):
                d = st.session_state.get("sb_district")
                s = st.session_state.get("sb_subdistrict")
                st.info(f"📍 **{d}** > **{s}**")
                current_district_val = d
                current_subdistrict_val = s
            elif st.session_state.get("location_source") == "Current GPS" and not st.session_state.get("geo_match_found"):
                 st.info("📍 **Coordinates confirmed, but no matching district/subdistrict found.**")
                 current_district_val = None # Ensure it doesn't try to use bad values
                 current_subdistrict_val = None
            else:
                st.info("Waiting for location...")
                current_district_val = None
                current_subdistrict_val = None
            
        add_margin(t=10)
        st.markdown("##### Coordinates")
        
        if st.session_state["confirmed_lat"]:
            c_coord, c_clear = st.columns([3, 1])
            with c_coord:
                st.success(f"**{st.session_state['confirmed_lat']:.6f}, {st.session_state['confirmed_long']:.6f}**", icon="✅")
            with c_clear:
                st.button("🗑️ Clear", on_click=clear_coordinates, use_container_width=True, help="Reset coordinates")
        else:
            st.warning("No coordinates confirmed yet.", icon="⏳")

    # --- LEFT COLUMN: MAP ---
    with col_map:
        if input_mode == "🗺️ Select on Map / Manual":
            st.markdown("**📍 Point Selection**")
            st.caption("Click map then 'Confirm Pin'.")
            
            gdf = load_geo_data()
            center = [13.7563, 100.5018]; zoom = 11
            target_geo = None

            # Zoom Logic: Confirmed Pin > Selected Area > Default Center
            if st.session_state["confirmed_lat"]:
                center = [st.session_state["confirmed_lat"], st.session_state["confirmed_long"]]
                zoom = 15
            elif gdf is not None and current_district_val and current_district_val != "--- Select District ---":
                try:
                    t = gdf[gdf['district_name'] == current_district_val]
                    if current_subdistrict_val:
                        sub_t = t[t['subdistrict_name'] == current_subdistrict_val]
                        if not sub_t.empty: t = sub_t; zoom = 14
                        else: zoom = 12
                    else: zoom = 12 # Zoom to district
                    
                    if not t.empty:
                        c = t.geometry.centroid.iloc[0]
                        center = [c.y, c.x]
                        target_geo = t
                except: pass

            m = folium.Map(location=center, zoom_start=zoom)
            
            if target_geo is not None:
                folium.GeoJson(target_geo, style_function=lambda x: {'fillColor': '#ffaf00', 'color': 'red', 'weight': 2, 'fillOpacity': 0.1}).add_to(m)
            
            if st.session_state["confirmed_lat"]:
                folium.Marker([st.session_state["confirmed_lat"], st.session_state["confirmed_long"]], icon=folium.Icon(color="green", icon="check")).add_to(m)

            m.add_child(folium.LatLngPopup())
            
            map_key = f"map_{current_district_val}_{current_subdistrict_val}_{st.session_state['confirmed_lat']}"
            map_data = st_folium(m, height=380, width=None, key=map_key, returned_objects=["last_clicked"])

            if map_data and map_data.get("last_clicked"):
                if st.button("✅ Confirm Pin", use_container_width=True):
                    st.session_state["pending_coords"] = {
                        "lat": map_data["last_clicked"]["lat"],
                        "lng": map_data["last_clicked"]["lng"],
                        "source": "Map Selection"
                    }
                    st.rerun()
        else:
            # GPS Mode
            st.markdown("**📍 GPS Selection**")
            if _HAS_JS_EVAL:
                 st.info("Click below to use browser location.")
                 add_margin(t=10)
                 geo_data = get_geolocation() # This is non-blocking
                 
                 # The button triggers the rerun *if* geo_data is ready on the next run
                 if st.button("📡 Get My Location & Auto-Fill", use_container_width=True):
                     if geo_data:
                         st.session_state["pending_coords"] = {
                             "lat": geo_data['coords']['latitude'],
                             "lng": geo_data['coords']['longitude'],
                             "source": "Current GPS"
                         }
                         st.rerun()
                     else:
                         st.warning("Waiting for data... Click again after allowing location access.")
                 add_margin(b=80)
            else:
                 st.error("GPS functionality disabled. Set `_HAS_JS_EVAL = True` or install `streamlit-js-eval`.")
                 add_margin(b=80)


    add_margin(t=20); st.markdown("---")

    # --- 3. DETAILS ---
    st.subheader("3. Agencies & Issues")
    c1, c2 = st.columns(2)
    with c1: orgs = st.multiselect("Responsible Organization", predictor.orgs)
    with c2: types = st.multiselect("Problem Type", predictor.p_types)
    
    add_margin(t=30)
    if st.button("🚀 Compute Prediction", type="primary", use_container_width=True):
        if not current_district_val or current_district_val == "--- Select District ---":
            st.error("⚠️ Select District"); return
        if not st.session_state["confirmed_lat"]:
            st.error("⚠️ Confirm Location"); return
        if not orgs or not types:
            st.error("⚠️ Fill Details"); return
            
        features = predictor.prepare_features(
            current_district_val, current_subdistrict_val, types, orgs,
            report_date, st.session_state["confirmed_lat"], st.session_state["confirmed_long"]
        )
        with st.spinner("Predicting..."):
            d, l = predictor.predict(features)
        display_results(d, l, features)

def display_results(days, level, features):
    """Renders the prediction results."""
    add_margin(t=30)
    st.markdown("---")
    st.markdown("### 📊 Analysis Report")
    
    col_card1, col_card2 = st.columns(2)
    def card(title, value, color="#f0f2f6"):
        return f"""<div style="background-color:{color};padding:20px;border-radius:10px;border:1px solid #e0e0e0;"><p style="margin:0;font-size:14px;color:#555;">{title}</p><h2 style="margin:0;font-size:28px;color:#000;">{value}</h2></div>"""

    level_color = "#d4edda" if "Fast" in level else "#fff3cd" if "Normal" in level else "#f8d7da"
    
    with col_card1: st.markdown(card("Estimated Resolution", f"**{days}** Days"), unsafe_allow_html=True)
    with col_card2: st.markdown(card("Risk Category", f"**{level}**", color=level_color), unsafe_allow_html=True)

    add_margin(t=20)
    c_chart = st.container()
    with c_chart:
        st.markdown("#### Time-to-Fix Gauge")
        fig = go.Figure(go.Indicator(
            mode = "gauge+number+delta", value = days,
            domain = {'x': [0, 1], 'y': [0, 1]},
            title = {'text': "Days to Resolve", 'font': {'size': 18, 'color': "gray"}},
            delta = {'reference': 7, 'increasing': {'color': "red"}, 'decreasing': {'color': "green"}},
            gauge = {
                'axis': {'range': [None, 30], 'tickwidth': 1, 'tickcolor': "#333"},
                'bar': {'color': "#2b2b2b", 'thickness': 0.25}, 'bgcolor': "white", 'borderwidth': 2, 'bordercolor': "#eee",
                'steps': [
                    {'range': [0, 3], 'color': "#2ecc71"}, {'range': [3, 7], 'color': "#f1c40f"},
                    {'range': [7, 14], 'color': "#e67e22"}, {'range': [14, 30], 'color': "#e74c3c"}
                ],
                'threshold': {'line': {'color': "red", 'width': 4}, 'thickness': 0.75, 'value': days}
            }
        ))
        fig.update_layout(height=450, margin=dict(l=30, r=30, t=50, b=20), paper_bgcolor="rgba(0,0,0,0)", font={'family': "Arial"})
        st.plotly_chart(fig, use_container_width=True)
        
        st.markdown("""<div style="display:flex;justify-content:center;gap:15px;font-size:0.9em;margin-top:-10px;"><div><span style='color:#2ecc71;font-weight:bold;'>■</span> 0-3 Fast</div><div><span style='color:#f1c40f;font-weight:bold;'>■</span> 3-7 Moderate</div><div><span style='color:#e67e22;font-weight:bold;'>■</span> 7-14 Slow</div><div><span style='color:#e74c3c;font-weight:bold;'>■</span> 14+ Very Slow</div></div>""", unsafe_allow_html=True)
        
        with st.expander("🤖 Technical Details and Feature Vector", expanded=False):
            st.info("""**Prediction Factors:**\n* **Location (District/Subdistrict):** Density and historical performance.\n* **Issue Type:** Complexity weight based on problem type (e.g., 'Flood', 'Road').\n* **Organization:** Assigned agency historical resolution time.\n* **Date:** Month/Year for seasonality.\n\n*Note: This is a simplified mock model for demonstration.*""")
            st.code(str(features), language="json")
            st.caption("Raw input vector passed to the prediction model.")


# -----------------------------------------------------------------------------
# 6. MAIN APP CONTROLLER
# -----------------------------------------------------------------------------
class TraffyApp:
    def __init__(self):
        self.df_cleansed = TraffyDataLoader.load_cleansed()
        self.df_score = TraffyDataLoader.load_scores()
        self.pop_data = TraffyDataLoader.load_pop_data()
        self.filter_manager = TraffyFilter(self.df_cleansed)
        
    def run(self):
        # Navigation and Filter Setup
        selected_page, type_filter, start_date, end_date = self.filter_manager.render_sidebar()
        
        # Data Filtering
        # Filtered by date AND selected type (used for maps, daily counts, score analysis)
        df_filtered = self.filter_manager.apply_filters(filter_type=True, filter_date=True)
        
        # Filtered by date only (used for correlation/scatter matrix where all types are needed)
        df_time_only = self.filter_manager.apply_filters(filter_type=False, filter_date=True)

        # Content Rendering based on Navigation
        if selected_page == "Map":
            render_map_visualizer(self.df_cleansed, self.pop_data, type_filter, start_date, end_date)
        elif selected_page == "Scatter":
            # Pass df_filtered and df_time_only
            render_analysis_page(df_filtered, self.df_score, type_filter, df_time_only)
        elif selected_page == "Line":
            # Pass df_filtered (for the new daily counts chart) and type_filter
            # Note: The Line Chart original code still uses full cleansed data
            render_line_chart_page(self.df_cleansed, df_filtered, type_filter)
        elif selected_page == "Predictor": # <--- NEW PAGE LOGIC
            render_prediction_page()


if __name__ == "__main__":
    app = TraffyApp()
    app.run()