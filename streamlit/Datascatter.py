# import datetime
# import os
# import sys
# import pandas as pd
# import streamlit as st
# import altair as alt
# import plotly.express as px
# import plotly.graph_objects as go
# from plotly.subplots import make_subplots

# # -----------------------------------------------------------------------------
# # SETUP & CONFIGURATION
# # -----------------------------------------------------------------------------

# # Add project root to Python path
# project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# if project_root not in sys.path:
#     sys.path.append(project_root)

# # Try importing the utility; if it fails, user might need to adjust path
# try:
#     from src.utils import read_config_path
# except ImportError:
#     # Fallback or placeholder if src.utils is missing in this context
#     def read_config_path(domain, key):
#         return f"data/{domain}/{key}.csv" # Dummy implementation

# st.set_page_config(layout="wide", page_title="Bangkok Traffy Viewer")


# # -----------------------------------------------------------------------------
# # 1. DATA LOADER CLASS
# # -----------------------------------------------------------------------------
# class TraffyDataLoader:
#     """Handles loading and cleaning of raw data."""

#     @staticmethod
#     @st.cache_data
#     def load_cleansed() -> pd.DataFrame:
#         path = read_config_path(domain="processed", key="cleansed_data_path")
#         df = pd.read_csv(path)

#         # Process 'type' column to extract lists
#         df["type_cleaned"] = (
#             df["type"]
#             .astype(str)
#             .str.replace("{", "", regex=False)
#             .str.replace("}", "", regex=False)
#             .str.split(",")
#             .apply(tuple)
#         )

#         # Extract single main category
#         df["type_clean"] = df["type_cleaned"].apply(
#             lambda x: x[0].strip() if isinstance(x, tuple) and len(x) > 0 else None
#         )
#         return df

#     @staticmethod
#     @st.cache_data
#     def load_scores() -> pd.DataFrame:
#         path = read_config_path(domain="scrapping", key="bangkok_index_scrapped_path")
#         return pd.read_csv(path)

#     @staticmethod
#     @st.cache_data
#     def get_unique_types(df: pd.DataFrame) -> list:
#         clean_list = []
#         for row in df["type_cleaned"]:
#             for t in row:
#                 if pd.notna(t) and str(t).strip() != "":
#                     clean_list.append(t.strip())
#         return sorted(set(clean_list))


# # -----------------------------------------------------------------------------
# # 2. FILTER & LOGIC CLASS
# # -----------------------------------------------------------------------------
# class TraffyFilter:
#     """Handles sidebar rendering and data filtering logic."""

#     def __init__(self, df: pd.DataFrame):
#         self.df = df
#         self.type_list = TraffyDataLoader.get_unique_types(df)
        
#         # Defaults
#         self.default_start = datetime.date(2021, 9, 19)
#         self.default_end = datetime.date(2025, 1, 16)

#     def render_sidebar(self):
#         st.sidebar.header("Filters")
#         with st.sidebar.form("filter_form"):
#             selected_type = st.selectbox("เลือกประเภทปัญหา", options=["ทั้งหมด"] + self.type_list)
            
#             date_range = st.date_input(
#                 "เลือกช่วงวัน",
#                 value=[self.default_start, self.default_end],
#                 min_value=self.default_start,
#                 max_value=self.default_end,
#             )

#             # Validate date range
#             if isinstance(date_range, tuple) and len(date_range) == 2:
#                 start_date, end_date = date_range
#             else:
#                 start_date, end_date = self.default_start, self.default_end

#             submit = st.form_submit_button("Apply Filter")

#         if submit:
#             st.session_state["type_filter"] = selected_type
#             st.session_state["start_date"] = start_date
#             st.session_state["end_date"] = end_date

#         # Retrieve from state or use defaults
#         self.current_type = st.session_state.get("type_filter", "ทั้งหมด")
#         self.current_start = st.session_state.get("start_date", self.default_start)
#         self.current_end = st.session_state.get("end_date", self.default_end)

#         return self.current_type, self.current_start, self.current_end

#     def apply_filters(self) -> pd.DataFrame:
#         """Filters the dataframe based on current session state params."""
#         s, e = self.current_start, self.current_end
        
#         # Filter by Time
#         # Converting columns to tuple for comparison as per original logic
#         mask_time = (
#             self.df[["timestamp_year", "timestamp_month", "timestamp_date"]]
#             .apply(tuple, axis=1)
#             >= (s.year, s.month, s.day)
#         ) & (
#             self.df[["timestamp_year", "timestamp_month", "timestamp_date"]]
#             .apply(tuple, axis=1)
#             <= (e.year, e.month, e.day)
#         )
        
#         filtered_df = self.df[mask_time]

#         # Filter by Type
#         if self.current_type != "ทั้งหมด":
#             filtered_df = filtered_df[filtered_df["type_clean"] == self.current_type]

#         return filtered_df


# # -----------------------------------------------------------------------------
# # 3. VISUALIZER CLASS
# # -----------------------------------------------------------------------------
# class TraffyVisualizer:
#     """Encapsulates all plotting logic (Plotly & Altair)."""

#     @staticmethod
#     def plot_daily_counts(df: pd.DataFrame, type_label: str):
#         st.markdown("---")
#         label = type_label if type_label != "ทั้งหมด" else "ทั้งหมด"
#         st.subheader(f"📈 จำนวนปัญหา {label} ตามเวลา (Plotly Scatter)")

#         daily_counts = (
#             df.groupby(["timestamp_year", "timestamp_month", "timestamp_date"])
#             .size()
#             .reset_index(name="count")
#         )

#         if daily_counts.empty:
#             st.warning("ไม่มีข้อมูลในช่วงเวลาหรือประเภทที่เลือก")
#             return

