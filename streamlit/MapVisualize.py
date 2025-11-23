# -------------------------------------------------------
# Bangkok Traffy Map Visualize
# -------------------------------------------------------

# Import necessary libraries
import datetime
import os
import sys

import pandas as pd
import streamlit as st
import pydeck as pdk
from streamlit_folium import st_folium
import geopandas as gpd
from shapely import wkt

# -------------------------------------------------------
# Setup project root
# -------------------------------------------------------
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.append(project_root)

from src.visualize.MapVisualizer import MapVisualizer
from src.utils import read_config_path

# -------------------------------------------------------
# Streamlit page configuration
# -------------------------------------------------------
st.set_page_config(layout="wide")
st.title("Bangkok Traffy Map Visualize")
st.sidebar.header("Filters")

st.markdown("""
    <style>
    section[data-testid="stSidebar"] .css-1d391kg {
        padding-bottom: 200px !important;
    }
    </style>
""", unsafe_allow_html=True)

# -------------------------------------------------------
# Load and preprocess data
# -------------------------------------------------------
@st.cache_data
def load_data() -> pd.DataFrame:
    df = pd.read_csv(read_config_path(domain="processed", key="cleansed_data_path"))
    
    # Clean and split types
    df["type_cleaned"] = (
        df["type"]
        .astype(str)
        .str.replace("{", "")
        .str.replace("}", "")
        .str.split(",")
        .apply(tuple)
    )

    # Build datetime column
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

df_cleansed = load_data()

# -------------------------------------------------------
# Type list for sidebar filter
# -------------------------------------------------------
@st.cache_data
def get_type_list(df: pd.DataFrame) -> list[str]:
    return ["ทั้งหมด"] + sorted({t.strip() for row in df["type_cleaned"] for t in row})

type_list = get_type_list(df_cleansed)

# -------------------------------------------------------
# Sidebar filters
# -------------------------------------------------------
with st.sidebar.form("filter_form"):
    type_filter = st.selectbox("เลือกประเภทปัญหา", type_list)
    
    date_range = st.date_input(
        "เลือกช่วงวัน",
        value=[datetime.date(2021, 9, 19), datetime.date(2025, 1, 16)],
        min_value=datetime.date(2021, 9, 19),
        max_value=datetime.date(2025, 1, 16),
    )

    # Normalize date range
    if len(date_range) == 2:
        start_date, end_date = date_range
    else:
        start_date = end_date = date_range[0]

    submit = st.form_submit_button("Apply Filter")

# Store filter values in session
if submit:
    st.session_state["type_filter"] = type_filter
    st.session_state["start_date"] = start_date
    st.session_state["end_date"] = end_date

type_filter = st.session_state.get("type_filter", "ทั้งหมด")
start_date = st.session_state.get("start_date", datetime.date(2021, 9, 19))
end_date = st.session_state.get("end_date", datetime.date(2025, 1, 16))

# -------------------------------------------------------
# Filter dataset
# -------------------------------------------------------
type_mask = pd.Series([True] * len(df_cleansed)) if type_filter == "ทั้งหมด" else df_cleansed["type_cleaned"].apply(lambda x: type_filter in x)
date_mask = (df_cleansed["date"] >= pd.Timestamp(start_date)) & (df_cleansed["date"] <= pd.Timestamp(end_date))
filtered_df = df_cleansed[type_mask & date_mask].copy()

# -------------------------------------------------------
# Compute top 10 districts
# -------------------------------------------------------
top10_district = (
    filtered_df.groupby("subdistrict")
    .size()
    .sort_values(ascending=False)
    .head(10)
    .reset_index(name="จำนวนปัญหา")
)

