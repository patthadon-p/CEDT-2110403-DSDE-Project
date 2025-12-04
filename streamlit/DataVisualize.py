# -----------------------------------------------------------------------------
# UNIFIED STREAMLIT APPLICATION: Bangkok Traffy Dashboard
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
rcParams["font.family"] = "Tahoma" # Set font family

# -----------------------------------------------------------------------------
# SETUP & CONFIGURATION
# -----------------------------------------------------------------------------

# Define a placeholder for the LineChartVisualizer class
# The real import is removed for self-containment, and we use the mock/local definition.
# We will define LineChartVisualizer directly in the global scope as the required class.

# Fallback/Utility functions (kept minimal for environment robustness)
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.append(project_root)
from src.utils import read_config_path

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
            "Line Chart": "Line"
        }
        selected_page = st.sidebar.radio(
            "Select View", 
            list(page_options.keys())
        )
        st.sidebar.markdown("---")
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
# 3. PAGE RENDERERS
# -----------------------------------------------------------------------------

# --- Page 1: Map Visualizer (Traffy Map Visualize) ---
def render_map_visualizer(df_cleansed: pd.DataFrame, pop_data: dict, type_filter: str, start_date: datetime.date, end_date: datetime.date):
    st.title("🗺️ Bangkok Traffy Spatial Analysis")
    st.markdown("---")
    
    # 1. Filter dataset and merge with population data
    # ... (Filtering and merging logic remains the same) ...
    df_filtered_raw = df_cleansed[
        (df_cleansed["date"] >= pd.Timestamp(start_date)) & 
        (df_cleansed["date"] <= pd.Timestamp(end_date))
    ].copy()
    
    # Apply type filter to the raw data (using the type_cleaned list/tuple)
    if type_filter != "ทั้งหมด":
        type_mask = df_filtered_raw["type_cleaned"].apply(lambda x: type_filter in x)
        df_filtered_raw = df_filtered_raw[type_mask].copy()

    # Merge with population data
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

    # 2. Compute Top 10 Tables 
    # ... (Top 10 logic remains the same) ...
    
    # Top 10 by Count
    top10_district = (
        dfwithpop.groupby("subdistrict")
        .size()
        .sort_values(ascending=False)
        .head(10)
        .reset_index(name="จำนวนปัญหา")
    )
    top10_district.columns = ["แขวง", "จำนวนปัญหา"] # Rename for display
    
    # Top 10 by Rate (Problems per Population)
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
    top10_perpop.columns = ["แขวง", "ความรุนแรง"] # Rename for display

    # 3. Add Key Metrics (KPIs)
    total_issues = len(dfwithpop)
    unique_districts = dfwithpop['district'].nunique()
    
    # 4. Layout: Key Metrics, Maps, and Top 10 Table
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

    # --- Section 2: Choropleth Maps and Top 10 Table (In 2 Columns) ---
    # **เริ่มการแบ่ง 2 คอลัมน์**
    col1, col2 = st.columns([3, 1])

    with col1:
        st.header(f"🌎 แผนที่วิเคราะห์ปัญหา{type_label}ตามพื้นที่")
        
        # --- Choropleth 1: Count ---
        st.subheader("จำนวนปัญหาต่อแขวง (Choropleth: Count)")
        choroplethmap = plot_choroplethmap(df=dfwithpop, region_path=region_path, type_filter=type_filter)
        st_folium(choroplethmap, width='100%', height=400)
        
        st.markdown("---") 
        
        # --- Choropleth 2: Per Population ---
        st.subheader("ความรุนแรงของปัญหาต่อแขวง (Choropleth: Per Population)")
        choroplethmapperpop = plot_choroplethmap_perpop(df=dfwithpop, region_path=region_path, type_filter=type_filter)
        st_folium(choroplethmapperpop, width='100%', height=400)
        # ไม่ต้องใส่ st.markdown("---") ตรงนี้แล้ว

    # --- Section 3: Top 10 Tables (Right Column) ---
    with col2:
        st.header("🏆 10 อันดับพื้นที่วิกฤต")
        
        # Table 1: Top 10 by Count
        st.subheader(f"1. แขวงที่มีจำนวนปัญหา{type_label}มากที่สุด")
        st.dataframe(
            top10_district.style.format({
                "จำนวนปัญหา": "{:,.0f}"
            }), 
            use_container_width=True
        )
        
        # Table 2: Top 10 by Rate
        st.subheader(f"2. แขวงที่มีความรุนแรงของปัญหา{type_label}สูงที่สุด")
        st.dataframe(
            top10_perpop.style.format({
                "ความรุนแรง": "{:,.2f}"
            }), 
            use_container_width=True
        )

    # **คอลัมน์คู่ col1, col2 สิ้นสุดที่นี่**
    st.markdown("---") 
    
    # --- Section 4: Heatmap (NEW) ---
    type_label = type_filter if type_filter != "ทั้งหมด" else ""
    st.header(f"🔥 แผนที่ความหนาแน่นของปัญหา{type_label} (Heatmap)")
    heatmap = plot_heatmap(dfwithpop) 
    st.pydeck_chart(heatmap, use_container_width=True, height=500)
    st.markdown("---")
    
    # --- Section 5: Scatter Map (Full Width) ---
    st.header(f"📍 แผนที่แสดงจุดที่เกิดปัญหา{type_label} (Scatter Map)")
    scatter_map = plot_scatter_map(dfwithpop) 
    st.pydeck_chart(scatter_map, use_container_width=True, height=500)
    