#         # Create proper datetime column
#         daily_counts["date"] = pd.to_datetime(daily_counts.rename(
#             columns={"timestamp_year": "year", "timestamp_month": "month", "timestamp_date": "day"}
#         )[["year", "month", "day"]])
        
#         daily_counts["year_month"] = daily_counts["date"].dt.to_period("M").astype(str)

#         fig = px.scatter(
#             daily_counts, x="date", y="count", color="year_month",
#             title="Daily Complaints Over Time",
#             labels={"date": "วันที่", "count": "จำนวนปัญหา", "year_month": "เดือน"},
#             hover_data=["date", "count", "year_month"],
#         )
#         # Add line trace
#         fig.add_trace(px.line(daily_counts, x="date", y="count").data[0])
#         fig.update_traces(marker=dict(size=8, opacity=0.8))
#         fig.update_layout(height=450, legend_title_text="เดือน", hovermode="x unified")
        
#         st.plotly_chart(fig, use_container_width=True)

#     @staticmethod
#     def plot_score_vs_complaints(df_filtered: pd.DataFrame, df_score: pd.DataFrame):
#         st.markdown("---")
#         st.subheader("📌 Total Score vs Complaints ")

#         if "district" not in df_filtered.columns:
#             st.error("Missing 'district' column.")
#             return

#         complaints = df_filtered.groupby("district").size().reset_index(name="complaints")
#         merged = df_score.merge(complaints, on="district", how="left")
#         merged["complaints"] = merged["complaints"].fillna(0)

#         if merged["complaints"].sum() == 0:
#             st.info("ไม่มีเรื่องร้องเรียนใด ๆ ในช่วงเวลา / ประเภทที่เลือก")
#             return

#         # Zone Logic
#         low_score_th = merged["total_score"].quantile(0.3)
#         high_complaints_th = merged["complaints"].quantile(0.7)

#         def get_zone(row):
#             if row["total_score"] < low_score_th and row["complaints"] > high_complaints_th:
#                 return "Danger Zone"
#             elif row["total_score"] >= low_score_th and row["complaints"] > high_complaints_th:
#                 return "Active Zone"
#             elif row["total_score"] < low_score_th and row["complaints"] <= high_complaints_th:
#                 return "Silent Risk Zone"
#             else:
#                 return "Good Zone"

#         merged["zone"] = merged.apply(get_zone, axis=1)
        
#         zone_order = ["Danger Zone", "Active Zone", "Silent Risk Zone", "Good Zone"]
#         color_map = {
#             "Danger Zone": "red", "Active Zone": "#ff7f0e",
#             "Silent Risk Zone": "#2ca02c", "Good Zone": "#1f77b4"
#         }

#         fig = px.scatter(
#             merged, x="total_score", y="complaints", color="zone",
#             category_orders={"zone": zone_order}, color_discrete_map=color_map,
#             hover_data=["district", "total_score", "complaints", "zone"],
#             title="Total Score vs Complaints by District"
#         )
        
#         fig.update_traces(marker=dict(size=15, opacity=0.9))
#         fig.update_xaxes(range=[10, 40], title="Total Score")
#         fig.update_yaxes(range=[0, 20000], title="Number of Complaints")
        
#         # Threshold lines
#         fig.add_vline(x=float(low_score_th), line_dash="dash", line_color="black")
#         fig.add_hline(y=float(high_complaints_th), line_dash="dash", line_color="black")
#         fig.update_layout(height=600, hovermode="closest")

#         st.plotly_chart(fig, use_container_width=True)

#     @staticmethod
#     def plot_quality_dimensions(df_filtered: pd.DataFrame, df_score: pd.DataFrame, type_label: str):
#         st.markdown("---")
#         st.subheader("📌 Scatter Plot - จำนวนร้องเรียน เทียบกับมิติคุณภาพเขต")
        
#         if "district" not in df_filtered.columns:
#             return

#         complaints = df_filtered.groupby("district").size().reset_index(name="complaints")
#         merged = df_score.merge(complaints, on="district", how="left")
#         merged["complaints"] = merged["complaints"].fillna(0)

#         metrics = ["public_service", "economy", "welfare", "environment"]
#         titles = {m: m.replace("_", " ").title() for m in metrics}

#         fig = make_subplots(rows=2, cols=2, subplot_titles=[titles[m] for m in metrics])

#         for i, m in enumerate(metrics):
#             row = i // 2 + 1
#             col = i % 2 + 1
#             fig.add_trace(
#                 go.Scatter(
#                     x=merged[m], y=merged["complaints"], mode="markers",
#                     marker=dict(
#                         size=12, opacity=0.7, color=merged["complaints"],
#                         colorscale="RdYlBu", reversescale=True,
#                         showscale=(i==0), colorbar=dict(title="Complaints") if i==0 else None
#                     ),
#                     text=merged["district"],
#                     hovertemplate=f"เขต: %{{text}}<br>{titles[m]}: %{{x}}<br>Complaints: %{{y}}<extra></extra>"
#                 ), row=row, col=col
#             )
#             fig.update_xaxes(title_text=titles[m], row=row, col=col)

#         fig.update_yaxes(title_text=f"จำนวนร้องเรียน ({type_label if type_label else 'ทั้งหมด'})", matches="y")
#         fig.update_layout(height=650, showlegend=False, title_text="Scatter: มิติคุณภาพเขต vs จำนวนร้องเรียน")
#         st.plotly_chart(fig, use_container_width=True)

#     @staticmethod
#     def plot_heatmap_metric_vs_type(df_base: pd.DataFrame, df_score: pd.DataFrame):
#         st.markdown("---")
#         st.subheader("🔥 Pearson Heatmap – ความสัมพันธ์ระหว่างมิติคุณภาพเขตกับประเภทปัญหา")

