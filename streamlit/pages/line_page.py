# pages/line_page.py

import pandas as pd
import streamlit as st
from components.visualizer import LineChartVisualizer, TraffyVisualizer


# --- Page 3: Line Chart (Line Chart Viewer) ---
def render_line_chart_page(
    df_cleansed: pd.DataFrame, df_filtered: pd.DataFrame, type_filter: str
):
    st.title("📈 Bangkok Traffy Line Chart Viewer")

    # 1. Daily Counts (Timeline)
    visualizer = TraffyVisualizer()
    visualizer.plot_daily_counts(df_filtered, type_filter)
    st.markdown("---")

    # 2. Monthly Trend by Type (Original LineChartVisualizer)
    st.subheader("Monthly Problem Counts by Type (All Types)")
    try:
        # Renaming columns back is still necessary if the external class is being used
        # The LineChartVisualizer expects 'timestamp_year' and 'timestamp_month'
        df_for_viz = df_cleansed.copy()

        col_map = {
            "year": "timestamp_year",
            "month": "timestamp_month",
            "day": "timestamp_date",
        }

        cols_to_rename = {
            old: new for old, new in col_map.items() if old in df_for_viz.columns
        }
        if cols_to_rename:
            df_for_viz.rename(columns=cols_to_rename, inplace=True)

        # Now instantiate and plot
        viz = LineChartVisualizer(df_for_viz)
        fig = viz.plot()

        # Display using Plotly command (as defined by the updated LineChartVisualizer)
        st.plotly_chart(fig, use_container_width=True)

    except Exception as e:
        st.error(f"Error rendering Line Chart: {e}.")
        # st.info("Debugging note: The DataFrame passed has columns: " + ", ".join(df_cleansed.columns))
