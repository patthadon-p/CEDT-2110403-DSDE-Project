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

@st.cache_data
def get_type_list(df):
    return sorted({t.strip() for row in df["type_cleaned"] for t in row})

type_list = get_type_list(df_cleansed)

type_filter = st.sidebar.selectbox(
    "เลือกประเภทปัญหา",
    options=["(all)"] + type_list
)

viz = MapVisualizer(df_cleansed, region_path="./data/processed/cleansed_geo.csv")

if type_filter == "(all)":
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
    st_folium(m, width=900, height=600)

with col2:
    st.write(f"### 10 อันดับเขตที่มีปัญหา {type_filter} มากที่สุด")
    st.dataframe(top10_district, use_container_width=True)
