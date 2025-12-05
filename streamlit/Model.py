import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import datetime
import sys
import os
import folium
from streamlit_folium import st_folium
import geopandas as gpd
from shapely import wkt
from shapely.geometry import Point
from streamlit_js_eval import get_geolocation

# --- Import Utility ---
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.append(project_root)

from src.utils import read_config_path

# -----------------------------------------------------------------------------
# 0. HELPER
# -----------------------------------------------------------------------------
def add_margin(t=0, r=0, b=0, l=0):
    st.markdown(f"<div style='margin:{t}px {r}px {b}px {l}px'></div>", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 1. DATA LOADER
# -----------------------------------------------------------------------------
@st.cache_data(show_spinner=False)
def load_and_process_data():
    path = read_config_path(domain="processed", key="cleansed_data_path")
    cols = ["district", "subdistrict", "type", "organization"]
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
    try:
        path = read_config_path(domain="processed", key="cleansed_geographic_data_path") 
        df = pd.read_csv(path)
        df['geometry'] = df['geometry'].apply(wkt.loads)
        gdf = gpd.GeoDataFrame(df, geometry='geometry')
        gdf.set_crs(epsg=4326, inplace=True)
        return gdf
    except: return None

def find_location_from_coords(lat, lng):
    gdf = load_geo_data()
    if gdf is None: return None, None
    point = Point(lng, lat)
    match = gdf[gdf.geometry.contains(point)]
    if not match.empty:
        return match.iloc[0]['district_name'], match.iloc[0]['subdistrict_name']
    return None, None

# -----------------------------------------------------------------------------
# 2. STATE MANAGEMENT & CALLBACKS
# -----------------------------------------------------------------------------
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
        d, s = find_location_from_coords(lat, lng)
        if d and s:
            st.session_state["sb_district"] = d
            st.session_state["sb_subdistrict"] = s
            st.session_state["geo_match_found"] = True
        else:
            st.session_state["geo_match_found"] = False
            # Optional: Clear dropdowns if no match found? 
            # st.session_state["sb_district"] = None 
        
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
    # No need to rerun explicitly if used in on_click

# -----------------------------------------------------------------------------
# 3. MODEL LOGIC
# -----------------------------------------------------------------------------
class TraffyTimePredictor:
    def __init__(self):
        self.d_map, self.p_types, self.orgs = load_and_process_data()

    def _sparse_vec(self, size, idx):
        u = sorted(list(set(idx)))
        return f"({size}, {u}, {[1.0]*len(u)})"

    def prepare_features(self, district, subdistrict, types, orgs, date, lat, long):
        tm = int(date.month); ty = int(date.year)
        dh = hash(district)%2048; sh = hash(subdistrict)%2048
        ti = [self.p_types.index(t) for t in types if t in self.p_types]
        oi = [hash(o)%1786 for o in orgs]
        
        return {
            "timestamp_month": tm, "timestamp_year": ty,
            "address_encoded": self._sparse_vec(2048, [dh, sh]),
            "latlong_encoded": [float(lat), float(long)],
            "organization_encoded": self._sparse_vec(1786, oi),
            "type_encoded": self._sparse_vec(25, ti)
        }

    def predict(self, model_input):
        base = 3.0
        try:
            ts = model_input["type_encoded"].split('[')[1].split(']')[0]
            if ts: 
                if any(int(x)%2!=0 for x in ts.split(',') if x.strip()): base += 5.0
        except: pass
        val = max(1, base + np.random.uniform(-1, 5))
        lvl = "Fast (เร็ว)" if val < 3 else "Normal (ปกติ)" if val < 10 else "Slow (ช้า)"
        return round(val, 1), lvl

# -----------------------------------------------------------------------------
# 4. UI RENDERER
# -----------------------------------------------------------------------------
def render_input_section(predictor):
    handle_pending_updates()
    
    if "confirmed_lat" not in st.session_state:
        st.session_state.update({"confirmed_lat": None, "confirmed_long": None, "location_source": None, "geo_match_found": None})

    # --- 1. GENERAL INFORMATION ---
    # --- 1. GENERAL INFORMATION ---
    st.subheader("1. Date selection") # (หรือ General Information ตามโค้ดล่าสุด)
    c1, _ = st.columns([1, 1]) # หรือ [1, 2] ตาม layout ที่คุณชอบ
    with c1:
        report_date = st.date_input(
            "Report Date", 
            value=datetime.date.today(),
            max_value=datetime.date.today()  # <--- เพิ่มตรงนี้เพื่อบล็อกวันอนาคต
        )
    
    add_margin(t=20); st.markdown("---")

    # --- 2. EXACT LOCATION ---
    st.subheader("2. Exact Location & Area")
    
    # Toggle Input Method
    input_mode = st.radio("Input Method:", ["📍 Use Current Location (GPS)", "🗺️ Select on Map / Manual"], horizontal=True, label_visibility="collapsed")
    add_margin(t=10)

    col_map, col_info = st.columns([1, 1], gap="large")

    # Values for Zoom/Highlight logic
    current_district_val = None
    current_subdistrict_val = None

    # --- RIGHT COLUMN: INFO & DROPDOWNS (Logic Priority) ---
    # We define logic here but render order is preserved by columns
    with col_info:
        if input_mode == "🗺️ Select on Map / Manual":
            st.markdown("##### Identified Area")
            st.caption("Select manually or click map to auto-fill.")
            
            d_opts = ["--- Select District ---"] + sorted(list(predictor.d_map.keys()))
            
            # District Dropdown
            # Check session state for value (populated by reverse geocode)
            sb_d_val = st.session_state.get("sb_district", "--- Select District ---")
            d_idx = d_opts.index(sb_d_val) if sb_d_val in d_opts else 0
            
            sel_d = st.selectbox("District", d_opts, index=d_idx, key="sb_district_widget")
            
            # Sync: Widget -> State
            if sel_d != st.session_state.get("sb_district"):
                st.session_state["sb_district"] = sel_d
                st.session_state["sb_subdistrict"] = None 
                st.rerun()

            # Subdistrict Dropdown
            if sel_d == "--- Select District ---":
                st.selectbox("Subdistrict", ["(Select District first)"], disabled=True)
                sel_s = None
            else:
                s_opts = sorted(predictor.d_map[sel_d])
                sb_s_val = st.session_state.get("sb_subdistrict")
                s_idx = s_opts.index(sb_s_val) if sb_s_val in s_opts else 0
                
                sel_s = st.selectbox("Subdistrict", s_opts, index=s_idx, key="sb_subdistrict_widget")
                
                if sel_s != st.session_state.get("sb_subdistrict"):
                    st.session_state["sb_subdistrict"] = sel_s
                    st.rerun()

            current_district_val = sel_d
            current_subdistrict_val = sel_s

        else:
            # GPS Mode: Hide Dropdowns
            st.markdown("##### Identified Area (GPS)")
            if st.session_state.get("location_source") == "Current GPS" and st.session_state.get("geo_match_found"):
                d = st.session_state.get("sb_district")
                s = st.session_state.get("sb_subdistrict")
                st.info(f"📍 **{d}** > **{s}**")
                current_district_val = d
                current_subdistrict_val = s
            else:
                st.info("Waiting for location...")
            
        add_margin(t=10)
        st.markdown("##### Coordinates")
        
        if st.session_state["confirmed_lat"]:
            c_coord, c_clear = st.columns([3, 1])
            with c_coord:
                st.success(f"**{st.session_state['confirmed_lat']:.6f}, {st.session_state['confirmed_long']:.6f}**", icon="✅")
            with c_clear:
                # Clear Button
                st.button("🗑️ Clear", on_click=clear_coordinates, use_container_width=True, help="Reset coordinates")
        else:
            st.warning("No coordinates confirmed yet.", icon="⏳")

    # --- LEFT COLUMN: MAP ---
    with col_map:
        if input_mode == "🗺️ Select on Map / Manual":
            st.markdown("**📍 Point Selection**")
            st.caption("Click map then 'Confirm Pin'.")
            
            gdf = load_geo_data()
            center = [13.7563, 100.5018]; zoom = 11
            target_geo = None

            # Zoom Logic
            if st.session_state["confirmed_lat"]:
                center = [st.session_state["confirmed_lat"], st.session_state["confirmed_long"]]
                zoom = 15
            elif gdf is not None and current_district_val and current_district_val != "--- Select District ---":
                try:
                    t = gdf[gdf['district_name'] == current_district_val]
                    if current_subdistrict_val:
                        sub_t = t[t['subdistrict_name'] == current_subdistrict_val]
                        if not sub_t.empty: t = sub_t; zoom = 14
                        else: zoom = 12
                    
                    if not t.empty:
                        c = t.geometry.centroid.iloc[0]
                        center = [c.y, c.x]
                        target_geo = t
                except: pass

            m = folium.Map(location=center, zoom_start=zoom)
            
            if target_geo is not None:
                folium.GeoJson(target_geo, style_function=lambda x: {'fillColor': '#ffaf00', 'color': 'red', 'weight': 2, 'fillOpacity': 0.1}).add_to(m)
            
            if st.session_state["confirmed_lat"]:
                folium.Marker([st.session_state["confirmed_lat"], st.session_state["confirmed_long"]], icon=folium.Icon(color="green", icon="check")).add_to(m)

            m.add_child(folium.LatLngPopup())
            
            # Key forces update on dropdown change
            map_key = f"map_{current_district_val}_{current_subdistrict_val}_{st.session_state['confirmed_lat']}"
            map_data = st_folium(m, height=380, width=None, key=map_key, returned_objects=["last_clicked"])

            if map_data and map_data.get("last_clicked"):
                if st.button("✅ Confirm Pin", use_container_width=True):
                    st.session_state["pending_coords"] = {
                        "lat": map_data["last_clicked"]["lat"],
                        "lng": map_data["last_clicked"]["lng"],
                        "source": "Map Selection"
                    }
                    st.rerun()
        else:
            # GPS Mode
            st.markdown("**📍 GPS Selection**")
            st.info("Click below to use browser location.")
            add_margin(t=10)
            geo_data = get_geolocation()
            
            if st.button("📡 Get My Location & Auto-Fill", use_container_width=True):
                if geo_data:
                    st.session_state["pending_coords"] = {
                        "lat": geo_data['coords']['latitude'],
                        "lng": geo_data['coords']['longitude'],
                        "source": "Current GPS"
                    }
                    st.rerun()
                else:
                    st.warning("Waiting for data... Click again.")
            
            add_margin(b=80)

    add_margin(t=20); st.markdown("---")

    # --- 3. DETAILS ---
    st.subheader("3. Agencies & Issues")
    c1, c2 = st.columns(2)
    with c1: orgs = st.multiselect("Responsible Organization", predictor.orgs)
    with c2: types = st.multiselect("Problem Type", predictor.p_types)
    
    add_margin(t=30)
    if st.button("🚀 Compute Prediction", type="primary", use_container_width=True):
        if not current_district_val or current_district_val == "--- Select District ---":
            st.error("⚠️ Select District"); return
        if not st.session_state["confirmed_lat"]:
            st.error("⚠️ Confirm Location"); return
        if not orgs or not types:
            st.error("⚠️ Fill Details"); return
            
        features = predictor.prepare_features(
            current_district_val, current_subdistrict_val, types, orgs,
            report_date, st.session_state["confirmed_lat"], st.session_state["confirmed_long"]
        )
        with st.spinner("Predicting..."):
            d, l = predictor.predict(features)
        display_results(d, l, features)

def display_results(days, level, features):
    add_margin(t=30)
    st.markdown("---")
    st.markdown("### 📊 Analysis Report")
    
    col_card1, col_card2 = st.columns(2)
    def card(title, value, color="#f0f2f6"):
        return f"""<div style="background-color:{color};padding:20px;border-radius:10px;border:1px solid #e0e0e0;"><p style="margin:0;font-size:14px;color:#555;">{title}</p><h2 style="margin:0;font-size:28px;color:#000;">{value}</h2></div>"""

    level_color = "#d4edda" if "Fast" in level else "#fff3cd" if "Normal" in level else "#f8d7da"
    
    with col_card1: st.markdown(card("Estimated Resolution", f"{days} Days"), unsafe_allow_html=True)
    with col_card2: st.markdown(card("Risk Category", level, color=level_color), unsafe_allow_html=True)

    add_margin(t=20)
    # c_chart, c_details = st.columns([1.5, 1])
    c_chart = st.container()
    with c_chart:
        st.markdown("#### Time-to-Fix Gauge")
        fig = go.Figure(go.Indicator(
            mode = "gauge+number+delta", value = days,
            domain = {'x': [0, 1], 'y': [0, 1]},
            title = {'text': "Days to Resolve", 'font': {'size': 18, 'color': "gray"}},
            delta = {'reference': 7, 'increasing': {'color': "red"}, 'decreasing': {'color': "green"}},
            gauge = {
                'axis': {'range': [None, 30], 'tickwidth': 1, 'tickcolor': "#333"},
                'bar': {'color': "#2b2b2b", 'thickness': 0.25}, 'bgcolor': "white", 'borderwidth': 2, 'bordercolor': "#eee",
                'steps': [
                    {'range': [0, 3], 'color': "#2ecc71"}, {'range': [3, 7], 'color': "#f1c40f"},
                    {'range': [7, 14], 'color': "#e67e22"}, {'range': [14, 30], 'color': "#e74c3c"}
                ],
                'threshold': {'line': {'color': "red", 'width': 4}, 'thickness': 0.75, 'value': days}
            }
        ))
        fig.update_layout(height=450, margin=dict(l=30, r=30, t=50, b=20), paper_bgcolor="rgba(0,0,0,0)", font={'family': "Arial"})
        st.plotly_chart(fig, use_container_width=True)
        st.markdown("""<div style="display:flex;justify-content:center;gap:15px;font-size:0.9em;margin-top:-10px;"><div><span style='color:#2ecc71;font-weight:bold;'>■</span> 0-3 Fast</div><div><span style='color:#f1c40f;font-weight:bold;'>■</span> 3-7 Moderate</div><div><span style='color:#e67e22;font-weight:bold;'>■</span> 7-14 Slow</div><div><span style='color:#e74c3c;font-weight:bold;'>■</span> 14+ Very Slow</div></div>""", unsafe_allow_html=True)

    # with c_details:
    #     st.markdown("#### 🤖 Technical Details")
    #     st.info("""**Prediction Factors:**\n* **Traffic/Density:** High density districts typically add +2 days.\n* **Issue Type:** 'Flood' & 'Road' issues have higher complexity weights.\n* **Historical Data:** Based on 2021-2024 resolution stats.""")
    #     with st.expander("View Feature Vector (JSON)", expanded=False):
    #         st.code(str(features), language="json")
    #         st.caption("Raw input passed to Spark Model pipeline.")

def render_prediction_page():
    st.title("🔮📅 Time Predictor Model 📅🔮")
    try: p = TraffyTimePredictor()
    except Exception as e: st.error(f"Init Error: {e}"); return
    render_input_section(p)

if __name__ == "__main__":
    st.set_page_config(layout="wide", page_title="AI Time Predictor")
    render_prediction_page()