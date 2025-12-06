# src/model_predictor.py

import numpy as np
import streamlit as st
from components.data_loader import load_and_process_predictor_data, load_geo_data
from components.utils import find_location_from_coords


# 3. MODEL LOGIC (Time Predictor - From Second Block)
class TraffyTimePredictor:
    """Mock-up predictor model logic."""

    def __init__(self):
        self.d_map, self.p_types, self.orgs = load_and_process_predictor_data()

    def _sparse_vec(self, size, idx):
        u = sorted(list(set(idx)))
        return f"({size}, {u}, {[1.0]*len(u)})"

    def prepare_features(self, district, subdistrict, types, orgs, date, lat, long):
        tm = int(date.month)
        ty = int(date.year)
        # Use pandas hash for consistency with the original code if run in the same environment
        dh = hash(district) % 2048
        sh = hash(subdistrict) % 2048
        ti = [self.p_types.index(t) for t in types if t in self.p_types]
        oi = [hash(o) % 1786 for o in orgs]

        return {
            "timestamp_month": tm,
            "timestamp_year": ty,
            "address_encoded": self._sparse_vec(2048, [dh, sh]),
            "latlong_encoded": [float(lat), float(long)],
            "organization_encoded": self._sparse_vec(1786, oi),
            "type_encoded": self._sparse_vec(25, ti),
        }

    def predict(self, model_input):
        base = 3.0
        # Mock logic: odd-indexed problem types (like 'ความสะอาด', 'PM2.5') increase base time
        try:
            # Extract the indices from the sparse vector string
            ts_str = model_input["type_encoded"].split("[")[1].split("]")[0]
            if ts_str:
                # Check if any index (before the comma, as a string) is odd-indexed.
                # This is a very rough mock and depends on the specific p_types list.
                # Simplified for demonstration purposes only.
                indices = [
                    int(x.strip())
                    for x in ts_str.split(",")
                    if x.strip() and x.strip().isdigit()
                ]
                if any(i % 2 != 0 for i in indices):
                    base += 5.0
        except:
            # Fallback if parsing fails
            pass

        # Add random variation to mock the prediction
        val = max(1, base + np.random.uniform(-1, 5))
        lvl = "Fast (เร็ว)" if val < 3 else "Normal (ปกติ)" if val < 10 else "Slow (ช้า)"
        return round(val, 1), lvl


# --- State Management & Callbacks (Time Predictor - From Second Block) ---


def handle_pending_updates():
    """Applies pending coordinate updates and runs reverse geocoding."""
    if "pending_coords" in st.session_state:
        lat = st.session_state.pending_coords["lat"]
        lng = st.session_state.pending_coords["lng"]
        src = st.session_state.pending_coords["source"]

        # 1. Update Coordinates
        st.session_state["confirmed_lat"] = lat
        st.session_state["confirmed_long"] = lng
        st.session_state["location_source"] = src

        # 2. Reverse Geocode (Fix: Explicitly set dropdown values)
        # Use the utility function with the required load_geo_data passed in
        d, s = find_location_from_coords(lat, lng, load_geo_data)
        if d and s:
            st.session_state["sb_district"] = d
            st.session_state["sb_subdistrict"] = s
            st.session_state["geo_match_found"] = True
        else:
            st.session_state["geo_match_found"] = False

        del st.session_state["pending_coords"]


def clear_coordinates():
    """Resets all coordinate-related session state."""
    st.session_state["confirmed_lat"] = None
    st.session_state["confirmed_long"] = None
    st.session_state["location_source"] = None
    st.session_state["geo_match_found"] = None
    # Reset Dropdowns to default
    st.session_state["sb_district"] = "--- Select District ---"
    st.session_state["sb_subdistrict"] = None
