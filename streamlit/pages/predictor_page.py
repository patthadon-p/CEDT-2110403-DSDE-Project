# Standard library
import datetime

# External dependencies
import folium
import plotly.graph_objects as go
import streamlit as st

# Project modules
from components.data_loader import load_geo_data
from components.model_predictor import (
    TraffyTimePredictor,
    clear_coordinates,
    handle_pending_updates,
)
from components.utils import _HAS_JS_EVAL, add_margin, get_geolocation
from pyspark.sql import DataFrame
from streamlit_folium import st_folium


# --- Page 4: Time Predictor (New Page) ---
def render_prediction_page() -> None:
    st.title("🔮📅 Time Predictor Model 📅🔮")

    add_margin(bottom=10)
    st.subheader("Estimate Resolution Time for a New Report")

    # Initialize the predictor inside the page render, so it reloads on session reset (if cached)
    try:
        p = TraffyTimePredictor()
    except Exception as e:
        st.error(
            f"Prediction Model Initialization Error: {e}. Check data paths or dependencies."
        )
        return

    # UI Logic for input and prediction
    render_input_section(p)


def render_input_section(predictor: TraffyTimePredictor) -> None:
    # # Process any pending coordinates from GPS/Map *before* rendering the widgets
    # handle_pending_updates()

    # --- SAFE PATCH 1: Run pending updates, but avoid UI during mid-render ---
    if "pending_coords" in st.session_state:
        updated = handle_pending_updates()  # Must return True if something changed
        if updated:
            st.rerun()

    # Ensure session state is initialized for coordinates
    if "confirmed_lat" not in st.session_state:
        st.session_state.update(
            {
                "confirmed_lat": None,
                "confirmed_long": None,
                "location_source": None,
                "geo_match_found": None,
                "sb_district": "--- Select District ---",
                "sb_subdistrict": None,
            }
        )

    # --- 1. GENERAL INFORMATION ---
    st.subheader("1. Date selection")
    c1, _ = st.columns([1, 1])
    with c1:
        # Use session state to hold the date value, just in case
        if "report_date" not in st.session_state:
            st.session_state["report_date"] = datetime.date.today()

        report_date = st.date_input(
            "Report Date",
            value=st.session_state["report_date"],
            max_value=datetime.date.today(),
            key="report_date_widget",  # Use a key linked to session state
        )
        st.session_state["report_date"] = report_date

    add_margin(top=20)
    st.markdown("---")

    # --- 2. EXACT LOCATION ---
    st.subheader("2. Exact Location & Area")

    # Toggle Input Method
    input_mode = st.radio(
        "Input Method:",
        ["📍 Use Current Location (GPS)", "🗺️ Select on Map / Manual"],
        horizontal=True,
        key="input_mode_widget",
        label_visibility="collapsed",
    )
    add_margin(top=10)

    col_map, col_info = st.columns([1, 1], gap="large")

    current_district_val = None
    current_subdistrict_val = None

    # --- RIGHT COLUMN: INFO & DROPDOWNS (Logic Priority) ---
    with col_info:
        if input_mode == "🗺️ Select on Map / Manual":
            st.markdown("##### Identified Area")
            st.caption("Select manually or click map to auto-fill.")

            d_opts = ["--- Select District ---"] + sorted(predictor.d_map.keys())

            # Get the current selected value from session state
            sb_d_val = st.session_state.get("sb_district", "--- Select District ---")
            d_idx = d_opts.index(sb_d_val) if sb_d_val in d_opts else 0

            # District Dropdown
            sel_d = st.selectbox(
                "District", d_opts, index=d_idx, key="sb_district_widget"
            )

            # Update session state *after* the widget value is confirmed (Streamlit's mechanics)
            if sel_d != st.session_state.get("sb_district"):
                st.session_state["sb_district"] = sel_d
                # Reset subdistrict to None or first valid option when district changes
                s_opts = predictor.d_map.get(sel_d, [])
                st.session_state["sb_subdistrict"] = s_opts[0] if s_opts else None

            # Subdistrict Dropdown
            current_district_for_sub = st.session_state["sb_district"]

            if current_district_for_sub == "--- Select District ---":
                st.selectbox("Subdistrict", ["(Select District first)"], disabled=True)
                sel_s = None
            else:
                s_opts = sorted(predictor.d_map[current_district_for_sub])

                # Ensure the stored value is valid for the current district
                sb_s_val = st.session_state.get("sb_subdistrict")
                if sb_s_val not in s_opts:
                    sb_s_val = s_opts[0] if s_opts else None

                s_idx = s_opts.index(sb_s_val) if sb_s_val in s_opts else 0

                sel_s = st.selectbox(
                    "Subdistrict", s_opts, index=s_idx, key="sb_subdistrict_widget"
                )

                # Update session state
                if sel_s != st.session_state.get("sb_subdistrict"):
                    st.session_state["sb_subdistrict"] = sel_s

            # Set the current area for prediction/map logic
            current_district_val = sel_d if sel_d != "--- Select District ---" else None
            current_subdistrict_val = sel_s

        else:
            # GPS Mode: Hide Dropdowns
            st.markdown("##### Identified Area (GPS)")
            if st.session_state.get(
                "location_source"
            ) == "Current GPS" and st.session_state.get("geo_match_found"):
                d = st.session_state.get("sb_district")
                s = st.session_state.get("sb_subdistrict")
                st.info(f"📍 **{d}** > **{s}**")
                current_district_val = d
                current_subdistrict_val = s
            elif st.session_state.get(
                "location_source"
            ) == "Current GPS" and not st.session_state.get("geo_match_found"):
                st.info(
                    "📍 **Coordinates confirmed, but no matching district/subdistrict found.**"
                )
                current_district_val = None  # Ensure it doesn't try to use bad values
                current_subdistrict_val = None
            else:
                st.info("Waiting for location...")
                current_district_val = None
                current_subdistrict_val = None

            add_margin(top=10)
            st.markdown("##### Coordinates")

            if st.session_state["confirmed_lat"]:
                c_coord, c_clear = st.columns([3, 1])
                with c_coord:
                    st.success(
                        f"**{st.session_state['confirmed_lat']:.6f}, {st.session_state['confirmed_long']:.6f}**",
                        icon="✅",
                    )
                with c_clear:
                    st.button(
                        "🗑️ Clear",
                        on_click=clear_coordinates,
                        width="stretch",
                        help="Reset coordinates",
                    )
            else:
                st.warning("No coordinates confirmed yet.", icon="⏳")

    # --- LEFT COLUMN: MAP ---
    with col_map:
        if input_mode == "🗺️ Select on Map / Manual":
            st.markdown("**📍 Point Selection**")
            st.caption("Click map then 'Confirm Pin'.")

            gdf = load_geo_data()
            center = [13.7563, 100.5018]
            zoom = 11
            target_geo = None

            # Zoom Logic: Confirmed Pin > Selected Area > Default Center
            if st.session_state["confirmed_lat"]:
                center = [
                    st.session_state["confirmed_lat"],
                    st.session_state["confirmed_long"],
                ]
                zoom = 15
            elif gdf is not None and current_district_val:
                t = gdf[gdf["district_name"] == current_district_val]
                if current_subdistrict_val:
                    sub_t = t[t["subdistrict_name"] == current_subdistrict_val]
                    if not sub_t.empty:
                        t = sub_t
                        zoom = 14
                    else:
                        zoom = 12
                else:
                    zoom = 12

                if not t.empty:
                    c = t.geometry.centroid.iloc[0]
                    # Extract coordinates properly from the geometry
                    coords = list(c.coords)[0]  # type: ignore
                    center = [coords[1], coords[0]]
                    target_geo = t

            m = folium.Map(location=center, zoom_start=zoom)

            if target_geo is not None:
                folium.GeoJson(
                    target_geo,
                    style_function=lambda x: {
                        "fillColor": "#ffaf00",
                        "color": "red",
                        "weight": 2,
                        "fillOpacity": 0.1,
                    },
                ).add_to(m)

            if st.session_state["confirmed_lat"]:
                folium.Marker(
                    [
                        st.session_state["confirmed_lat"],
                        st.session_state["confirmed_long"],
                    ],
                    icon=folium.Icon(color="green", icon="check"),
                ).add_to(m)

            m.add_child(folium.LatLngPopup())

            # Map key should only change when coordinates or the selected area changes
            map_key = f"map_manual_{current_district_val}_{current_subdistrict_val}_{st.session_state['confirmed_lat']}"
            map_data = st_folium(
                m,
                height=380,
                width=None,
                key=map_key,
                returned_objects=["last_clicked"],
            )

            if map_data and map_data.get("last_clicked"):
                new_lat = map_data["last_clicked"]["lat"]
                new_lng = map_data["last_clicked"]["lng"]

                if st.button("✅ Confirm Pin", width="stretch"):
                    st.session_state["pending_coords"] = {
                        "lat": new_lat,
                        "lng": new_lng,
                        "source": "Map Selection",
                    }

        else:
            # GPS Mode
            st.markdown("**📍 GPS Selection**")
            if _HAS_JS_EVAL:
                st.info("Click below to use browser location.")
                add_margin(top=10)
                geo_data = get_geolocation()  # This is non-blocking

                # The logic needs to handle the asynchronous nature of get_geolocation
                # If geo_data is returned (on a subsequent rerun), process it.
                if geo_data:
                    # Only set pending coords if we received a result and it's not already set
                    st.session_state["pending_coords"] = {
                        "lat": geo_data["coords"]["latitude"],
                        "lng": geo_data["coords"]["longitude"],
                        "source": "Current GPS",
                    }

                if st.session_state.get(
                    "location_source"
                ) != "Current GPS" or not st.session_state.get("confirmed_lat"):
                    st.button(
                        "📡 Get My Location & Auto-Fill",
                        width="stretch",
                        help="This may trigger a single full page reload to get the location data.",
                    )
                else:
                    st.success("Location confirmed via GPS.")

                add_margin(bottom=80)
            else:
                st.error(
                    "GPS functionality disabled. Set `_HAS_JS_EVAL = True` or install `streamlit-js-eval`."
                )
                add_margin(bottom=80)

    add_margin(top=20)
    st.markdown("---")

    # --- 3. DETAILS ---
    st.subheader("3. Agencies & Issues")
    # Use keys for multi-selects to store values in session state automatically
    c1, c2 = st.columns(2)
    with c1:
        orgs = st.multiselect(
            "Responsible Organization", predictor.orgs, key="predictor_orgs"
        )
    with c2:
        types = st.multiselect("Problem Type", predictor.p_types, key="predictor_types")

    add_margin(top=30)
    if st.button("🚀 Compute Prediction", type="primary", width="stretch"):
        if (
            not current_district_val
            or current_district_val == "--- Select District ---"
        ):
            st.error("⚠️ Select District")
            return
        if not current_subdistrict_val:
            st.error("⚠️ Select Subdistrict")
            return
        if not st.session_state["confirmed_lat"]:
            st.error("⚠️ Confirm Location")
            return
        if not orgs or not types:
            st.error("⚠️ Fill Details")
            return

        features = predictor.prepare_features(
            current_district_val,
            current_subdistrict_val,
            types,
            orgs,
            report_date,
            st.session_state["confirmed_lat"],
            st.session_state["confirmed_long"],
        )
        with st.spinner("Predicting..."):
            days, level = predictor.predict(features)
        display_results(int(days), level, features)