# -------------------------------------------------------
# Heat Map Visualizer
# -------------------------------------------------------
def plot_heatmap(
    df: pd.DataFrame,
    region_path: str,
    latitude_column: str = "latitude",
    longitude_column: str = "longitude",
    type_filter: str | None = None,
    value_column: str = "count",
):
    """
    Plot choropleth heatmap of points aggregated by subdistrict.
    """
    # Filter by type if needed
    df_points = df.copy()
    if type_filter and type_filter != "ทั้งหมด":
        df_points = df_points[df_points["type_cleaned"].apply(lambda x: type_filter in x)]

    # Create GeoDataFrame for points
    gdf_points = gpd.GeoDataFrame(
        df_points,
        geometry=gpd.points_from_xy(df_points[longitude_column], df_points[latitude_column]),
        crs="EPSG:4326",
    )

    # Load region shapefile / CSV with WKT geometry
    df_region = pd.read_csv(region_path)
    df_region["geometry"] = df_region["geometry"].map(wkt.loads)
    gdf_region = gpd.GeoDataFrame(df_region, geometry="geometry", crs="EPSG:4326")

    # Spatial join to assign points to subdistrict
    joined = gpd.sjoin(gdf_points, gdf_region, how="left", predicate="within")

    # Aggregate counts (or mean of value_column)
    if value_column == "count":
        agg_df = joined.groupby("subdistrict_name").size().reset_index(name="count")
    else:
        agg_df = joined.groupby("subdistrict_name")[value_column].mean().reset_index(name="count")

    # Merge back to region GeoDataFrame
    gdf_merged = gdf_region.merge(agg_df, on="subdistrict_name", how="left")
    gdf_merged["count"] = gdf_merged["count"].fillna(0)

    # Compute map center
    gdf_proj = gdf_merged.to_crs(epsg=3857)
    union_geom = gdf_proj.geometry.unary_union
    center_proj = union_geom.centroid
    center_latlon = gpd.GeoSeries([center_proj], crs=gdf_proj.crs).to_crs(epsg=4326).geometry[0]

    # Map bounds
    minx, miny, maxx, maxy = gdf_merged.total_bounds
    bounds = [[miny, minx], [maxy, maxx]]

    # Folium choropleth map
    m = gdf_merged.explore(
        column="count",
        cmap="Oranges",
        legend=True,
        location=[center_latlon.y, center_latlon.x],
        zoom_start=10,
        tooltip=["district_name", "subdistrict_name", "count"],
        min_zoom=10,
        max_zoom=16,
        max_bounds=False,
        map_kwds={"bounds": bounds},
    )

    # Enable map interactions
    m.options.update({
        "zoomControl": True,
        "scrollWheelZoom": True,
        "doubleClickZoom": True,
        "touchZoom": True,
        "dragging": True,
    })

    return m

# -------------------------------------------------------
# Scatter Map Visualizer
# -------------------------------------------------------
def plot_scatter_map(
    df: pd.DataFrame,
    max_points: int = 100_000,
    lon_col: str = "longitude",
    lat_col: str = "latitude",
):
    """
    Create a PyDeck scatterplot map for Traffy locations.
    Automatically samples if dataset is too large.
    """
    # Reduce dataset size if needed
    if len(df) > max_points:
        st.warning(
            f"Dataset too large ({len(df):,} rows). "
            f"Showing a sample of {max_points:,} points for performance."
        )
        df_plot = df.sample(max_points)
    else:
        df_plot = df.copy()

    # Select columns used in the plot
    df_small = df_plot[[lon_col, lat_col, "subdistrict", "district", "day", "month", "year", "comment"]]

    # Create scatter layer
    scatter_layer = pdk.Layer(
        "ScatterplotLayer",
        df_small,
        get_position=[lon_col, lat_col],
        get_radius=100,
        get_fill_color=[255, 0, 0],   # red
        pickable=True,
        opacity=0.5,
    )

    # View state (center of the points)
    view_state = pdk.ViewState(
        latitude=df_plot[lat_col].mean(),
        longitude=df_plot[lon_col].mean(),
        zoom=9.5,
        pitch=0,
    )

    # Build deck
    deck = pdk.Deck(
        layers=[scatter_layer],
        initial_view_state=view_state,
        tooltip={
            "text": "{subdistrict} {district}\n{day}/{month}/{year}\n{comment}"
        },
    )

    return deck


# -------------------------------------------------------
# Layout: Maps and Top 10 Table
# -------------------------------------------------------
if type_filter=="ทั้งหมด": type_filter=""
col1, col2 = st.columns([3, 1])

# --- Column 1: Maps ---
with col1:
    st.subheader(f"Heatmap แสดงจำนวนปัญหา{type_filter}ในแต่ละแขวง")
    region_path=read_config_path(
        domain="processed", key="cleansed_geographic_data_path"
    )
    heatmap = plot_heatmap(
        df=filtered_df,
        region_path=region_path,
        type_filter=type_filter,
    )
    st_folium(heatmap, width=800, height=400)


    st.subheader(f"Scatter Map แสดงตำแหน่งต่างๆที่เกิดปัญหา{type_filter}")
    scatter_map = plot_scatter_map(filtered_df)
    st.pydeck_chart(scatter_map, width=800, height=400)


# --- Column 2: Top 10 Districts ---
with col2:
    st.subheader(f"10 อันดับแขวงที่มีปัญหา{type_filter}มากที่สุด")
    st.dataframe(top10_district, width='stretch')
