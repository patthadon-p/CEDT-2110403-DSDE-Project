# src/visualizer.py

import json

import altair as alt
import geopandas as gpd
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import pydeck as pdk
import streamlit as st

# Import utilities and constants
from components.utils import _HAS_SKLEARN
from plotly.subplots import make_subplots
from shapely import wkt

# If DBSCAN is not available, we use the mock defined in utils
if not _HAS_SKLEARN:
    from components.utils import plot_dbscan_map  # Import the mock function
else:
    # If available, import necessary DBSCAN dependencies for the real function
    import matplotlib.pyplot as plt  # Required for colormap
    from sklearn.cluster import DBSCAN
    from sklearn.preprocessing import StandardScaler

    # Define the real function (as in the original file)
    def plot_dbscan_map(
        df: pd.DataFrame,
        eps: float,
        min_samples: int,
        top_n: int = 5,
        lon_col: str = "longitude",
        lat_col: str = "latitude",
        max_points: int = 100_000,
    ):
        """
        Performs DBSCAN clustering on spatial data using user-defined parameters
        and visualizes all non-noise clusters using a dynamic continuous colormap.
        """
        if df.empty or len(df) < min_samples:
            st.info("Insufficient data for clustering with current filters/parameters.")
            return pdk.Deck(
                initial_view_state=pdk.ViewState(
                    latitude=13.75, longitude=100.51, zoom=9.5
                )
            )

        # --- 1. Data Preparation and Scaling (Same as original) ---
        if len(df) > max_points:
            df_plot = df.sample(max_points, random_state=42).copy()
            st.warning(
                f"Dataset too large ({len(df):,} rows). Showing a sample of {max_points:,} points."
            )
        else:
            df_plot = df.copy()

        cols_to_keep = [
            lon_col,
            lat_col,
            "subdistrict",
            "district",
            "type_cleaned",
            "type_clean",
        ]
        optional_cols = ["day", "month", "year", "comment"]
        for col in optional_cols:
            if col in df_plot.columns and col not in cols_to_keep:
                cols_to_keep.append(col)

        df_plot = df_plot[
            [col for col in cols_to_keep if col in df_plot.columns]
        ].copy()

        # Prepare coordinates for clustering
        coords = df_plot[[lat_col, lon_col]]
        scaler = StandardScaler()
        coords_scaled = scaler.fit_transform(coords)

        # --- 2. DBSCAN Clustering (Your Logic) ---
        db = DBSCAN(eps=eps, min_samples=min_samples).fit(coords_scaled)
        df_plot["cluster"] = db.labels_

        # Filter out noise points, as requested
        df_clustered = df_plot[df_plot["cluster"] != -1].copy()

        if df_clustered.empty:
            st.info(
                "DBSCAN found no clusters (all points classified as noise) with current parameters."
            )
            return pdk.Deck(
                initial_view_state=pdk.ViewState(
                    latitude=13.75, longitude=100.51, zoom=9.5
                )
            )

        # --- 3. Dynamic Coloring (Your Logic) ---
        unique_clusters = sorted(df_clustered["cluster"].unique())
        num_clusters = len(unique_clusters)

        colormap = plt.get_cmap("hsv")
        cluster_colors = {
            cluster: [int(x * 255) for x in colormap(i / num_clusters)[:3]]
            + [255]  # Added Alpha=255
            for i, cluster in enumerate(unique_clusters)
        }

        df_clustered["color"] = df_clustered["cluster"].map(cluster_colors)

        # --- 4. Pydeck Layer Configuration (Your Logic) ---
        scatter_layer = pdk.Layer(
            "ScatterplotLayer",
            df_clustered,
            get_position="[longitude, latitude]",
            get_color="color",
            get_radius=50,
            opacity=0.8,
            pickable=True,
        )

        # --- 5. View State and Deck ---
        view_state = pdk.ViewState(
            latitude=df_clustered["latitude"].mean(),
            longitude=df_clustered["longitude"].mean(),
            zoom=10,
            pitch=0,
        )

        deck = pdk.Deck(
            layers=[scatter_layer],
            initial_view_state=view_state,
            map_style="dark",
            tooltip={
                "html": "<b>Cluster:</b> {cluster}<br/><b>Location:</b> {subdistrict} {district}<br/><b>Date:</b> {day}/{month}/{year}<br/><b>Type:</b> {type_clean}",
                "style": {"color": "white"},
            },
        )
        return deck