# --- Page 2: Data Analysis (Datascatter) ---
def render_analysis_page(df_filtered: pd.DataFrame, df_score: pd.DataFrame, type_filter: str, df_time_only: pd.DataFrame):
    st.title("📊 Bangkok Traffy Data Analysis")
    visualizer = TraffyVisualizer()

    # REMOVED: Timeline (plot_daily_counts) is now in render_line_chart_page
    # st.markdown("---") # Keep for spacing if necessary, but removed for clean-up

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
    # Using Tabs hides the large/complex charts so they don't clutter the screen
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
    
    # 1. Daily Counts (Timeline) - MOVED FROM ANALYSIS PAGE
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
        # This will catch errors from the external class if the column is still missing
        # or if the plot fails for other reasons.
        st.error(f"Error rendering Line Chart: {e}. Please check the `LineChartVisualizer` definition.")
        st.info("Debugging note: The DataFrame passed has columns: " + ", ".join(df_cleansed.columns))

# -----------------------------------------------------------------------------
# 4. PLOTTING FUNCTIONS (Copied from original for functionality)
# -----------------------------------------------------------------------------

# --- Plotting Helpers for Map Visualizer ---
# Note: These functions require geopandas and shapely to run.

def plot_choroplethmap(df: pd.DataFrame, region_path: str, type_filter: str | None = None, value_column: str = "count"):
    df_points = df.copy()
    if type_filter and type_filter != "ทั้งหมด":
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
    agg_df = joined.groupby("subdistrict_name").size().reset_index(name="count")

    # 3. Merge and fill
    gdf_merged = gdf_region.merge(agg_df, on="subdistrict_name", how="left")
    gdf_merged["count"] = gdf_merged["count"].fillna(0)

    # 4. Compute map center
    gdf_proj = gdf_merged.to_crs(epsg=3857)
    union_geom = gdf_proj.geometry.unary_union
    center_proj = union_geom.centroid
    center_latlon = gpd.GeoSeries([center_proj], crs=gdf_proj.crs).to_crs(epsg=4326).geometry[0]
    minx, miny, maxx, maxy = gdf_merged.total_bounds
    bounds = [[miny, minx], [maxy, maxx]]

    # 5. Folium choropleth map
    m = gdf_merged.explore(
        column="count", cmap="Oranges", legend=True, 
        location=[center_latlon.y, center_latlon.x], zoom_start=10,
        tooltip=["district_name", "subdistrict_name", "count"],
        min_zoom=10, max_zoom=16, map_kwds={"bounds": bounds}
    )
    m.options.update({"zoomControl": True, "scrollWheelZoom": True, "dragging": True})
    return m

def plot_choroplethmap_perpop(df: pd.DataFrame, region_path: str, type_filter: str | None = None, value_column: str = "count"):
    df_region = pd.read_csv(region_path)
    df_region["geometry"] = df_region["geometry"].map(wkt.loads)
    gdf_region = gpd.GeoDataFrame(df_region, geometry="geometry", crs="EPSG:4326")
    region_geom = gdf_region[["subdistrict_name", "geometry"]].copy()

    df_points = df.copy()
    if type_filter and type_filter != "ทั้งหมด":
        df_points = df_points[df_points["type_cleaned"].apply(lambda x: type_filter in x)]

    # Aggregate counts and mean population (using 'subdistrict-name' from pop data)
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

    # Compute map center
    gdf_proj = gdf_merged.to_crs(epsg=3857)
    union_geom = gdf_proj.geometry.unary_union
    center_latlon = gpd.GeoSeries([union_geom.centroid], crs=gdf_proj.crs).to_crs(epsg=4326).geometry[0]
    minx, miny, maxx, maxy = gdf_merged.total_bounds
    bounds = [[miny, minx], [maxy, maxx]]

    # Folium choropleth map
    m = gdf_merged.explore(
        column="probperpop", cmap="Oranges", legend=True, scheme="natural_breaks",
        location=[center_latlon.y, center_latlon.x], zoom_start=10,
        tooltip=["subdistrict_name", "probperpop"],
        min_zoom=10, max_zoom=16, map_kwds={"bounds": bounds}
    )
    m.options.update({"zoomControl": True, "scrollWheelZoom": True, "dragging": True})
    return m

# Insert this function into the '4. PLOTTING FUNCTIONS' section

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

    cols_to_select = [lon_col, lat_col, "subdistrict", "district", "day", "month", "year", "comment", "color_rgb", 'type_cleaned']
    df_small = df_plot[[col for col in cols_to_select if col in df_plot.columns]]


    # --- 2. Pydeck Layer Configuration ---
    # Heatmap visualization uses the location data and weights. 
    # Since we are counting complaints, we don't need a weight column 
    # (Pydeck implicitly weights each point as 1).
    
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

def plot_scatter_map(
    df: pd.DataFrame,
    max_points: int = 100_000,
    lon_col: str = "longitude",
    lat_col: str = "latitude",
    type_col: str = "type_clean", # CHANGED: Use 'type_clean' for single-type coloring
):
    # --- 1. Sampling and Data Preparation ---
    if len(df) > max_points:
        st.warning(f"Dataset too large ({len(df):,} rows). Showing a sample of {max_points:,} points.")
        df_plot = df.sample(max_points).copy()
    else:
        df_plot = df.copy()

    # --- 2. Color Mapping Setup ---
    # Define a simple color mapping for example types. 
    # NOTE: You should expand this to cover all types in your data.
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
        # The 'type_clean' column might have None/NaN, use 'Other' if so
        if pd.isna(type_value):
            return COLOR_MAP["Other"]
        # Use .get() with fallback to handle types not explicitly in COLOR_MAP
        return COLOR_MAP.get(str(type_value).strip(), COLOR_MAP["Other"])

    # **FIX:** Apply the color function to the single-type column ('type_clean'), 
    # not the tuple column ('type_cleaned').
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
# 5. MAIN APP CONTROLLER
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


if __name__ == "__main__":
    app = TraffyApp()
    app.run()