#         df = df_base.dropna(subset=["type_clean"]).copy()
#         df = df[df["type_clean"].astype(str).str.strip() != ""]

#         if df.empty or "district" not in df.columns:
#             st.info("ข้อมูลไม่เพียงพอสำหรับ Heatmap")
#             return

#         # Prepare Data
#         pivot_types = (
#             df.groupby(["district", "type_clean"]).size()
#             .reset_index(name="complaints")
#             .pivot(index="district", columns="type_clean", values="complaints")
#             .fillna(0).reset_index()
#         )
        
#         corr_df = df_score.merge(pivot_types, on="district", how="left").fillna(0)
        
#         metric_cols = ["total_score", "public_service", "economy", "welfare", "environment"]
#         type_cols = [c for c in corr_df.columns if c not in metric_cols + ["district"]]

#         if not type_cols:
#             st.info("ไม่พบคอลัมน์ประเภทปัญหา")
#             return

#         # Correlation
#         corr_matrix = corr_df[metric_cols + type_cols].corr(method="pearson")
#         corr_sub = corr_matrix.loc[metric_cols, type_cols].reset_index().melt(
#             id_vars="index", var_name="problem_type", value_name="corr"
#         ).rename(columns={"index": "metric"})

#         # Altair Plot
#         heatmap = alt.Chart(corr_sub).mark_rect().encode(
#             x=alt.X("problem_type:N", title="ประเภทปัญหา", sort=type_cols),
#             y=alt.Y("metric:N", title="มิติคุณภาพเขต", sort=metric_cols),
#             color=alt.Color("corr:Q", title="Pearson r", scale=alt.Scale(scheme="redblue", domain=[-1, 0, 1])),
#             tooltip=["metric", "problem_type", alt.Tooltip("corr", format=".2f")]
#         ).properties(width=400, height=400, title="Pearson Correlation: District Metrics × Problem Types")
        
#         st.altair_chart(heatmap, use_container_width=True)

#     @staticmethod
#     def plot_heatmap_type_vs_type(df_base: pd.DataFrame):
#         st.markdown("---")
#         st.subheader("🔥 Pearson Heatmap – ความสัมพันธ์ระหว่าง 'ประเภทปัญหา' ด้วยกันเอง")

#         triangle_mode = st.sidebar.selectbox(
#             "แสดง Heatmap ความสัมพันธ์ระหว่างประเภทปัญหาแบบ:",
#             ["Full Matrix", "Upper Triangle", "Lower Triangle"],
#             index=2, key="problem_corr_triangle_mode"
#         )

#         df = df_base.dropna(subset=["type_clean"]).copy()
#         df = df[df["type_clean"].astype(str).str.strip() != ""]

#         if df.empty or "district" not in df.columns:
#             st.info("ข้อมูลไม่เพียงพอ")
#             return

#         pivot_problems = (
#             df.groupby(["district", "type_clean"]).size()
#             .reset_index(name="complaints")
#             .pivot(index="district", columns="type_clean", values="complaints")
#             .fillna(0)
#         )

#         if pivot_problems.shape[1] < 2:
#             st.info("จำนวนประเภทปัญหาน้อยเกินไป (< 2)")
#             return

#         corr_matrix = pivot_problems.corr(method="pearson")
#         corr_long = corr_matrix.reset_index().melt(
#             id_vars="type_clean", var_name="problem_type_2", value_name="corr"
#         ).rename(columns={"type_clean": "problem_type_1"})

#         # Triangle Logic
#         problem_list = list(corr_matrix.index)
#         idx_map = {p: i for i, p in enumerate(problem_list)}
#         corr_long["i"] = corr_long["problem_type_1"].map(idx_map)
#         corr_long["j"] = corr_long["problem_type_2"].map(idx_map)

#         if triangle_mode == "Upper Triangle":
#             corr_long = corr_long[corr_long["i"] < corr_long["j"]]
#         elif triangle_mode == "Lower Triangle":
#             corr_long = corr_long[corr_long["i"] > corr_long["j"]]

#         heatmap = alt.Chart(corr_long).mark_rect().encode(
#             x=alt.X("problem_type_2:N", title="ประเภทปัญหา 2", sort=problem_list),
#             y=alt.Y("problem_type_1:N", title="ประเภทปัญหา 1", sort=problem_list),
#             color=alt.Color("corr:Q", scale=alt.Scale(scheme="redblue", domain=[-1, 0, 1])),
#             tooltip=["problem_type_1", "problem_type_2", alt.Tooltip("corr", format=".2f")]
#         ).properties(
#             width=40 * max(6, len(problem_list)),
#             height=40 * max(6, len(problem_list)),
#             title=f"Pearson Correlation ({triangle_mode})"
#         )
#         st.altair_chart(heatmap, use_container_width=True)

#     @staticmethod
#     def plot_scatter_matrix(df_time_filtered: pd.DataFrame):
#         st.markdown("---")
#         st.subheader("📊 Scatter Matrix - เปรียบเทียบจำนวนปัญหาระหว่างประเภท (ต่อเขต)")

#         df = df_time_filtered.dropna(subset=["type_clean"]).copy()
#         df = df[df["type_clean"].astype(str).str.strip() != ""]
        
#         options = sorted(df["type_clean"].unique())
#         selected = st.multiselect(
#             "เลือกประเภทปัญหา (2–5)", options=options,
#             default=options[:5] if len(options) >= 5 else options,
#             key="scatter_matrix_v3"
#         )

#         if len(selected) < 2:
#             st.warning("กรุณาเลือกอย่างน้อย 2 ประเภท")
#             return