# --- LINECHARTVISUALIZER CLASS (Updated with Custom Hover Data) ---
class LineChartVisualizer:
    def __init__(self, df):
        self.df = df.copy()

        # 1. Expand data to handle multiple types per ticket
        self.df = self.df.explode("type_cleaned")
        self.df["type_cleaned"] = self.df["type_cleaned"].str.strip()

        # Ensure required columns are available (using the renamed 'year'/'month' columns)
        if (
            "timestamp_year" not in self.df.columns
            or "timestamp_month" not in self.df.columns
        ):
            # Fallback check for new column names if the main app logic failed to rename back
            if "year" in self.df.columns:
                self.df.rename(
                    columns={"year": "timestamp_year", "month": "timestamp_month"},
                    inplace=True,
                )
            else:
                raise ValueError(
                    "DataFrame must have 'timestamp_year' and 'timestamp_month' columns for monthly grouping."
                )

        # 2. Create date column for sorting and grouping
        # NOTE: Using the original names expected by the class logic
        self.df["date_ts"] = pd.to_datetime(
            self.df[["timestamp_year", "timestamp_month"]]
            .rename(columns={"timestamp_year": "year", "timestamp_month": "month"})
            .assign(day=1)
        )

        # Filter out empty types
        self.df = self.df[self.df["type_cleaned"] != ""]

    def plot(self, figsize: tuple = (12, 6)) -> go.Figure:

        # 3. Group by Year-Month and Type
        monthly_counts = (
            self.df.groupby([self.df["date_ts"].dt.to_period("M"), "type_cleaned"])
            .size()
            .reset_index(name="Count")
        )
        # Convert Period back to Timestamp for Plotly plotting
        monthly_counts["Date"] = monthly_counts["date_ts"].dt.to_timestamp()

        if monthly_counts.empty:
            fig = go.Figure()
            fig.update_layout(title="No data available for plotting.")
            return fig

        # 4. Create Plotly Line Chart (multi-series plot)
        fig = px.line(
            monthly_counts,
            x="Date",
            y="Count",
            color="type_cleaned",
            title="Monthly Problem Counts by Type (All Types)",
            labels={"Count": "Number of Problems", "type_cleaned": "Problem Type"},
            height=600,
            # Specify the columns to appear in the hover box
            hover_data={"type_cleaned": True},
        )

        # 5. Customize Layout
        fig.update_traces(mode="lines", line=dict(width=2))
        fig.update_layout(
            legend_title_text="Problem Type",
            xaxis_title=None,
            hovermode="x",  # Use 'x' to show combined tooltips for all series at a single date
            margin=dict(l=20, r=20, t=50, b=20),
        )

        return fig


# Pydeck Choropleth (Count)
def plot_choroplethmap(
    df: pd.DataFrame,
    region_path: str,
    type_filter: str | None = None,
    value_column: str = "count",
):
    df_points = df.copy()
    if type_filter and type_filter != "ทั้งหมด":
        # Need to use the full 'type_cleaned' tuple column to filter
        df_points = df_points[
            df_points["type_cleaned"].apply(lambda x: type_filter in x)
        ]

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

    # --- Pydeck Specific Steps ---

    # 4. Compute map center
    center_latlon = gdf_merged.to_crs(epsg=3857).geometry.unary_union.centroid
    center_latlon = (
        gpd.GeoSeries([center_latlon], crs="EPSG:3857").to_crs(epsg=4326).geometry[0]
    )

    # Convert GeoDataFrame to GeoJSON
    geojson_data = json.loads(gdf_merged.to_json())

    # 5. Define the Pydeck Layer
    max_count = gdf_merged["count"].max()
    if max_count == 0:
        max_count = 1

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
        pickable=True,
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
        map_style="light",
        tooltip={
            "html": "<b>Subdistrict:</b> {subdistrict_name}<br/><b>District:</b> {district_name}<br/><b>Count:</b> {count}",
            "style": {"color": "white"},
        },
    )

    return r


