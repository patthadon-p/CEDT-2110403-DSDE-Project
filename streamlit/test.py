import datetime
import streamlit as st
import pandas as pd
import sys, os
import geopandas as gpd
from streamlit_folium import st_folium

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.append(project_root)
from src.visualize.MapVisualizer import MapVisualizer

st.set_page_config(layout="wide")

st.title("Bangkok Traffy Heatmap Viewer")
st.sidebar.header("Filters")
st.markdown(
    """
    <style>
    section[data-testid="stSidebar"] .css-1d391kg {
        padding-bottom: 200px !important;  /* ⭐ prevents drop-up */
    }
    </style>
    """,
    unsafe_allow_html=True
)

# Load Cleansed Data
@st.cache_data
def load_data():
    df = pd.read_csv("./data/processed/cleansed_data.csv")
    df["type_cleaned"] = (
        df["type"]
        .astype(str)
        .str.replace("{", "")
        .str.replace("}", "")
        .str.split(",")
    )
    return df

df_cleansed = load_data()

# Load Type list
@st.cache_data
def get_type_list(df):
    return sorted({t.strip() for row in df["type_cleaned"] for t in row})

type_list = get_type_list(df_cleansed)

# Sidebar Filters
with st.sidebar.form("filter_form"):

    type_filter = st.selectbox(
        "เลือกประเภทปัญหา",
        options=["ทั้งหมด"] + type_list
    )

    start_date, end_date = st.date_input(
        "เลือกช่วงวัน",
        value=[
            datetime.date(2021, 9, 19),
            datetime.date(2025, 1, 16)
        ],
        min_value=datetime.date(2021, 9, 19),
        max_value=datetime.date(2025, 1, 16)
    )

    submit = st.form_submit_button("Apply Filter")

if submit:
    st.session_state["type_filter"] = type_filter
    st.session_state["start_date"] = start_date
    st.session_state["end_date"] = end_date

type_filter = st.session_state.get("type_filter", "ทั้งหมด")
start_date = st.session_state.get("start_date", datetime.date(2021, 9, 19))
end_date = st.session_state.get("end_date", datetime.date(2025, 1, 16))

filtered_time = df_cleansed[
    (df_cleansed[["timestamp_year", "timestamp_month", "timestamp_date"]]
        .apply(tuple, axis=1) >= (start_date.year, start_date.month, start_date.day))
    &
    (df_cleansed[["timestamp_year", "timestamp_month", "timestamp_date"]]
        .apply(tuple, axis=1) <= (end_date.year, end_date.month, end_date.day))
]

viz = MapVisualizer(filtered_time, region_path="./data/processed/cleansed_geo.csv")

if type_filter == "ทั้งหมด":
    gdf_filtered = viz.gdf_points
    m = viz.plot(type_filter=None)
    type_filter = ""
else:
    gdf_filtered = viz.gdf_points[viz.gdf_points["type_clean"] == type_filter]
    m = viz.plot(type_filter=type_filter)

joined = gpd.sjoin(
    gdf_filtered,
    viz.gdf_region,
    how="left",
    predicate="within"
)

top10_district = (
    joined.groupby("subdistrict_name")
    .size()
    .sort_values(ascending=False)
    .head(10)
    .reset_index(name="จำนวนปัญหา")
)

col1, col2 = st.columns([3, 1])

with col1:
    st_folium(m, width=800, height=500)

with col2:
    st.write(f"#### 10 อันดับเขตที่มีปัญหา {type_filter} มากที่สุด")
    st.dataframe(top10_district, width='stretch')
