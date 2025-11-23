import datetime
import os
import sys
import matplotlib.pyplot as plt

import altair as alt
import pandas as pd
import streamlit as st

# Add project root to Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.append(project_root)

# Utility Functions
from src.utils import read_config_path

# Streamlit page configuration
st.set_page_config(layout="wide")

st.title("Bangkok Traffy - Scatter Viewer")
st.sidebar.header("Filters")


# -----------------------------
# 1) LOAD DATA
# -----------------------------


@st.cache_data
def load_cleansed() -> pd.DataFrame:
    df = pd.read_csv(read_config_path(domain="processed", key="cleansed_data_path"))

    # list of categories
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
def load_scores() -> pd.DataFrame:
    # web-scraped score data (50 districts)
    return pd.read_csv(
        read_config_path(domain="scrapping", key="bangkok_index_scrapped_path")
    )


# Load cleansed data and scores
df_cleansed = load_cleansed()
df_score = load_scores()


# -----------------------------
# 2) SIDEBAR FILTERS
# -----------------------------

@st.cache_data
def get_type_list(df):
    clean_list = []
    for row in df["type_cleaned"]:
        for t in row:
            if pd.notna(t) and str(t).strip() != "":
                clean_list.append(t.strip())
    return sorted(set(clean_list))

type_list = get_type_list(df_cleansed)

with st.sidebar.form("filter_form"):
    type_filter = st.selectbox("เลือกประเภทปัญหา", options=["ทั้งหมด"] + type_list)

    date_range = st.date_input(
        "เลือกช่วงวัน",
        value=[datetime.date(2021, 9, 19), datetime.date(2025, 1, 16)],
        min_value=datetime.date(2021, 9, 19),
        max_value=datetime.date(2025, 1, 16),
    )

    if isinstance(date_range, tuple) and len(date_range) == 2:
        start_date, end_date = date_range
    else:
        # Default values if user hasn't selected a proper range
        start_date = datetime.date(2021, 9, 19)
        end_date = datetime.date(2025, 1, 16)

    submit = st.form_submit_button("Apply Filter")

if submit:
    st.session_state["type_filter"] = type_filter
    st.session_state["start_date"] = start_date
    st.session_state["end_date"] = end_date

type_filter = st.session_state.get("type_filter", "ทั้งหมด")
start_date = st.session_state.get("start_date", datetime.date(2021, 9, 19))
end_date = st.session_state.get("end_date", datetime.date(2025, 1, 16))


# -----------------------------
# 3) FILTER TRAFFY DATA
# -----------------------------

# filter by time
filtered_time = df_cleansed[
    (
        df_cleansed[["timestamp_year", "timestamp_month", "timestamp_date"]].apply(
            tuple, axis=1
        )
        >= (start_date.year, start_date.month, start_date.day)
    )
    & (
        df_cleansed[["timestamp_year", "timestamp_month", "timestamp_date"]].apply(
            tuple, axis=1
        )
        <= (end_date.year, end_date.month, end_date.day)
    )
]

# filter by type
if type_filter != "ทั้งหมด":
    gdf_filtered = filtered_time[filtered_time["type_clean"] == type_filter]
else:
    gdf_filtered = filtered_time
    type_filter = ""