#         matrix_df = (
#             df[df["type_clean"].isin(selected)]
#             .groupby(["district", "type_clean"]).size()
#             .reset_index(name="count")
#             .pivot_table(index="district", columns="type_clean", values="count", aggfunc="sum", fill_value=0)
#             .reset_index()
#         )

#         dim_cols = [t for t in selected if t in matrix_df.columns]
#         if len(dim_cols) < 2:
#             st.warning("ข้อมูลไม่เพียงพอหลัง Pivot")
#             return

#         fig = px.scatter_matrix(
#             matrix_df, dimensions=dim_cols, color="district",
#             hover_data=["district"], title="Scatter Matrix"
#         )
#         fig.update_traces(marker=dict(size=7, opacity=0.8))
#         fig.update_layout(height=700, width=900, plot_bgcolor="#F8FAFC", paper_bgcolor="white")
#         st.plotly_chart(fig, use_container_width=True)


# # -----------------------------------------------------------------------------
# # 4. MAIN APP CONTROLLER
# # -----------------------------------------------------------------------------
# class TraffyApp:
#     def __init__(self):
#         st.title("Bangkok Traffy - Scatter Viewer")
#         self.visualizer = TraffyVisualizer()
        
#     def run(self):
#         # 1. Load Data
#         df_cleansed = TraffyDataLoader.load_cleansed()
#         df_score = TraffyDataLoader.load_scores()

#         # 2. Sidebar & Filtering
#         filter_manager = TraffyFilter(df_cleansed)
#         type_filter, start_date, end_date = filter_manager.render_sidebar()
        
#         # Apply filters (returns df specific to time AND type)
#         df_filtered_fully = filter_manager.apply_filters()
        
#         # We also need a version filtered ONLY by time (for comparisons across types)
#         # Manually create a time-only filtered df for the heatmaps/matrices
#         filter_manager.current_type = "ทั้งหมด" # Temporarily reset to get time-only
#         df_filtered_time_only = filter_manager.apply_filters()
#         filter_manager.current_type = type_filter # Restore

#         # 3. Visualizations
#         self.visualizer.plot_daily_counts(df_filtered_fully, type_filter)
        
#         self.visualizer.plot_score_vs_complaints(df_filtered_fully, df_score)
        
#         self.visualizer.plot_quality_dimensions(df_filtered_fully, df_score, type_filter)
        
#         # Note: Heatmaps and Scatter Matrix usually use data filtered by TIME, 
#         # but compare ALL TYPES, so we use df_filtered_time_only
#         self.visualizer.plot_heatmap_metric_vs_type(df_filtered_time_only, df_score)
        
#         self.visualizer.plot_heatmap_type_vs_type(df_filtered_time_only)
        
#         self.visualizer.plot_scatter_matrix(df_filtered_time_only)


# # -----------------------------------------------------------------------------
# # EXECUTION
# # -----------------------------------------------------------------------------
# if __name__ == "__main__":
#     app = TraffyApp()
#     app.run()
# app_scatter_viewer_oop.py

from dataclasses import dataclass
from typing import List
import datetime
import os
import sys

import matplotlib.pyplot as plt  # (ยังคง import ไว้ แม้ตอนนี้จะไม่ได้ใช้)
import plotly.express as px
from plotly.subplots import make_subplots
import plotly.graph_objects as go
import altair as alt
import pandas as pd
import streamlit as st

# -------------------------------------------------
# 0) PROJECT PATH & CONFIG
# -------------------------------------------------

# Add project root to Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.append(project_root)

from src.utils import read_config_path  # noqa: E402

# Streamlit page configuration
st.set_page_config(layout="wide")


# -------------------------------------------------
# 1) CACHED UTILITY FUNCTIONS
# -------------------------------------------------

@st.cache_data
def _load_cleansed() -> pd.DataFrame:
    """
    Load cleansed Traffy data and add:
      - type_cleaned: tuple of categories
      - type_clean: first (main) category
    """
    df = pd.read_csv(read_config_path(domain="processed", key="cleansed_data_path"))

    # list of categories (tuple per row)
    df["type_cleaned"] = (
        df["type"]
        .astype(str)
        .str.replace("{", "", regex=False)
        .str.replace("}", "", regex=False)
        .str.split(",")
        .apply(tuple)
    )

    # single main category
    df["type_clean"] = df["type_cleaned"].apply(
        lambda x: x[0].strip() if isinstance(x, tuple) and len(x) > 0 else None
    )

    return df


@st.cache_data
def _load_scores() -> pd.DataFrame:
    """
    Load Bangkok index (score) data for 50 districts.
    """
    return pd.read_csv(
        read_config_path(domain="scrapping", key="bangkok_index_scrapped_path")
    )


@st.cache_data
def _get_type_list(df: pd.DataFrame) -> List[str]:
    """
    Extract unique problem types from 'type_cleaned' column.
    """
    clean_list: List[str] = []
    for row in df["type_cleaned"]:
        for t in row:
            if pd.notna(t) and str(t).strip() != "":
                clean_list.append(str(t).strip())
    return sorted(set(clean_list))


# -------------------------------------------------
# 2) DATA CLASSES & LOADER
# -------------------------------------------------

@dataclass
class FilterOptions:
    type_filter: str
    start_date: datetime.date
    end_date: datetime.date


class TraffyDataLoader:
    """
    Handle data loading (with caching) and simple pre-computed lists.
    """

    def __init__(self) -> None:
        self._cleansed = _load_cleansed()
        self._scores = _load_scores()
        self._type_list = _get_type_list(self._cleansed)

    @property
    def cleansed(self) -> pd.DataFrame:
        return self._cleansed

    @property
    def scores(self) -> pd.DataFrame:
        return self._scores

    @property
    def type_list(self) -> List[str]:
        return self._type_list


