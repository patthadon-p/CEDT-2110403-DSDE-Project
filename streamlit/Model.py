import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import datetime
import sys
import os

# --- Import Utility ---
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.append(project_root)

from src.utils import read_config_path

# -----------------------------------------------------------------------------
# 1. DATA LOADER (Cached & Optimized)
# -----------------------------------------------------------------------------
@st.cache_data(show_spinner=False)
def load_and_process_data():
    """
    Loads District, Subdistricts, Types, and Organizations from the processed data.
    Uses vectorized string operations for speed.
    """
    # 1. Load Data
    path = read_config_path(domain="processed", key="cleansed_data_path")
    cols_needed = ["district", "subdistrict", "type", "organization"]
    df = pd.read_csv(path, usecols=lambda c: c in cols_needed)
    
    # 2. Process District Map
    district_map = (
        df.dropna(subset=["district", "subdistrict"])
        .groupby("district")["subdistrict"]
        .apply(lambda x: sorted(list(set(x))))
        .to_dict()
    )
    
    # 3. Process Types (Vectorized Split & Explode)
    unique_types = (
        df["type"].astype(str)
        .str.replace(r"[{}]", "", regex=True)
        .str.split(",")
        .explode()
        .str.strip()
    )
    problem_types = sorted(unique_types[unique_types != ""].unique().tolist())

    # 4. Process Organizations
    unique_orgs = (
        df["organization"].astype(str)
        .str.replace(r"[{}]", "", regex=True)
        .str.split(",")
        .explode()
        .str.strip()
    )
    organizations = sorted(unique_orgs[unique_orgs != ""].unique().tolist())
    
    return district_map, problem_types, organizations

# -----------------------------------------------------------------------------
# 2. MODEL LOGIC CLASS
# -----------------------------------------------------------------------------
class TraffyTimePredictor:
    def __init__(self):
        # Load all data components
        self.district_map, self.problem_types, self.organizations = load_and_process_data()

    def _create_sparse_vector_string(self, size, indices):
        """Helper to format list of indices into Spark SparseVector string format"""
        # Sort and remove duplicates
        unique_indices = sorted(list(set(indices)))
        # Create values list (1.0 for each active index)
        values = [1.0] * len(unique_indices)
        return f"({size}, {unique_indices}, {values})"

    def prepare_features(self, district, subdistrict, problem_types_list, organization_list, report_date, lat, long):
        """
        Transforms raw inputs into the specific model schema.
        Handles MULTIPLE selections for Types and Organizations.
        """
        # 1. Time Features
        ts_month = int(report_date.month)
        ts_year = int(report_date.year)
        
        # 2. Address Vector (District + Subdistrict)
        # Simulation: Hash inputs
        d_hash = hash(district) % 2048
        s_hash = hash(subdistrict) % 2048
        address_vec = self._create_sparse_vector_string(2048, [d_hash, s_hash])
        
        # 3. Type Vector (Handle Multiple)
        type_indices = []
        for t in problem_types_list:
            try:
                idx = self.problem_types.index(t)
                type_indices.append(idx)
            except:
                pass # Skip unknown types
        
        # Create Sparse Vector string (Size 25 is arbitrary based on previous examples)
        type_vec = self._create_sparse_vector_string(25, type_indices)
        
        # 4. Organization Vector (Handle Multiple)
        org_indices = []
        for org in organization_list:
            # Simulation: using hash to get a consistent index within 1786 size
            idx = hash(org) % 1786
            org_indices.append(idx)
            
        org_vec = self._create_sparse_vector_string(1786, org_indices)
        
        # 5. LatLong Vector
        latlong_vec = [float(lat), float(long)]

        # Return Dictionary matching the Model Schema
        return {
            "timestamp_month": ts_month,
            "timestamp_year": ts_year,
            "address_encoded": address_vec,
            "latlong_encoded": latlong_vec,
            "organization_encoded": org_vec,
            "type_encoded": type_vec
        }

    def predict(self, model_input):
        """
        Simulates the model inference (GBTRegressor).
        """
        # Mock Logic
        base_days = 3.0
        
        # Extract indices string to check for specific types (Mocking logic)
        # format: "(25, [1, 2], [1.0, 1.0])"
        try:
            type_str = model_input["type_encoded"]
            # Extract the middle part: [1, 2]
            indices_part = type_str.split('[')[1].split(']')[0]
            indices = [int(x.strip()) for x in indices_part.split(',') if x.strip()]
            
            # Logic: If ANY selected type is "slow" (simulated by odd index), add time
            for idx in indices:
                if idx % 2 != 0:
                    base_days += 5.0
                    break # Add penalty once
        except:
            pass
            
        import random
        variance = random.uniform(-1, 5)
        final_prediction = max(1, base_days + variance)
        
        if final_prediction < 3: level = "Fast (เร็ว)"
        elif final_prediction < 10: level = "Normal (ปกติ)"
        else: level = "Slow (ช้า)"
            
        return round(final_prediction, 1), level

