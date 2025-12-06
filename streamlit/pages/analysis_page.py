# pages/analysis_page.py

import pandas as pd
import streamlit as st
from components.visualizer import TraffyVisualizer


# --- Page 2: Data Analysis (Datascatter) ---
def render_analysis_page(
    df_filtered: pd.DataFrame,
    df_score: pd.DataFrame,
    type_filter: str,
    df_time_only: pd.DataFrame,
):
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
    t1, t2, t3 = st.tabs(
        ["🔥 Correlation (Metric)", "🔥 Correlation (Type)", "📊 Scatter Matrix"]
    )

    with t1:
        st.subheader("Correlation: Metric x Problem Type")
        visualizer.plot_heatmap_metric_vs_type(df_time_only, df_score)

    with t2:
        st.subheader("Correlation: Problem Type x Problem Type")
        visualizer.plot_heatmap_type_vs_type(df_time_only)

    with t3:
        st.subheader("Multi-Type Scatter Matrix")
        visualizer.plot_scatter_matrix(df_time_only)
