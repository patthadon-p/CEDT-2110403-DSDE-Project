# streamlit/Datascatter.py

import datetime
import os
import sys
import pandas as pd
import streamlit as st
import altair as alt
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# -----------------------------------------------------------------------------
# SETUP & CONFIGURATION
# -----------------------------------------------------------------------------

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.append(project_root)

try:
    from src.utils import read_config_path
except ImportError:
    def read_config_path(domain, key):
        return f"data/{domain}/{key}.csv"

st.set_page_config(layout="wide", page_title="Bangkok Traffy Viewer")


# -----------------------------------------------------------------------------
# 1. DATA LOADER CLASS
# -----------------------------------------------------------------------------
class TraffyDataLoader:
    @staticmethod
    @st.cache_data
    def load_cleansed() -> pd.DataFrame:
        path = read_config_path(domain="processed", key="cleansed_data_path")
        df = pd.read_csv(path)
        df["type_cleaned"] = (
            df["type"].astype(str)
            .str.replace("{", "", regex=False)
            .str.replace("}", "", regex=False)
            .str.split(",").apply(tuple)
        )
        df["type_clean"] = df["type_cleaned"].apply(
            lambda x: x[0].strip() if isinstance(x, tuple) and len(x) > 0 else None
        )
        return df

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
# 2. FILTER & LOGIC CLASS
# -----------------------------------------------------------------------------
class TraffyFilter:
    def __init__(self, df: pd.DataFrame):
        self.df = df
        self.type_list = TraffyDataLoader.get_unique_types(df)
        self.default_start = datetime.date(2021, 9, 19)
        self.default_end = datetime.date(2025, 1, 16)

    def render_sidebar(self):
        st.sidebar.header("Filters")
        with st.sidebar.form("filter_form"):
            selected_type = st.selectbox("เลือกประเภทปัญหา", options=["ทั้งหมด"] + self.type_list)
            date_range = st.date_input(
                "เลือกช่วงวัน",
                value=[self.default_start, self.default_end],
                min_value=self.default_start,
                max_value=self.default_end,
            )
            if isinstance(date_range, tuple) and len(date_range) == 2:
                start_date, end_date = date_range
            else:
                start_date, end_date = self.default_start, self.default_end
            submit = st.form_submit_button("Apply Filter")

        if submit:
            st.session_state["type_filter"] = selected_type
            st.session_state["start_date"] = start_date
            st.session_state["end_date"] = end_date

        self.current_type = st.session_state.get("type_filter", "ทั้งหมด")
        self.current_start = st.session_state.get("start_date", self.default_start)
        self.current_end = st.session_state.get("end_date", self.default_end)
        return self.current_type, self.current_start, self.current_end

    def apply_filters(self) -> pd.DataFrame:
        s, e = self.current_start, self.current_end
        mask_time = (
            self.df[["timestamp_year", "timestamp_month", "timestamp_date"]].apply(tuple, axis=1)
            >= (s.year, s.month, s.day)
        ) & (
            self.df[["timestamp_year", "timestamp_month", "timestamp_date"]].apply(tuple, axis=1)
            <= (e.year, e.month, e.day)
        )
        filtered_df = self.df[mask_time]
        if self.current_type != "ทั้งหมด":
            filtered_df = filtered_df[filtered_df["type_clean"] == self.current_type]
        return filtered_df