# -------------------------------------------------
# 3) SIDEBAR FILTER PANEL
# -------------------------------------------------

class FilterPanel:
    """
    Render sidebar filters (type + date range) and return FilterOptions.
    """

    def __init__(
        self,
        type_list: List[str],
        default_start: datetime.date,
        default_end: datetime.date,
    ) -> None:
        self.type_list = type_list
        self.default_start = default_start
        self.default_end = default_end

    def render(self) -> FilterOptions:
        st.sidebar.header("Filters")

        with st.sidebar.form("filter_form"):
            type_filter = st.selectbox(
                "เลือกประเภทปัญหา",
                options=["ทั้งหมด"] + self.type_list,
            )

            date_range = st.date_input(
                "เลือกช่วงวัน",
                value=[self.default_start, self.default_end],
                min_value=self.default_start,
                max_value=self.default_end,
            )

            # date_input with range returns list/tuple of 2 dates
            if isinstance(date_range, (list, tuple)) and len(date_range) == 2:
                start_date, end_date = date_range
            else:
                start_date, end_date = self.default_start, self.default_end

            submit = st.form_submit_button("Apply Filter")

        # Persist in session state (same behavior as original code)
        if submit:
            st.session_state["type_filter"] = type_filter
            st.session_state["start_date"] = start_date
            st.session_state["end_date"] = end_date

        final_type_filter = st.session_state.get("type_filter", "ทั้งหมด")
        final_start = st.session_state.get("start_date", self.default_start)
        final_end = st.session_state.get("end_date", self.default_end)

        return FilterOptions(
            type_filter=final_type_filter,
            start_date=final_start,
            end_date=final_end,
        )


# -------------------------------------------------
# 4) FILTERED VIEW ON DATA
# -------------------------------------------------

class TraffyView:
    """
    A view over the cleansed data with given filter options.
    Provides:
      - filtered_time: filter by date only
      - filtered_by_type: filter by date + type
    """

    def __init__(self, df_cleansed: pd.DataFrame, filters: FilterOptions) -> None:
        self.df_cleansed = df_cleansed
        self.filters = filters

        self.filtered_time = self._filter_by_time()
        self.filtered_by_type = self._filter_by_type()

    def _filter_by_time(self) -> pd.DataFrame:
        f = self.filters
        df = self.df_cleansed

        mask = (
            df[["timestamp_year", "timestamp_month", "timestamp_date"]].apply(
                tuple, axis=1
            )
            >= (f.start_date.year, f.start_date.month, f.start_date.day)
        ) & (
            df[["timestamp_year", "timestamp_month", "timestamp_date"]].apply(
                tuple, axis=1
            )
            <= (f.end_date.year, f.end_date.month, f.end_date.day)
        )

        return df[mask].copy()

    def _filter_by_type(self) -> pd.DataFrame:
        if self.filters.type_filter != "ทั้งหมด":
            return self.filtered_time[
                self.filtered_time["type_clean"] == self.filters.type_filter
            ]
        return self.filtered_time.copy()


# -------------------------------------------------
# 5) CHART RENDERER (ALL SECTIONS)
# -------------------------------------------------