# -----------------------------------------------------------------------------
# 3. PAGE RENDERER (UI)
# -----------------------------------------------------------------------------
def render_prediction_page():
    st.title("🔮 AI Resolution Time Predictor")
    st.markdown("ระบบพยากรณ์ระยะเวลาแก้ไขปัญหา (Data Driven Parameters)")
    
    # Initialize Class
    try:
        predictor = TraffyTimePredictor()
    except Exception as e:
        st.error(f"Failed to initialize predictor: {e}")
        return

    # --- SIDEBAR: INPUT PARAMETERS ---
    st.sidebar.header("🛠️ Input Parameters")
    
    # 1. TIME
    st.sidebar.subheader("1. Time Factors")
    report_date = st.sidebar.date_input("Date (วันที่)", datetime.date.today())
    
    # 2. LOCATION
    st.sidebar.subheader("2. Location Data")
    
    # District
    all_districts = sorted(list(predictor.district_map.keys()))
    district_options = ["--- กรุณาเลือกเขต ---"] + all_districts
    selected_district = st.sidebar.selectbox("District (เขต)", district_options)
    
    # Subdistrict
    if selected_district == "--- กรุณาเลือกเขต ---":
        selected_subdistrict = st.sidebar.selectbox(
            "Subdistrict (แขวง)", 
            ["(รอการเลือกเขต)"], 
            disabled=True
        )
        is_ready = False
    else:
        sub_options = sorted(predictor.district_map[selected_district])
        selected_subdistrict = st.sidebar.selectbox("Subdistrict (แขวง)", sub_options)
        is_ready = True

    # Coordinates
    st.sidebar.markdown("##### Coordinates (พิกัด)")
    c1, c2 = st.sidebar.columns(2)
    lat = c1.number_input(
        "Latitude", min_value=-90.0, max_value=90.0, value=None, 
        format="%.6f", placeholder="13.xxxx"
    )
    long = c2.number_input(
        "Longitude", min_value=-180.0, max_value=180.0, value=None, 
        format="%.6f", placeholder="100.xxxx"
    )

    # 3. ORGANIZATION (Multi-Select)
    st.sidebar.subheader("3. Responsible Org")
    selected_orgs = st.sidebar.multiselect(
        "Organization (เลือกได้มากกว่า 1)", 
        predictor.organizations,
        placeholder="Select organizations..."
    )

    # 4. TYPE (Multi-Select)
    st.sidebar.subheader("4. Problem Type")
    selected_types = st.sidebar.multiselect(
        "Type (เลือกได้มากกว่า 1)", 
        predictor.problem_types,
        placeholder="Select problem types..."
    )
    
    st.sidebar.markdown("---")
    
    # Run Button
    run_btn = st.sidebar.button("🚀 Compute Prediction", type="primary")

    # --- MAIN CONTENT ---
    if run_btn:
        # Validation Logic
        if not is_ready:
            st.warning("⚠️ กรุณาเลือก **เขต (District)** ให้เรียบร้อยก่อน")
        elif lat is None or long is None:
            st.warning("⚠️ กรุณาระบุ **พิกัด (Latitude และ Longitude)** ให้ครบถ้วน")
        elif not selected_orgs:
            st.warning("⚠️ กรุณาเลือก **หน่วยงาน (Organization)** อย่างน้อย 1 หน่วยงาน")
        elif not selected_types:
            st.warning("⚠️ กรุณาเลือก **ประเภทปัญหา (Type)** อย่างน้อย 1 ประเภท")
        else:
            # A. Prepare Data
            features = predictor.prepare_features(
                selected_district, selected_subdistrict, selected_types, selected_orgs, report_date, lat, long
            )
            
            # B. Run Prediction
            with st.spinner(f"Analyzing..."):
                days, level = predictor.predict(features)

            # C. Display Results
            col1, col2 = st.columns([1.3, 1])
            
            with col1:
                st.subheader("📊 Prediction Result")
                st.metric("Estimated Resolution Time", f"{days} Days", delta=level, delta_color="inverse")
                
                # Gauge Chart
                fig = go.Figure(go.Indicator(
                    mode = "gauge+number",
                    value = days,
                    domain = {'x': [0, 1], 'y': [0, 1]},
                    title = {'text': "Days to Fix", 'font': {'size': 20}},
                    gauge = {
                        'axis': {'range': [None, 30]},
                        'bar': {'color': "#1f77b4"},
                        'steps': [
                            {'range': [0, 3], 'color': "#2ca02c"},
                            {'range': [3, 10], 'color': "#ff7f0e"},
                            {'range': [10, 30], 'color': "#d62728"}
                        ],
                        'threshold': {'line': {'color': "black", 'width': 4}, 'thickness': 0.75, 'value': days}
                    }
                ))
                fig.update_layout(height=300, margin=dict(l=20, r=20, t=40, b=20))
                st.plotly_chart(fig, use_container_width=True)

            with col2:
                st.subheader("🤖 Model Input Schema")
                st.caption("Data compiled for Model Call:")
                st.code(f"""
{{
  "timestamp_month": {features['timestamp_month']},
  "timestamp_year": {features['timestamp_year']},
  "address_encoded": "{features['address_encoded']}",
  "latlong_encoded": {features['latlong_encoded']},
  "organization_encoded": "{features['organization_encoded']}",
  "type_encoded": "{features['type_encoded']}"
}}
                """, language="json")

    elif not run_btn and (not is_ready or lat is None or long is None):
        st.info("👈 กรุณากรอกข้อมูลใน Sidebar ทางซ้ายให้ครบถ้วน")

if __name__ == "__main__":
    st.set_page_config(layout="wide", page_title="AI Time Predictor")
    render_prediction_page()