# Pydeck Choropleth (Per Population)
def plot_choroplethmap_perpop(
    df: pd.DataFrame,
    region_path: str,
    type_filter: str | None = None,
    value_column: str = "probperpop",
):
    df_region = pd.read_csv(region_path)
    df_region["geometry"] = df_region["geometry"].map(wkt.loads)
    gdf_region = gpd.GeoDataFrame(df_region, geometry="geometry", crs="EPSG:4326")
    region_geom = gdf_region[["subdistrict_name", "geometry"]].copy()

    df_points = df.copy()
    if type_filter and type_filter != "ทั้งหมด":
        df_points = df_points[
            df_points["type_cleaned"].apply(lambda x: type_filter in x)
        ]

    # Aggregate counts and mean population (using 'subdistrict-name' from pop data)
    agg_df = (
        df_points.groupby("subdistrict-name")
        .agg(count=("subdistrict-name", "size"), total=("total", "mean"))
        .reset_index()
    )
    agg_df.rename(columns={"subdistrict-name": "subdistrict_name"}, inplace=True)
    agg_df["probperpop"] = agg_df["count"] / agg_df["total"].fillna(1)

    # Merge aggregated data back to region GeoDataFrame
    gdf_merged = region_geom.merge(agg_df, on="subdistrict_name", how="left")
    gdf_merged["probperpop"] = gdf_merged["probperpop"].fillna(0)
    gdf_merged["count"] = gdf_merged["count"].fillna(0)

    # --- Pydeck Specific Steps ---

    # 1. Compute map center
    center_latlon = gdf_merged.to_crs(epsg=3857).geometry.unary_union.centroid
    center_latlon = (
        gpd.GeoSeries([center_latlon], crs="EPSG:3857").to_crs(epsg=4326).geometry[0]
    )

    # Convert GeoDataFrame to GeoJSON
    geojson_data = json.loads(gdf_merged.to_json())

    # 2. Define the Pydeck Layer
    max_probperpop = gdf_merged["probperpop"].max()

    if max_probperpop == 0:
        max_probperpop = 1

    color_expression = (
        f"[255, 140, 0, (properties.probperpop / {max_probperpop}) * 255]"
    )

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
        pickable=True,
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
        map_style="light",
        tooltip={
            "html": "<b>Subdistrict:</b> {subdistrict_name}<br/><b>Incidents per Pop:</b> {probperpop}",
            "style": {"color": "white"},
        },
    )

    return r


# Pydeck Heatmap
def plot_heatmap(
    df: pd.DataFrame,
    lon_col: str = "longitude",
    lat_col: str = "latitude",
    max_points: int = 100_000,
):
    """Creates a Pydeck HeatmapLayer visualization."""

    # --- 1. Sampling and Data Preparation ---
    if len(df) > max_points:
        st.warning(
            f"Dataset too large ({len(df):,} rows). Showing a sample of {max_points:,} points."
        )
        df_plot = df.sample(max_points).copy()
    else:
        df_plot = df.copy()

    # Ensure coordinates are numeric
    df_plot = df_plot.dropna(subset=[lat_col, lon_col])

    cols_to_select = [
        lon_col,
        lat_col,
        "subdistrict",
        "district",
        "day",
        "month",
        "year",
        "comment",
        "type_cleaned",
    ]
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