class TraffyCharts:
    """
    Render all charts using the filtered view and score data.
    """

    def __init__(
        self,
        view: TraffyView,
        df_score: pd.DataFrame,
        filters: FilterOptions,
    ) -> None:
        self.view = view
        self.df_score = df_score
        self.filters = filters

    # -----------------------------
    # 5.1 SCATTER: DAILY COUNTS OVER TIME
    # -----------------------------
    def show_daily_counts(self) -> None:
        gdf_filtered = self.view.filtered_by_type.copy()
        daily_counts = (
            gdf_filtered.groupby(
                ["timestamp_year", "timestamp_month", "timestamp_date"]
            )
            .size()
            .reset_index(name="count")
        )

        if daily_counts.empty:
            st.warning("ไม่มีข้อมูลในช่วงเวลาหรือประเภทที่เลือก")
            return

        daily_counts["date"] = pd.to_datetime(
            daily_counts[["timestamp_year", "timestamp_month", "timestamp_date"]].rename(
                columns={
                    "timestamp_year": "year",
                    "timestamp_month": "month",
                    "timestamp_date": "day",
                }
            )
        )
        daily_counts["year_month"] = daily_counts["date"].dt.to_period("M").astype(str)

        st.markdown("---")
        st.subheader(
            f"📈 จำนวนปัญหา "
            f"{self.filters.type_filter if self.filters.type_filter != 'ทั้งหมด' else 'ทั้งหมด'} "
            f"ตามเวลา (Plotly Scatter)"
        )

        # scatter + line
        fig = px.scatter(
            daily_counts,
            x="date",
            y="count",
            color="year_month",
            title="Daily Complaints Over Time",
            labels={"date": "วันที่", "count": "จำนวนปัญหา", "year_month": "เดือน"},
            hover_data=["date", "count", "year_month"],
        )

        fig.add_trace(
            px.line(
                daily_counts,
                x="date",
                y="count",
            ).data[0]
        )

        fig.update_traces(marker=dict(size=8, opacity=0.8))
        fig.update_layout(
            height=450,
            legend_title_text="เดือน",
            hovermode="x unified",
        )
        fig.update_xaxes(title="วันที่")
        fig.update_yaxes(title="จำนวนปัญหา")

        st.plotly_chart(fig, use_container_width=True)

    # -----------------------------
    # 5.2 SCATTER: TOTAL_SCORE vs COMPLAINTS
    # -----------------------------
    def show_score_vs_complaints(self) -> None:
        st.markdown("---")
        st.subheader("📌 Total Score vs Complaints ")

        gdf_filtered = self.view.filtered_by_type.copy()

        if "district" not in gdf_filtered.columns:
            st.error(
                "ไม่พบคอลัมน์ 'district' ใน cleansed_data.csv "
                "(ต้องมี district เพื่อรวมกับคะแนน)"
            )
            return

        complaints_by_district = (
            gdf_filtered.groupby("district").size().reset_index(name="complaints")
        )

        df_typeb = self.df_score.merge(complaints_by_district, on="district", how="left")
        df_typeb["complaints"] = df_typeb["complaints"].fillna(0)

        if df_typeb["complaints"].sum() == 0:
            st.info(
                "ไม่มีเรื่องร้องเรียนใด ๆ ในช่วงเวลา / ประเภทที่เลือก จึงยังวิเคราะห์ไม่ได้"
            )
            return

        # thresholds
        low_score_threshold = df_typeb["total_score"].quantile(0.3)
        high_complaints_threshold = df_typeb["complaints"].quantile(0.7)

        def label_type(row: pd.Series) -> str:
            if (
                row["total_score"] < low_score_threshold
                and row["complaints"] > high_complaints_threshold
            ):
                return "Danger Zone"
            elif (
                row["total_score"] >= low_score_threshold
                and row["complaints"] > high_complaints_threshold
            ):
                return "Active Zone"
            elif (
                row["total_score"] < low_score_threshold
                and row["complaints"] <= high_complaints_threshold
            ):
                return "Silent Risk Zone"
            else:
                return "Good Zone"

        df_typeb["zone"] = df_typeb.apply(label_type, axis=1)

        zone_order = [
            "Danger Zone",
            "Active Zone",
            "Silent Risk Zone",
            "Good Zone",
        ]
        color_map = {
            "Danger Zone": "red",
            "Active Zone": "#ff7f0e",
            "Silent Risk Zone": "#2ca02c",
            "Good Zone": "#1f77b4",
        }

        fig = px.scatter(
            df_typeb,
            x="total_score",
            y="complaints",
            color="zone",
            category_orders={"zone": zone_order},
            color_discrete_map=color_map,
            hover_data=["district", "total_score", "complaints", "zone"],
            labels={
                "total_score": "Total Score",
                "complaints": "Number of Complaints",
                "zone": "Zone",
            },
            title="Total Score vs Complaints by District",
        )

        fig.update_traces(
            marker=dict(size=15, opacity=0.9),
            selector=dict(mode="markers"),
        )
        fig.update_xaxes(range=[10, 40], title="Total Score")
        fig.update_yaxes(range=[0, 20000], title="Number of Complaints")

        fig.add_vline(
            x=float(low_score_threshold),
            line_dash="dash",
            line_color="black",
            annotation_text=" ",
            annotation_position="top left",
        )
        fig.add_hline(
            y=float(high_complaints_threshold),
            line_dash="dash",
            line_color="black",
            annotation_text=" ",
            annotation_position="top right",
        )

        fig.update_layout(
            height=600,
            legend_title_text="Zone",
            hovermode="closest",
        )

        st.plotly_chart(fig, use_container_width=True)

    # -----------------------------
    # 5.3 Scatter: District Quality vs Complaints (4 metrics)
    # -----------------------------
    def show_quality_vs_complaints_scatter(self) -> None:
        st.markdown("---")
        st.subheader("📌 Scatter Plot - จำนวนร้องเรียน เทียบกับมิติคุณภาพเขต")

        gdf_filtered = self.view.filtered_by_type.copy()

        if "district" not in gdf_filtered.columns:
            st.error("ไม่พบคอลัมน์ 'district'")
            return

        complaints_by_district = (
            gdf_filtered.groupby("district").size().reset_index(name="complaints")
        )

        df_scatter = self.df_score.merge(
            complaints_by_district, on="district", how="left"
        )
        df_scatter["complaints"] = df_scatter["complaints"].fillna(0)

        metrics = ["public_service", "economy", "welfare", "environment"]
        metric_titles = {
            "public_service": "Public Service",
            "economy": "Economy",
            "welfare": "Welfare",
            "environment": "Environment",
        }

        fig = make_subplots(
            rows=2,
            cols=2,
            subplot_titles=[metric_titles[m] for m in metrics],
        )

        for i, m in enumerate(metrics):
            row = i // 2 + 1
            col = i % 2 + 1

            fig.add_trace(
                go.Scatter(
                    x=df_scatter[m],
                    y=df_scatter["complaints"],
                    mode="markers",
                    marker=dict(
                        size=12,
                        opacity=0.7,
                        color=df_scatter["complaints"],
                        colorscale="RdYlBu",
                        reversescale=True,
                        showscale=True if i == 0 else False,
                        colorbar=dict(title="Complaints") if i == 0 else None,
                    ),
                    name=metric_titles[m],
                    text=df_scatter["district"],
                    hovertemplate=(
                        "เขต: %{text}<br>"
                        f"{metric_titles[m]}: " + "%{x}<br>"
                        "Complaints: %{y}<extra></extra>"
                    ),
                ),
                row=row,
                col=col,
            )

            fig.update_xaxes(title_text=metric_titles[m], row=row, col=col)

        y_label = (
            f"จำนวนร้องเรียนเรื่อง{self.filters.type_filter}"
            if self.filters.type_filter != "ทั้งหมด"
            else "จำนวนร้องเรียนเรื่องทั้งหมด"
        )
        fig.update_yaxes(title_text=y_label, matches="y")
        fig.update_layout(
            height=650,
            showlegend=False,
            margin=dict(l=40, r=20, t=60, b=40),
            title=dict(
                text="Scatter: มิติคุณภาพเขต vs จำนวนร้องเรียน",
                x=0.5,
            ),
        )

        st.plotly_chart(fig, use_container_width=True)

    # -----------------------------
    # 5.4 Pearson Heatmap: District Quality vs Problem Types
    # -----------------------------
    def show_metric_type_heatmap(self) -> None:
        st.markdown("---")
        st.subheader("🔥 Pearson Heatmap – ความสัมพันธ์ระหว่างมิติคุณภาพเขตกับประเภทปัญหา")

        corr_base = self.view.filtered_time.copy()
        corr_base = corr_base.dropna(subset=["type_clean"])
        corr_base = corr_base[corr_base["type_clean"].astype(str).str.strip() != ""]

        if corr_base.empty:
            st.info(
                "ไม่มีข้อมูลประเภทปัญหาหลังตัด NaN / ค่าว่าง ออก "
                "จึงยังทำ Pearson heatmap ไม่ได้"
            )
            return

        if "district" not in corr_base.columns:
            st.error(
                "ไม่พบคอลัมน์ 'district' ใน cleansed_data.csv "
                "(ต้องมี district เพื่อทำ heatmap)"
            )
            return

        type_district_counts = (
            corr_base.groupby(["district", "type_clean"])
            .size()
            .reset_index(name="complaints")
        )

        pivot_types = (
            type_district_counts.pivot(
                index="district", columns="type_clean", values="complaints"
            )
            .fillna(0)
            .reset_index()
        )

        corr_df = self.df_score.merge(pivot_types, on="district", how="left").fillna(0)

        metric_cols = ["total_score", "public_service", "economy", "welfare", "environment"]
        type_cols = [
            c for c in corr_df.columns if c not in metric_cols + ["district"]
        ]

        if not type_cols:
            st.info("ไม่มีคอลัมน์ประเภทปัญหาที่จะแปลงเป็นตัวเลขสำหรับทำ Pearson heatmap")
            return

        corr_matrix = corr_df[metric_cols + type_cols].corr(method="pearson")
        corr_sub = corr_matrix.loc[metric_cols, type_cols]

        corr_long = (
            corr_sub.reset_index()
            .melt(id_vars="index", var_name="problem_type", value_name="corr")
            .rename(columns={"index": "metric"})
        )

        heatmap = (
            alt.Chart(corr_long)
            .mark_rect()
            .encode(
                x=alt.X(
                    "problem_type:N",
                    title="ประเภทปัญหา",
                    sort=type_cols,
                ),
                y=alt.Y(
                    "metric:N",
                    title="มิติคุณภาพเขต",
                    sort=metric_cols,
                ),
                color=alt.Color(
                    "corr:Q",
                    title="Pearson r",
                    scale=alt.Scale(scheme="redblue", domain=[-1, 0, 1]),
                ),
                tooltip=[
                    "metric:N",
                    "problem_type:N",
                    alt.Tooltip("corr:Q", title="Pearson r", format=".2f"),
                ],
            )
            .properties(
                width=400,
                height=400,
                title="Pearson Correlation: District Quality Metrics × Problem Types",
            )
        )

        st.altair_chart(heatmap, use_container_width=True)

    # -----------------------------
    # 5.5 Pearson Heatmap: Problem Type vs Problem Type
    # -----------------------------
    def show_problem_problem_heatmap(self) -> None:
        st.markdown("---")
        st.subheader("🔥 Pearson Heatmap – ความสัมพันธ์ระหว่าง 'ประเภทปัญหา' ด้วยกันเอง")

        triangle_mode = st.sidebar.selectbox(
            "แสดง Heatmap ความสัมพันธ์ระหว่างประเภทปัญหาแบบ:",
            ["Full Matrix", "Upper Triangle", "Lower Triangle"],
            index=2,
            key="problem_corr_triangle_mode",
        )

        corr_problem = self.view.filtered_time.copy()
        corr_problem = corr_problem.dropna(subset=["type_clean"])
        corr_problem = corr_problem[
            corr_problem["type_clean"].astype(str).str.strip() != ""
        ]

        if corr_problem.empty:
            st.info(
                "ไม่มีข้อมูลประเภทปัญหาหลังตัด NaN / ค่าว่างออก "
                "จึงยังทำ Pearson heatmap (ปัญหากับปัญหา) ไม่ได้"
            )
            return

        if "district" not in corr_problem.columns:
            st.error(
                "ไม่พบคอลัมน์ 'district' ใน cleansed_data.csv "
                "(ต้องมี district เพื่อทำ heatmap ปัญหากับปัญหา)"
            )
            return

        type_district_counts = (
            corr_problem.groupby(["district", "type_clean"])
            .size()
            .reset_index(name="complaints")
        )

        pivot_problems = (
            type_district_counts.pivot(
                index="district", columns="type_clean", values="complaints"
            )
            .fillna(0)
        )

        if pivot_problems.shape[1] < 2:
            st.info("จำนวนประเภทปัญหาน้อยเกินไป (< 2) สำหรับทำ correlation ปัญหากับปัญหา")
            return

        corr_matrix_prob = pivot_problems.corr(method="pearson")
        corr_prob_long = (
            corr_matrix_prob.reset_index()
            .melt(id_vars="type_clean", var_name="problem_type_2", value_name="corr")
            .rename(columns={"type_clean": "problem_type_1"})
        )

        problem_list = list(corr_matrix_prob.index)
        index_map = {p: i for i, p in enumerate(problem_list)}

        corr_prob_long["i_idx"] = corr_prob_long["problem_type_1"].map(index_map)
        corr_prob_long["j_idx"] = corr_prob_long["problem_type_2"].map(index_map)

        if triangle_mode == "Upper Triangle":
            corr_filtered = corr_prob_long[
                corr_prob_long["i_idx"] < corr_prob_long["j_idx"]
            ]
            title_suffix = " (Upper Triangle)"
        elif triangle_mode == "Lower Triangle":
            corr_filtered = corr_prob_long[
                corr_prob_long["i_idx"] > corr_prob_long["j_idx"]
            ]
            title_suffix = " (Lower Triangle)"
        else:
            corr_filtered = corr_prob_long
            title_suffix = " (Full Matrix)"

        heatmap_prob = (
            alt.Chart(corr_filtered)
            .mark_rect()
            .encode(
                x=alt.X(
                    "problem_type_2:N",
                    title="ประเภทปัญหา (ตัวแปรที่ 2)",
                    sort=problem_list,
                ),
                y=alt.Y(
                    "problem_type_1:N",
                    title="ประเภทปัญหา (ตัวแปรที่ 1)",
                    sort=problem_list,
                ),
                color=alt.Color(
                    "corr:Q",
                    title="Pearson r",
                    scale=alt.Scale(scheme="redblue", domain=[-1, 0, 1]),
                ),
                tooltip=[
                    "problem_type_1:N",
                    "problem_type_2:N",
                    alt.Tooltip("corr:Q", title="Pearson r", format=".2f"),
                ],
            )
            .properties(
                width=40 * max(6, len(problem_list)),
                height=40 * max(6, len(problem_list)),
                title=f"Pearson Correlation: Problem Type × Problem Type{title_suffix}",
            )
        )

        st.altair_chart(heatmap_prob, use_container_width=True)

    # -----------------------------
    # 5.6 Scatter Matrix – Problem Counts per District
    # -----------------------------
    def show_scatter_matrix(self, df_cleansed: pd.DataFrame) -> None:
        st.markdown("---")
        st.subheader("📊 Scatter Matrix - เปรียบเทียบจำนวนปัญหาระหว่างประเภท (ต่อเขต)")

        f = self.filters

        # Filter by time (same logic as original for scatter matrix section)
        df_time = df_cleansed[
            (
                df_cleansed[["timestamp_year", "timestamp_month", "timestamp_date"]]
                .apply(tuple, axis=1)
                >= (f.start_date.year, f.start_date.month, f.start_date.day)
            )
            & (
                df_cleansed[["timestamp_year", "timestamp_month", "timestamp_date"]]
                .apply(tuple, axis=1)
                <= (f.end_date.year, f.end_date.month, f.end_date.day)
            )
        ].copy()

        # clean type_clean
        df_time = df_time.dropna(subset=["type_clean"])
        df_time = df_time[df_time["type_clean"].astype(str).str.strip() != ""]

        # problem options
        problem_options = sorted(df_time["type_clean"].unique())

        selected_types = st.multiselect(
            "เลือกประเภทปัญหา (2–5)",
            options=problem_options,
            default=(
                problem_options[:5] if len(problem_options) >= 5 else problem_options
            ),
            key="scatter_matrix_v3",
        )

        if len(selected_types) < 2:
            st.warning("กรุณาเลือกอย่างน้อย 2 ประเภท")
            return

        # (district, type_clean) counts
        df_counts = (
            df_time[df_time["type_clean"].isin(selected_types)]
            .groupby(["district", "type_clean"])
            .size()
            .reset_index(name="count")
        )

        if df_counts.empty:
            st.warning("ไม่มีข้อมูล")
            return

        # pivot to wide
        matrix_df = (
            df_counts.pivot_table(
                index="district",
                columns="type_clean",
                values="count",
                aggfunc="sum",
                fill_value=0,
            )
            .reset_index()
        )

        dim_cols = [t for t in selected_types if t in matrix_df.columns]

        if len(dim_cols) < 2:
            st.warning("Pivot แล้วได้ประเภทน้อยกว่า 2")
            return

        fig = px.scatter_matrix(
            matrix_df,
            dimensions=dim_cols,
            color="district",
            hover_data=["district"],
            title="Scatter Matrix - จำนวนปัญหาแต่ละประเภท (ต่อเขต)",
        )

        fig.update_traces(marker=dict(size=7, opacity=0.8))
        fig.update_xaxes(showline=True, linewidth=1, linecolor="black")
        fig.update_yaxes(showline=True, linewidth=1, linecolor="black")

        fig.update_layout(
            height=700,
            width=900,
            plot_bgcolor="#F8FAFC",
            paper_bgcolor="white",
            hovermode="closest",
        )

        st.plotly_chart(fig, use_container_width=True)


