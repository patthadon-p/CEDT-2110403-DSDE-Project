# Import necessary libraries
import datetime

import pandas as pd
import pydeck as pdk
import streamlit as st

# Utility Functions
from src.utils import read_config_path

# Set up Streamlit page configuration
st.set_page_config(layout="wide")
st.title("Bangkok Traffy Scattermap Viewer")
st.sidebar.header("Filters")
st.markdown(
    """
    <style>
    section[data-testid="stSidebar"] .css-1d391kg {
        padding-bottom: 200px !important;  /* prevents drop-up */
    }
    </style>
    """,
    unsafe_allow_html=True,
)


@st.cache_data
def load_data() -> pd.DataFrame:
    df = pd.read_csv(read_config_path("processed", "cleansed_data_path"))
    df["type_cleaned"] = (
        df["type"].astype(str).str.replace("{", "").str.replace("}", "").str.split(",")
    )
    return df


df_cleansed = load_data()


@st.cache_data
def get_type_list(df: pd.DataFrame) -> list[str]:
    return sorted({t.strip() for row in df["type_cleaned"] for t in row})


type_list = get_type_list(df_cleansed)


with st.sidebar.form("filter_form"):
    type_filter = st.selectbox(
        "เลือกประเภทปัญหา", options=type_list, index=type_list.index("น้ำท่วม")
    )

    date_range = st.date_input(
        "เลือกช่วงวัน",
        value=[datetime.date(2021, 9, 19), datetime.date(2025, 1, 16)],
        min_value=datetime.date(2021, 9, 19),
        max_value=datetime.date(2025, 1, 16),
    )

    if len(date_range) == 2:
        start_date, end_date = date_range
    else:
        start_date = end_date = (
            date_range[0] if len(date_range) == 1 else datetime.date(2021, 9, 19)
        )

    submit = st.form_submit_button("Apply Filter")


if submit:
    st.session_state["type_filter"] = type_filter
    st.session_state["start_date"] = start_date
    st.session_state["end_date"] = end_date

type_filter = st.session_state.get("type_filter", "น้ำท่วม")
start_date = st.session_state.get("start_date", datetime.date(2021, 9, 19))
end_date = st.session_state.get("end_date", datetime.date(2025, 1, 16))


filtered_df = df_cleansed[
    df_cleansed["type_cleaned"].apply(lambda x: type_filter in x)
    & (
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


filtered_df["latitude"] = pd.to_numeric(filtered_df["latitude"], errors="coerce")
filtered_df["longitude"] = pd.to_numeric(filtered_df["longitude"], errors="coerce")
filtered_df = filtered_df.dropna(subset=["latitude", "longitude"])


top10_district = (
    filtered_df.groupby("subdistrict")
    .size()
    .sort_values(ascending=False)
    .head(10)
    .reset_index(name="จำนวนปัญหา")
)

col1, col2 = st.columns([3, 1])

with col1:
    layer = pdk.Layer(
        "ScatterplotLayer",
        filtered_df,
        get_position=["longitude", "latitude"],
        get_radius=100,
        get_fill_color=[255, 0, 0],
        pickable=True,
        opacity=0.5,
    )

    view_state = pdk.ViewState(
        latitude=filtered_df["latitude"].mean(),
        longitude=filtered_df["longitude"].mean(),
        zoom=10,
        pitch=0,
    )

    deck = pdk.Deck(
        layers=[layer],
        initial_view_state=view_state,
        tooltip={
            "text": "{subdistrict} {district}\n{timestamp_date}/{timestamp_month}/{timestamp_year}\n{comment}"
        },
    )

    st.pydeck_chart(deck)


with col2:
    st.write(f"#### 10 อันดับแขวงที่มีปัญหา {type_filter} มากที่สุด")
    st.dataframe(top10_district, width="stretch")
