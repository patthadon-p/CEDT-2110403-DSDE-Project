# Import necessary libraries
import pandas as pd
import streamlit as st

# Utility Functions
from src.utils import read_config_path

# Visualization Class
from src.visualize.LineChartVisualizer import LineChartVisualizer

# Set up Streamlit page configuration
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
    unsafe_allow_html=True,
)


# Load Cleansed Data
@st.cache_data
def load_data() -> pd.DataFrame:
    df = pd.read_csv(read_config_path("processed", "cleansed_data_path"))
    df["type_cleaned"] = (
        df["type"].astype(str).str.replace("{", "").str.replace("}", "").str.split(",")
    )
    return df


df_cleansed = load_data()

viz = LineChartVisualizer(df_cleansed)
fig = viz.plot()
st.pyplot(fig)