# -----------------------------------------------------------------------------
# 3. VISUALIZER CLASS
# -----------------------------------------------------------------------------
class TraffyVisualizer:
    """Encapsulates all plotting logic with optimized screen fitting."""

    @staticmethod
    def plot_daily_counts(df: pd.DataFrame, type_label: str):
        label = type_label if type_label != "ทั้งหมด" else "ทั้งหมด"
        st.subheader(f"📈 Timeline: {label}")

        daily_counts = (
            df.groupby(["timestamp_year", "timestamp_month", "timestamp_date"])
            .size()
            .reset_index(name="count")
        )

        if daily_counts.empty:
            st.warning("No data for this selection.")
            return

        daily_counts["date"] = pd.to_datetime(daily_counts.rename(
            columns={"timestamp_year": "year", "timestamp_month": "month", "timestamp_date": "day"}
        )[["year", "month", "day"]])
        
        daily_counts["year_month"] = daily_counts["date"].dt.to_period("M").astype(str)

        fig = px.scatter(
            daily_counts, x="date", y="count", color="year_month",
            labels={"date": "Date", "count": "Issues", "year_month": "Month"},
            hover_data=["date", "count"],
        )
        fig.add_trace(px.line(daily_counts, x="date", y="count").data[0])
        
        # OPTIMIZATION: Reduced height to 380px, tighter margins
        fig.update_traces(marker=dict(size=6, opacity=0.8))
        fig.update_layout(
            height=380, 
            margin=dict(l=20, r=20, t=30, b=20),
            legend_title_text=None,
            hovermode="x unified"
        )
        st.plotly_chart(fig, use_container_width=True)

    @staticmethod
    def plot_score_vs_complaints(df_filtered: pd.DataFrame, df_score: pd.DataFrame):
        # We assume the header is handled outside to allow column layout
        if "district" not in df_filtered.columns:
            st.error("Missing 'district' column.")
            return

        complaints = df_filtered.groupby("district").size().reset_index(name="complaints")
        merged = df_score.merge(complaints, on="district", how="left")
        merged["complaints"] = merged["complaints"].fillna(0)

        if merged["complaints"].sum() == 0:
            st.info("No complaints found.")
            return

        low_score_th = merged["total_score"].quantile(0.3)
        high_complaints_th = merged["complaints"].quantile(0.7)

        def get_zone(row):
            if row["total_score"] < low_score_th and row["complaints"] > high_complaints_th:
                return "Danger"
            elif row["total_score"] >= low_score_th and row["complaints"] > high_complaints_th:
                return "Active"
            elif row["total_score"] < low_score_th and row["complaints"] <= high_complaints_th:
                return "Silent Risk"
            else:
                return "Good"

        merged["zone"] = merged.apply(get_zone, axis=1)
        
        zone_order = ["Danger", "Active", "Silent Risk", "Good"]
        color_map = {"Danger": "red", "Active": "#ff7f0e", "Silent Risk": "#2ca02c", "Good": "#1f77b4"}

        fig = px.scatter(
            merged, x="total_score", y="complaints", color="zone",
            category_orders={"zone": zone_order}, color_discrete_map=color_map,
            hover_data=["district", "total_score", "complaints"],
            title="Total Score vs Complaints"
        )
        
        # OPTIMIZATION: Height 450px, remove legend title, add dashed lines
        fig.update_traces(marker=dict(size=12, opacity=0.8))
        fig.add_vline(x=float(low_score_th), line_dash="dash", line_color="gray", opacity=0.5)
        fig.add_hline(y=float(high_complaints_th), line_dash="dash", line_color="gray", opacity=0.5)
        
        fig.update_layout(
            height=510 ,
            margin=dict(l=20, r=20, t=60, b=20),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1, title=None)
        )

        st.plotly_chart(fig, use_container_width=True)

    @staticmethod
    def plot_quality_dimensions(df_filtered: pd.DataFrame, df_score: pd.DataFrame):
        if "district" not in df_filtered.columns:
            return

        complaints = df_filtered.groupby("district").size().reset_index(name="complaints")
        merged = df_score.merge(complaints, on="district", how="left")
        merged["complaints"] = merged["complaints"].fillna(0)

        metrics = ["public_service", "economy", "welfare", "environment"]
        titles = {m: m.replace("_", " ").title() for m in metrics}

        fig = make_subplots(rows=2, cols=2, subplot_titles=[titles[m] for m in metrics])

        for i, m in enumerate(metrics):
            row = i // 2 + 1
            col = i % 2 + 1
            fig.add_trace(
                go.Scatter(
                    x=merged[m], y=merged["complaints"], mode="markers",
                    marker=dict(
                        size=10, opacity=1, color=merged["complaints"],
                        colorscale="RdYlBu", reversescale=True,
                        showscale=False # Removed colorbar to save space
                    ),
                    text=merged["district"],
                    hovertemplate=f"<b>%{{text}}</b><br>{titles[m]}: %{{x}}<br>Complaints: %{{y}}<extra></extra>"
                ), row=row, col=col
            )
            # Minimal axes
            fig.update_xaxes(title_text=None, row=row, col=col, showgrid=True)
            fig.update_yaxes(showgrid=True, row=row, col=col)

        # OPTIMIZATION: Share Y axes, Height 500px (compact 2x2)
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

        if df.empty: return

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

        # OPTIMIZATION: Fixed modest height
        heatmap = alt.Chart(corr_sub).mark_rect().encode(
            x=alt.X("problem_type:N", title=None, sort=type_cols),
            y=alt.Y("metric:N", title=None, sort=metric_cols),
            color=alt.Color("corr:Q", scale=alt.Scale(scheme="redblue", domain=[-1, 0, 1])),
            tooltip=["metric", "problem_type", alt.Tooltip("corr", format=".2f")]
        ).properties(
            height=350,  # Compact height
            title="Correlation: Metric x Type"
        )
        st.altair_chart(heatmap, use_container_width=True)

    @staticmethod
    def plot_heatmap_type_vs_type(df_base: pd.DataFrame):
        # Logic to select triangle mode
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
        if pivot_problems.shape[1] < 2: return

        corr_matrix = pivot_problems.corr(method="pearson")
        corr_long = corr_matrix.reset_index().melt(
            id_vars="type_clean", var_name="problem_type_2", value_name="corr"
        ).rename(columns={"type_clean": "problem_type_1"})

        # Filtering triangle
        problem_list = list(corr_matrix.index)
        idx_map = {p: i for i, p in enumerate(problem_list)}
        corr_long["i"] = corr_long["problem_type_1"].map(idx_map)
        corr_long["j"] = corr_long["problem_type_2"].map(idx_map)

        if triangle_mode == "Upper": corr_long = corr_long[corr_long["i"] < corr_long["j"]]
        elif triangle_mode == "Lower": corr_long = corr_long[corr_long["i"] > corr_long["j"]]

        # OPTIMIZATION: Dynamic but constrained sizing
        # We limit the max size to prevent it from blowing up the screen
        cell_size = 25 if len(problem_list) > 15 else 35
        
        heatmap = alt.Chart(corr_long).mark_rect().encode(
            x=alt.X("problem_type_2:N", title=None), # Hide X labels to save space
            y=alt.Y("problem_type_1:N", title=None),
            color=alt.Color("corr:Q", scale=alt.Scale(scheme="redblue", domain=[-1, 0, 1])),
            tooltip=["problem_type_1", "problem_type_2", alt.Tooltip("corr", format=".2f")]
        ).properties(
            width=cell_size * (len(problem_list)*1.5),
            height=cell_size * (len(problem_list)*1.5),
            title="Correlation: Type x Type"
        )
        st.altair_chart(heatmap, use_container_width=False) # Allow scrolling if large

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
        
        # OPTIMIZATION: Height 600px, removed fixed width
        fig = px.scatter_matrix(
            matrix_df, dimensions=dim_cols, color="district",
            hover_data=["district"], title=None
        )
        fig.update_traces(marker=dict(size=8, opacity=0.9))
        fig.update_layout(
            height=600, 
            margin=dict(l=30, r=30, t=30, b=30),
            plot_bgcolor="#FFFFFF", paper_bgcolor="white"
            
        )
        st.plotly_chart(fig, use_container_width=True)


