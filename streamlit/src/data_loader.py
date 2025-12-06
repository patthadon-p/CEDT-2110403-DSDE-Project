# src/data_loader.py

import datetime
import pandas as pd
import streamlit as st
import geopandas as gpd
from shapely import wkt

# Import necessary utility functions
from src.utils import read_config_path


# 1. DATA LOADER CLASS (Combined and Enhanced)
class TraffyDataLoader:
    
    default_start = datetime.date(2021, 9, 19)
    default_end = datetime.date(2025, 1, 16)
    
    @staticmethod
    @st.cache_data
    def load_cleansed() -> pd.DataFrame:
        path = read_config_path(domain="processed", key="cleansed_data_path")
        df = pd.read_csv(path)
        
        # Clean and split types
        df["type_cleaned"] = (
            df["type"].astype(str)
            .str.replace("{", "", regex=False)
            .str.replace("}", "", regex=False)
            .str.split(",").apply(tuple)
        )
        
        # 'type_clean' is the first type (for single type filtering)
        df["type_clean"] = df["type_cleaned"].apply(
            lambda x: x[0].strip() if isinstance(x, tuple) and len(x) > 0 else None
        )
        
        # Build datetime column for easy comparison
        df.rename(columns={
            "timestamp_year": "year",
            "timestamp_month": "month",
            "timestamp_date": "day"
        }, inplace=True)
        df["date"] = pd.to_datetime(df[["year", "month", "day"]])
        
        # Ensure numeric coordinates
        df["latitude"] = pd.to_numeric(df["latitude"], errors="coerce")
        df["longitude"] = pd.to_numeric(df["longitude"], errors="coerce")
        df = df.dropna(subset=["latitude", "longitude"])
        
        return df

    @staticmethod
    @st.cache_data
    def load_pop_data() -> dict[int, pd.DataFrame]:
        # Loads population data for 2022, 2023, 2024
        pop_data = {}
        for year, key in [(2022, "population_2565_scrapped_path"), 
                              (2023, "population_2566_scrapped_path"), 
                              (2024, "population_2567_scrapped_path")]:
            try:
                path = read_config_path(domain="scrapping", key=key)
                pop_data[year] = pd.read_csv(path)
            except Exception as e:
                st.error(f"Could not load population data for {year}: {e}")
                pop_data[year] = pd.DataFrame()
        return pop_data

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

# --- Data Loading Helpers for Time Predictor (From Second Block) ---

@st.cache_data(show_spinner=False)
def load_and_process_predictor_data():
    """Loads a minimal set of data for the Time Predictor's dropdowns."""
    path = read_config_path(domain="processed", key="cleansed_data_path")
    # Added 'timestamp_month', 'timestamp_year' to help the hash in prepare_features
    cols = ["district", "subdistrict", "type", "organization", "timestamp_month", "timestamp_year"]
    df = pd.read_csv(path, usecols=lambda c: c in cols)
    
    district_map = (
        df.dropna(subset=["district", "subdistrict"])
        .groupby("district")["subdistrict"]
        .apply(lambda x: sorted(list(set(x))))
        .to_dict()
    )
    
    def clean_explode(c):
        s = df[c].astype(str).str.replace(r"[{}]", "", regex=True).str.split(",").explode().str.strip()
        return sorted(s[s != ""].unique().tolist())

    return district_map, clean_explode("type"), clean_explode("organization")

@st.cache_data(show_spinner=False)
def load_geo_data():
    """Loads the GeoDataFrame for reverse geocoding/map highlighting."""
    try:
        path = read_config_path(domain="processed", key="cleansed_geographic_data_path") 
        df = pd.read_csv(path)
        df['geometry'] = df['geometry'].apply(wkt.loads)
        gdf = gpd.GeoDataFrame(df, geometry='geometry')
        gdf.set_crs(epsg=4326, inplace=True)
        return gdf
    except Exception as e: 
        st.warning(f"Failed to load geographic data for reverse geocoding: {e}")
        return None