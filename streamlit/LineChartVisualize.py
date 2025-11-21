import datetime
import streamlit as st
import pandas as pd
import sys, os

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.append(project_root)

from src.visualize.LineChartVisualizer import LineChartVisualizer   

st.set_page_config(layout="wide")

st.title("Bangkok Traffy Line Chart Viewer")
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

viz = LineChartVisualizer(df_cleansed)
fig = viz.plot()
st.pyplot(fig)