# -------------------------------------------------
# 6) MAIN APP WRAPPER
# -------------------------------------------------

class TraffyDashboardApp:
    """
    Main Streamlit application that wires:
      - data loader
      - filter panel
      - filtered view
      - chart renderer
    """

    def __init__(self) -> None:
        self.data_loader = TraffyDataLoader()
        self.default_start = datetime.date(2021, 9, 19)
        self.default_end = datetime.date(2025, 1, 16)

    def run(self) -> None:
        st.title("Bangkok Traffy - Scatter Viewer")

        # 1) Sidebar filters
        filter_panel = FilterPanel(
            type_list=self.data_loader.type_list,
            default_start=self.default_start,
            default_end=self.default_end,
        )
        filters = filter_panel.render()

        # 2) Filtered view
        view = TraffyView(self.data_loader.cleansed, filters)

        # 3) Charts
        charts = TraffyCharts(
            view=view,
            df_score=self.data_loader.scores,
            filters=filters,
        )

        charts.show_daily_counts()
        charts.show_score_vs_complaints()
        charts.show_quality_vs_complaints_scatter()
        charts.show_metric_type_heatmap()
        charts.show_problem_problem_heatmap()
        charts.show_scatter_matrix(self.data_loader.cleansed)


def main() -> None:
    app = TraffyDashboardApp()
    app.run()


if __name__ == "__main__":
    main()