# -----------------------------------------------------------------------------
# 4. MAIN APP CONTROLLER
# -----------------------------------------------------------------------------
class TraffyApp:
    def __init__(self):
        self.visualizer = TraffyVisualizer()
        
    def run(self):
        st.title("Bangkok Traffy Viewer")
        
        # 1. Load & Filter
        df_cleansed = TraffyDataLoader.load_cleansed()
        df_score = TraffyDataLoader.load_scores()
        filter_manager = TraffyFilter(df_cleansed)
        type_filter, _, _ = filter_manager.render_sidebar()
        
        df_filtered = filter_manager.apply_filters()
        
        # Time-only filter for Heatmaps
        filter_manager.current_type = "ทั้งหมด"
        df_time_only = filter_manager.apply_filters()
        filter_manager.current_type = type_filter

        # ---------------------------------------------------------------------
        # LAYOUT: Top Section (Timeline)
        # ---------------------------------------------------------------------
        self.visualizer.plot_daily_counts(df_filtered, type_filter)

        st.markdown("---")

        # ---------------------------------------------------------------------
        # LAYOUT: Middle Section (2 Columns for Core Analysis)
        # ---------------------------------------------------------------------
        c1, c2 = st.columns(2)
        
        with c1:
            st.subheader("📌 Overview: Score vs Complaints")
            self.visualizer.plot_score_vs_complaints(df_filtered, df_score)
        
        with c2:
            st.subheader("📌 Quality Dimensions")
            self.visualizer.plot_quality_dimensions(df_filtered, df_score)

        st.markdown("---")

        # ---------------------------------------------------------------------
        # LAYOUT: Middle Section (กลับสู่การเรียงซ้อนกันตามแถว)
        # ---------------------------------------------------------------------

        # ส่วนที่ 1: Total Score vs Complaints (จะอยู่ในแถวบนสุด)
        # st.subheader("📌 Overview: Score vs Complaints")
        # self.visualizer.plot_score_vs_complaints(df_filtered, df_score)

        # st.markdown("---") # เพิ่มเส้นแบ่งเพื่อให้ดูแยกแถวชัดเจน

        # # ส่วนที่ 2: Quality Dimensions (จะอยู่ในแถวถัดไป)
        # st.subheader("📌 Quality Dimensions")
        # self.visualizer.plot_quality_dimensions(df_filtered, df_score)

        # st.markdown("---")

        # ---------------------------------------------------------------------
        # LAYOUT: Bottom Section (Tabs for Heavy Analysis)
        # ---------------------------------------------------------------------
        # Using Tabs hides the large/complex charts so they don't clutter the screen
        # until the user actively wants to explore them.
        t1, t2, t3 = st.tabs(["🔥 Correlation (Metric)", "🔥 Correlation (Type)", "📊 Scatter Matrix"])

        with t1:
            self.visualizer.plot_heatmap_metric_vs_type(df_time_only, df_score)
        
        with t2:
            self.visualizer.plot_heatmap_type_vs_type(df_time_only)
            
        with t3:
            self.visualizer.plot_scatter_matrix(df_time_only)


if __name__ == "__main__":
    app = TraffyApp()
    app.run()