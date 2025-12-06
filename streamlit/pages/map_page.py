# Standard library
import datetime

# External dependencies
import pandas as pd
import streamlit as st

# Project modules
from components.utils import _HAS_SKLEARN, read_config_path
from components.visualizer import (
    plot_choroplethmap,
    plot_choroplethmap_perpop,
    plot_dbscan_map,
    plot_heatmap,
    plot_scatter_map,
)


# --- Page 1: Map Visualizer (Traffy Map Visualize) ---
def render_map_visualizer(
    df_cleansed: pd.DataFrame,
    pop_data: dict,
    type_filter: str,
    start_date: datetime.date,
    end_date: datetime.date,
) -> None:
    st.title("🗺️ Bangkok Traffy Spatial Analysis")
    st.markdown("---")

    # --- New: Map Selection Radio Button ---
    map_mode = st.radio(
        "Select Map Visualization Mode:",
        ("Choropleth/Top 10", "Heatmap", "Scatter Plot", "DBSCAN Clustering"),
        horizontal=True,
    )
    st.markdown("---")

    # 1. Filter dataset and merge with population data
    df_filtered_raw = df_cleansed[
        (df_cleansed["date"] >= pd.Timestamp(start_date))
        & (df_cleansed["date"] <= pd.Timestamp(end_date))
    ].copy()

    if type_filter != "ทั้งหมด":
        type_mask = df_filtered_raw["type_cleaned"].apply(lambda x: type_filter in x)
        df_filtered_raw = df_filtered_raw[type_mask].copy()

    dfs_with_pop = []
    for year, pop_df in pop_data.items():
        df_year = df_filtered_raw[df_filtered_raw["year"] == year]
        if not df_year.empty and not pop_df.empty:
            df_merged = df_year.merge(
                pop_df,
                left_on=["district", "subdistrict"],
                right_on=["district-name", "subdistrict-name"],
                how="left",
            )
            dfs_with_pop.append(df_merged)

    dfwithpop = pd.concat(dfs_with_pop, ignore_index=True)

    if dfwithpop.empty:
        st.info("No data available for the selected filters.")
        return

    # --- Core Metric Calculation (Always needed for Top 10) ---
    total_issues = len(dfwithpop)
    unique_districts = dfwithpop["district"].nunique()
    type_label = type_filter if type_filter != "ทั้งหมด" else ""
    region_path = read_config_path(
        domain="processed", key="cleansed_geographic_data_path"
    )

    # --- Section 1: Key Metrics (KPIs) ---
    st.header("🎯 Key Spatial Metrics")
    kpi1, kpi2, kpi3 = st.columns(3)

    with kpi1:
        st.metric("จำนวนปัญหาทั้งหมด", f"{total_issues:,}")
    with kpi2:
        st.metric(
            "ช่วงเวลาการวิเคราะห์",
            f"{start_date.strftime('%Y-%m-%d')} - {end_date.strftime('%Y-%m-%d')}",
        )
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

        agg_rate_df = (
            dfwithpop.groupby("subdistrict-name")
            .agg(count=("subdistrict-name", "size"), total=("total", "mean"))
            .reset_index()
        )
        agg_rate_df["probperpop"] = (
            agg_rate_df["count"] / agg_rate_df["total"].fillna(1) * 1000
        ).round(2)

        top10_perpop = agg_rate_df.sort_values(by="probperpop", ascending=False).head(
            10
        )[["subdistrict-name", "probperpop"]]
        top10_perpop.columns = ["แขวง", "ความรุนแรง"]

        col1, col2 = st.columns([3, 1])

        with col1:
            st.subheader("จำนวนปัญหาต่อแขวง (Choropleth: Count)")
            choroplethmap = plot_choroplethmap(
                df=dfwithpop, region_path=region_path, type_filter=type_filter
            )
            st.pydeck_chart(choroplethmap, width="stretch", height=380)

            st.markdown("---")

            st.subheader("ความรุนแรงของปัญหาต่อแขวง (Choropleth: Per Population)")
            choroplethmapperpop = plot_choroplethmap_perpop(
                df=dfwithpop, region_path=region_path, type_filter=type_filter
            )
            st.pydeck_chart(choroplethmapperpop, width="stretch", height=380)

        with col2:
            st.subheader(f"1. แขวงที่มีจำนวนปัญหา{type_label}มากที่สุด")
            st.dataframe(
                top10_district.style.format({"จำนวนปัญหา": "{:,.0f}"}),
                width="stretch",
            )
            st.subheader(f"2. แขวงที่มีความรุนแรงของปัญหา{type_label}สูงที่สุด")
            st.dataframe(
                top10_perpop.style.format({"ความรุนแรง": "{:,.2f}"}),
                width="stretch",
            )

    elif map_mode == "DBSCAN Clustering":
        st.header(f"🌀 DBSCAN Cluster Analysis of Problems {type_label}")
        st.caption("DBSCAN groups dense points together, identifying key hotspots.")

        # --- DBSCAN Controls ---
        col_db1, col_db2, col_db3 = st.columns(3)
        with col_db1:
            eps_val = st.slider(
                "1. Cluster Radius (EPS)",
                min_value=0.01,
                max_value=0.5,
                value=0.05,
                step=0.01,
                format="%.2f",
            )
        with col_db2:
            min_samples_val = st.slider(
                "2. Min Cluster Size", min_value=5, max_value=100, value=25, step=5
            )
        with col_db3:
            top_n_val = st.slider(
                "3. Top Clusters to Highlight (N)",
                min_value=1,
                max_value=10,
                value=5,
                step=1,
            )

        st.markdown("---")

        # --- DBSCAN Map ---
        if _HAS_SKLEARN:
            dbscan_map = plot_dbscan_map(
                df=dfwithpop, eps=eps_val, min_samples=min_samples_val, top_n=top_n_val
            )
            st.pydeck_chart(dbscan_map, width="stretch", height=600)

        else:
            # Fallback to the mock function defined in src/utils/visualizer
            plot_dbscan_map()

    elif map_mode == "Heatmap":
        st.header(f"🔥 แผนที่ความหนาแน่นของปัญหา{type_label} (Heatmap)")
        heatmap = plot_heatmap(dfwithpop)
        st.pydeck_chart(heatmap, width="stretch", height=600)

    elif map_mode == "Scatter Plot":
        st.header(f"📍 แผนที่แสดงจุดที่เกิดปัญหา{type_label} (Scatter Map)")
        scatter_map = plot_scatter_map(dfwithpop)
        st.pydeck_chart(scatter_map, width="stretch", height=600)

    st.markdown("---")
