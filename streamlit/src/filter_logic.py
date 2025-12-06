# src/filter_logic.py

import datetime
import pandas as pd
import streamlit as st
from src.data_loader import TraffyDataLoader

# 2. FILTER & LOGIC CLASS (Centralized)
class TraffyFilter:
    
    def __init__(self, df: pd.DataFrame):
        self.df = df
        self.type_list = TraffyDataLoader.get_unique_types(df)
        self.default_start = TraffyDataLoader.default_start
        self.default_end = TraffyDataLoader.default_end

    def render_sidebar(self):
        st.sidebar.title("🛠️ Navigation & Filters")
        
        # --- Navigation ---
        page_options = {
            "Spatial Analysis": "Map",
            "Scatter Analysis": "Scatter",
            "Line Chart": "Line",
            "Time Predictor": "Predictor" # <--- ADDED PAGE
        }
        selected_page = st.sidebar.radio(
            "Select View", 
            list(page_options.keys())
        )
        st.sidebar.markdown("---")
        
        # Filter settings are only necessary for the first three pages
        if selected_page != "Time Predictor":
            st.sidebar.header("Filter Settings")

            # --- Filter Form ---
            with st.sidebar.form("filter_form"):
                selected_type = st.selectbox("เลือกประเภทปัญหา", options=["ทั้งหมด"] + self.type_list)
                date_range = st.date_input(
                    "เลือกช่วงวัน",
                    value=[self.default_start, self.default_end],
                    min_value=self.default_start,
                    max_value=self.default_end,
                )
                
                # Normalize date range
                if isinstance(date_range, tuple) and len(date_range) == 2:
                    start_date, end_date = date_range
                else:
                    start_date = end_date = date_range[0]
                    
                submit = st.form_submit_button("Apply Filter")

            # Store filter values in session state
            if submit or "type_filter" not in st.session_state:
                st.session_state["type_filter"] = selected_type
                st.session_state["start_date"] = start_date
                st.session_state["end_date"] = end_date

            self.current_type = st.session_state.get("type_filter", "ทั้งหมด")
            self.current_start = st.session_state.get("start_date", self.default_start)
            self.current_end = st.session_state.get("end_date", self.default_end)
        else:
            # Predictor page doesn't need data filtering here
            self.current_type = "ทั้งหมด"
            self.current_start = self.default_start
            self.current_end = self.default_end
            start_date = self.default_start
            end_date = self.default_end
            
        return page_options[selected_page], self.current_type, self.current_start, self.current_end

    def apply_filters(self, filter_type: bool = True, filter_date: bool = True) -> pd.DataFrame:
        df_filtered = self.df.copy()
        
        if filter_date:
            start_ts = pd.Timestamp(self.current_start)
            end_ts = pd.Timestamp(self.current_end)
            
            # Apply date mask
            date_mask = (df_filtered["date"] >= start_ts) & (df_filtered["date"] <= end_ts)
            df_filtered = df_filtered[date_mask]
        
        if filter_type and self.current_type != "ทั้งหมด":
            # Apply type mask (using the list of types)
            type_mask = df_filtered["type_cleaned"].apply(lambda x: self.current_type in x)
            df_filtered = df_filtered[type_mask]

        return df_filtered