# Pydeck Scatter Map
def plot_scatter_map(
    df: pd.DataFrame,
    max_points: int = 100_000,
    lon_col: str = "longitude",
    lat_col: str = "latitude",
    type_col: str = "type_clean",
):
    # --- 1. Sampling and Data Preparation ---
    if len(df) > max_points:
        st.warning(
            f"Dataset too large ({len(df):,} rows). Showing a sample of {max_points:,} points."
        )
        df_plot = df.sample(max_points).copy()
    else:
        df_plot = df.copy()

    # --- 2. Color Mapping Setup ---
    COLOR_MAP = {
        # โครงสร้างพื้นฐาน/ถนน - ส้มเข้ม
        "ถนน": [255, 140, 0],
        "ทางเท้า": [255, 140, 0],
        "สะพาน": [255, 140, 0],
        "กีดขวาง": [255, 140, 0],
        "ป้าย": [255, 140, 0],
        "ป้ายจราจร": [255, 140, 0],
        # สิ่งแวดล้อม/สุขภาวะ - เขียวเข้ม
        "ความสะอาด": [34, 139, 34],
        "ห้องน้ำ": [34, 139, 34],
        "คลอง": [34, 139, 34],
        "PM2.5": [34, 139, 34],
        "เสียงรบกวน": [34, 139, 34],
        # น้ำ/สาธารณูปโภค - ฟ้าอ่อน
        "น้ำท่วม": [0, 191, 255],
        "ท่อระบายน้ำ": [0, 191, 255],
        "สายไฟ": [0, 191, 255],
        "แสงสว่าง": [0, 191, 255],
        # สังคม/ความปลอดภัย - แดง
        "ความปลอดภัย": [255, 0, 0],
        "สัตว์จรจัด": [255, 0, 0],
        "คนจรจัด": [255, 0, 0],
        # การบริการ/อื่นๆ - ชมพูเข้ม
        "การเดินทาง": [255, 20, 147],
        "ต้นไม้": [255, 20, 147],
        # การสื่อสาร - น้ำเงินอมเทา
        "ร้องเรียน": [70, 130, 180],
        "สอบถาม": [70, 130, 180],
        "เสนอแนะ": [70, 130, 180],
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
    cols_to_select = [
        lon_col,
        lat_col,
        "subdistrict",
        "district",
        "day",
        "month",
        "year",
        "comment",
        "color_rgb",
        type_col,
    ]
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
            "style": {"color": "white"},
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
            daily_counts,
            x="date",
            y="count",
            color="year_month",
            labels={"date": "Date", "count": "Issues", "year_month": "Month"},
            hover_data=["date", "count"],
        )
        fig.add_trace(px.line(daily_counts, x="date", y="count").data[0])
        fig.update_traces(marker=dict(size=6, opacity=0.8))
        fig.update_layout(
            height=380,
            margin=dict(l=20, r=20, t=30, b=20),
            legend_title_text=None,
            hovermode="x unified",
        )
        st.plotly_chart(fig, use_container_width=True)

    @staticmethod
    def plot_score_vs_complaints(df_filtered: pd.DataFrame, df_score: pd.DataFrame):
        if "district" not in df_filtered.columns or df_score.empty:
            return

        complaints = (
            df_filtered.groupby("district").size().reset_index(name="complaints")
        )
        merged = df_score.merge(complaints, on="district", how="left")
        merged["complaints"] = merged["complaints"].fillna(0)

        if merged["complaints"].sum() == 0:
            st.info("No complaints found.")
            return

        low_score_th = merged["total_score"].quantile(0.3)
        high_complaints_th = merged["complaints"].quantile(0.7)

        def get_zone(row):
            if (
                row["total_score"] < low_score_th
                and row["complaints"] > high_complaints_th
            ):
                return "Danger"
            elif (
                row["total_score"] >= low_score_th
                and row["complaints"] > high_complaints_th
            ):
                return "Active"
            elif (
                row["total_score"] < low_score_th
                and row["complaints"] <= high_complaints_th
            ):
                return "Silent Risk"
            else:
                return "Good"

        merged["zone"] = merged.apply(get_zone, axis=1)
        zone_order = ["Danger", "Active", "Silent Risk", "Good"]
        color_map = {
            "Danger": "red",
            "Active": "#ff7f0e",
            "Silent Risk": "#2ca02c",
            "Good": "#1f77b4",
        }

        fig = px.scatter(
            merged,
            x="total_score",
            y="complaints",
            color="zone",
            category_orders={"zone": zone_order},
            color_discrete_map=color_map,
            hover_data=["district", "total_score", "complaints"],
            title="Total Score vs Complaints",
        )

        fig.update_traces(marker=dict(size=12, opacity=0.8))
        fig.add_vline(
            x=float(low_score_th), line_dash="dash", line_color="gray", opacity=0.5
        )
        fig.add_hline(
            y=float(high_complaints_th),
            line_dash="dash",
            line_color="gray",
            opacity=0.5,
        )

        fig.update_layout(
            height=510,
            margin=dict(l=20, r=20, t=60, b=20),
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1,
                title=None,
            ),
        )
        st.plotly_chart(fig, use_container_width=True)

    @staticmethod
    def plot_quality_dimensions(df_filtered: pd.DataFrame, df_score: pd.DataFrame):
        if "district" not in df_filtered.columns or df_score.empty:
            return

        complaints = (
            df_filtered.groupby("district").size().reset_index(name="complaints")
        )
        merged = df_score.merge(complaints, on="district", how="left")
        merged["complaints"] = merged["complaints"].fillna(0)

        metrics = ["public_service", "economy", "welfare", "environment"]
        titles = {m: m.replace("_", " ").title() for m in metrics}

        fig = make_subplots(rows=2, cols=2, subplot_titles=[titles[m] for m in metrics])

        for i, m in enumerate(metrics):
            row, col = i // 2 + 1, i % 2 + 1
            fig.add_trace(
                go.Scatter(
                    x=merged[m],
                    y=merged["complaints"],
                    mode="markers",
                    marker=dict(
                        size=10,
                        opacity=1,
                        color=merged["complaints"],
                        colorscale="RdYlBu",
                        reversescale=True,
                        showscale=False,
                    ),
                    text=merged["district"],
                    hovertemplate=f"<b>%{{text}}</b><br>{titles[m]}: %{{x}}<br>Complaints: %{{y}}<extra></extra>",
                ),
                row=row,
                col=col,
            )
            fig.update_xaxes(title_text=None, row=row, col=col, showgrid=True)
            fig.update_yaxes(showgrid=True, row=row, col=col)

        fig.update_yaxes(matches="y")
        fig.update_layout(
            height=500,
            showlegend=False,
            title_text="Dimensions vs Complaints",
            margin=dict(l=40, r=20, t=60, b=40),
        )
        st.plotly_chart(fig, use_container_width=True)

    @staticmethod
    def plot_heatmap_metric_vs_type(df_base: pd.DataFrame, df_score: pd.DataFrame):
        df = df_base.dropna(subset=["type_clean"]).copy()
        df = df[df["type_clean"].astype(str).str.strip() != ""]
        if df.empty or df_score.empty:
            return

        pivot_types = (
            df.groupby(["district", "type_clean"])
            .size()
            .reset_index(name="complaints")
            .pivot(index="district", columns="type_clean", values="complaints")
            .fillna(0)
            .reset_index()
        )
        corr_df = df_score.merge(pivot_types, on="district", how="left").fillna(0)

        metric_cols = [
            "total_score",
            "public_service",
            "economy",
            "welfare",
            "environment",
        ]
        type_cols = [c for c in corr_df.columns if c not in metric_cols + ["district"]]
        if not type_cols:
            return

        corr_matrix = corr_df[metric_cols + type_cols].corr(method="pearson")
        corr_sub = (
            corr_matrix.loc[metric_cols, type_cols]
            .reset_index()
            .melt(id_vars="index", var_name="problem_type", value_name="corr")
            .rename(columns={"index": "metric"})
        )

        heatmap = (
            alt.Chart(corr_sub)
            .mark_rect()
            .encode(
                x=alt.X("problem_type:N", title=None, sort=type_cols),
                y=alt.Y("metric:N", title=None, sort=metric_cols),
                color=alt.Color(
                    "corr:Q", scale=alt.Scale(scheme="redblue", domain=[-1, 0, 1])
                ),
                tooltip=["metric", "problem_type", alt.Tooltip("corr", format=".2f")],
            )
            .properties(height=350, title="Correlation: Metric x Type")
        )
        st.altair_chart(heatmap, use_container_width=True)

    @staticmethod
    def plot_heatmap_type_vs_type(df_base: pd.DataFrame):
        triangle_mode = st.radio(
            "Mode:",
            ["Full", "Upper", "Lower"],
            index=2,
            horizontal=True,
            key="heat_mode",
        )

        df = df_base.dropna(subset=["type_clean"]).copy()
        df = df[df["type_clean"].astype(str).str.strip() != ""]
        if df.empty:
            return

        pivot_problems = (
            df.groupby(["district", "type_clean"])
            .size()
            .reset_index(name="complaints")
            .pivot(index="district", columns="type_clean", values="complaints")
            .fillna(0)
        )
        if pivot_problems.shape[1] < 2:
            st.info("Not enough problem types selected for correlation.")
            return

        corr_matrix = pivot_problems.corr(method="pearson")
        corr_long = (
            corr_matrix.reset_index()
            .melt(id_vars="type_clean", var_name="problem_type_2", value_name="corr")
            .rename(columns={"type_clean": "problem_type_1"})
        )

        problem_list = list(corr_matrix.index)
        idx_map = {p: i for i, p in enumerate(problem_list)}
        corr_long["i"] = corr_long["problem_type_1"].map(idx_map)
        corr_long["j"] = corr_long["problem_type_2"].map(idx_map)

        if triangle_mode == "Upper":
            corr_long = corr_long[corr_long["i"] < corr_long["j"]]
        elif triangle_mode == "Lower":
            corr_long = corr_long[corr_long["i"] > corr_long["j"]]

        cell_size = 25 if len(problem_list) > 15 else 35

        heatmap = (
            alt.Chart(corr_long)
            .mark_rect()
            .encode(
                x=alt.X("problem_type_2:N", title=None),
                y=alt.Y("problem_type_1:N", title=None),
                color=alt.Color(
                    "corr:Q", scale=alt.Scale(scheme="redblue", domain=[-1, 0, 1])
                ),
                tooltip=[
                    "problem_type_1",
                    "problem_type_2",
                    alt.Tooltip("corr", format=".2f"),
                ],
            )
            .properties(
                width=cell_size * (len(problem_list) * 1.5),
                height=cell_size * (len(problem_list) * 1.5),
                title="Correlation: Type x Type",
            )
        )
        st.altair_chart(heatmap, use_container_width=False)

    @staticmethod
    def plot_scatter_matrix(df_time_filtered: pd.DataFrame):
        df = df_time_filtered.dropna(subset=["type_clean"]).copy()
        df = df[df["type_clean"].astype(str).str.strip() != ""]

        options = sorted(df["type_clean"].unique())
        selected = st.multiselect(
            "Select Types (2-4 recommended)",
            options=options,
            default=options[:3] if len(options) >= 3 else options,
            key="matrix_select",
        )

        if len(selected) < 2:
            st.warning("Select at least 2 types.")
            return

        matrix_df = (
            df[df["type_clean"].isin(selected)]
            .groupby(["district", "type_clean"])
            .size()
            .reset_index(name="count")
            .pivot_table(
                index="district",
                columns="type_clean",
                values="count",
                aggfunc="sum",
                fill_value=0,
            )
            .reset_index()
        )

        dim_cols = [t for t in selected if t in matrix_df.columns]

        fig = px.scatter_matrix(
            matrix_df,
            dimensions=dim_cols,
            color="district",
            hover_data=["district"],
            title=None,
        )
        fig.update_traces(marker=dict(size=8, opacity=0.9))
        fig.update_layout(
            height=600,
            margin=dict(l=30, r=30, t=30, b=30),
            plot_bgcolor="#FFFFFF",
            paper_bgcolor="white",
        )
        st.plotly_chart(fig, use_container_width=True)