def display_results(days: int, level: str, features: DataFrame) -> None:
    add_margin(top=30)
    st.markdown("---")
    st.markdown("### 📊 Analysis Report")

    col_card1, col_card2 = st.columns(2)

    def card(title: str, value: str, color: str = "#f0f2f6") -> str:
        return f"""<div style="background-color:{color};padding:20px;border-radius:10px;border:1px solid #e0e0e0;"><p style="margin:0;font-size:14px;color:#555;">{title}</p><h2 style="margin:0;font-size:28px;color:#000;">{value}</h2></div>"""

    level_color = (
        "#d4edda" if "Fast" in level else "#fff3cd" if "Normal" in level else "#f8d7da"
    )

    with col_card1:
        st.markdown(
            card("Estimated Resolution", f"**{days}** Days"), unsafe_allow_html=True
        )
    with col_card2:
        st.markdown(
            card("Risk Category", f"**{level}**", color=level_color),
            unsafe_allow_html=True,
        )

    add_margin(top=20)
    c_chart = st.container()

    with c_chart:
        st.markdown("#### Time-to-Fix Gauge")
        fig = go.Figure(
            go.Indicator(
                mode="gauge+number+delta",
                value=days,
                domain={"x": [0, 1], "y": [0, 1]},
                title={
                    "text": "Days to Resolve",
                    "font": {"size": 18, "color": "gray"},
                },
                delta={
                    "reference": 7,
                    "increasing": {"color": "red"},
                    "decreasing": {"color": "green"},
                },
                gauge={
                    "axis": {"range": [None, 30], "tickwidth": 1, "tickcolor": "#333"},
                    "bar": {"color": "#2b2b2b", "thickness": 0.25},
                    "bgcolor": "white",
                    "borderwidth": 2,
                    "bordercolor": "#eee",
                    "steps": [
                        {"range": [0, 3], "color": "#2ecc71"},
                        {"range": [3, 7], "color": "#f1c40f"},
                        {"range": [7, 14], "color": "#e67e22"},
                        {"range": [14, 30], "color": "#e74c3c"},
                    ],
                    "threshold": {
                        "line": {"color": "red", "width": 4},
                        "thickness": 0.75,
                        "value": days,
                    },
                },
            )
        )
        fig.update_layout(
            height=450,
            margin={"l": 30, "r": 30, "t": 50, "b": 20},
            paper_bgcolor="rgba(0,0,0,0)",
            font={"family": "Arial"},
        )
        st.plotly_chart(fig, width="stretch")

        st.markdown(
            """<div style="display:flex;justify-content:center;gap:15px;font-size:0.9em;margin-top:-10px;"><div><span style='color:#2ecc71;font-weight:bold;'>■</span> 0-3 Fast</div><div><span style='color:#f1c40f;font-weight:bold;'>■</span> 3-7 Moderate</div><div><span style='color:#e67e22;font-weight:bold;'>■</span> 7-14 Slow</div><div><span style='color:#e74c3c;font-weight:bold;'>■</span> 14+ Very Slow</div></div>""",
            unsafe_allow_html=True,
        )

        with st.expander("🤖 Technical Details and Feature Vector", expanded=False):
            st.info(
                """**Prediction Factors:**\n* **Location (District/Subdistrict):** Density and historical performance.\n* **Issue Type:** Complexity weight based on problem type (e.g., 'Flood', 'Road').\n* **Organization:** Assigned agency historical resolution time.\n* **Date:** Month/Year for seasonality.\n\n*Note: This is a simplified mock model for demonstration.*"""
            )
            st.code(str(features), language="json")
            st.caption("Raw input vector passed to the prediction model.")
