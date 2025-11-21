# # import datetime
# # import streamlit as st
# # import pandas as pd

# # st.set_page_config(layout="wide")

# # st.title("Bangkok Traffy – Scatter Only Viewer")
# # st.sidebar.header("Filters")

# # # Load Cleansed Data
# # @st.cache_data
# # def load_data():
# #     df = pd.read_csv("./data/processed/cleansed_data.csv")
# #     df["type_cleaned"] = (
# #         df["type"]
# #         .astype(str)
# #         .str.replace("{", "")
# #         .str.replace("}", "")
# #         .str.split(",")
# #     )
# #     return df

# # df_cleansed = load_data()

# # # Load Type list
# # @st.cache_data
# # def get_type_list(df):
# #     return sorted({t.strip() for row in df["type_cleaned"] for t in row})

# # type_list = get_type_list(df_cleansed)

# # # Sidebar Filters
# # with st.sidebar.form("filter_form"):

# #     type_filter = st.selectbox(
# #         "เลือกประเภทปัญหา",
# #         options=["ทั้งหมด"] + type_list
# #     )

# #     start_date, end_date = st.date_input(
# #         "เลือกช่วงวัน",
# #         value=[
# #             datetime.date(2021, 9, 19),
# #             datetime.date(2025, 1, 16)
# #         ],
# #         min_value=datetime.date(2021, 9, 19),
# #         max_value=datetime.date(2025, 1, 16)
# #     )

# #     submit = st.form_submit_button("Apply Filter")

# # if submit:
# #     st.session_state["type_filter"] = type_filter
# #     st.session_state["start_date"] = start_date
# #     st.session_state["end_date"] = end_date

# # type_filter = st.session_state.get("type_filter", "ทั้งหมด")
# # start_date = st.session_state.get("start_date", datetime.date(2021, 9, 19))
# # end_date = st.session_state.get("end_date", datetime.date(2025, 1, 16))

# # # ----- filter by time -----
# # filtered_time = df_cleansed[
# #     (df_cleansed[["timestamp_year", "timestamp_month", "timestamp_date"]]
# #         .apply(tuple, axis=1) >= (start_date.year, start_date.month, start_date.day))
# #     &
# #     (df_cleansed[["timestamp_year", "timestamp_month", "timestamp_date"]]
# #         .apply(tuple, axis=1) <= (end_date.year, end_date.month, end_date.day))
# # ]

# # # ----- filter by type -----
# # if type_filter != "ทั้งหมด":
# #     gdf_filtered = filtered_time[filtered_time["type_clean"] == type_filter]
# # else:
# #     gdf_filtered = filtered_time
# #     # เพื่อให้ text ในหัวข้อไม่ขึ้น None
# #     type_filter = ""

# # # NEW: prepare daily counts for scatter chart
# # daily_counts = (
# #     gdf_filtered
# #     .groupby(["timestamp_year", "timestamp_month", "timestamp_date"])
# #     .size()
# #     .reset_index(name="count")
# # )

# # if daily_counts.empty:
# #     st.warning("ไม่มีข้อมูลในช่วงเวลาหรือประเภทที่เลือก")
# # else:
# #     daily_counts["date"] = pd.to_datetime(
# #         daily_counts[["timestamp_year", "timestamp_month", "timestamp_date"]]
# #         .rename(columns={
# #             "timestamp_year": "year",
# #             "timestamp_month": "month",
# #             "timestamp_date": "day"
# #         })
# #     )

# #     # scatter chart section
# #     st.markdown("---")
# #     st.subheader(f"📈 จำนวนปัญหา {type_filter if type_filter else 'ทั้งหมด'} ตามเวลา (Scatter Chart)")

# #     st.scatter_chart(
# #         daily_counts,
# #         x="date",
# #         y="count"
# #     )

# import datetime
# import streamlit as st
# import pandas as pd
# import altair as alt   # ✅ เพิ่ม Altair เข้ามา

# st.set_page_config(layout="wide")

# st.title("Bangkok Traffy – Scatter Only Viewer")
# st.sidebar.header("Filters")

# # Load Cleansed Data
# @st.cache_data
# def load_data():
#     df = pd.read_csv("./data/processed/cleansed_data.csv")
#     df["type_cleaned"] = (
#         df["type"]
#         .astype(str)
#         .str.replace("{", "")
#         .str.replace("}", "")
#         .str.split(",")
#     )
#     return df

# df_cleansed = load_data()

# # Load Type list
# @st.cache_data
# def get_type_list(df):
#     return sorted({t.strip() for row in df["type_cleaned"] for t in row})

# type_list = get_type_list(df_cleansed)

# # Sidebar Filters
# with st.sidebar.form("filter_form"):

#     type_filter = st.selectbox(
#         "เลือกประเภทปัญหา",
#         options=["ทั้งหมด"] + type_list
#     )

#     start_date, end_date = st.date_input(
#         "เลือกช่วงวัน",
#         value=[
#             datetime.date(2021, 9, 19),
#             datetime.date(2025, 1, 16)
#         ],
#         min_value=datetime.date(2021, 9, 19),
#         max_value=datetime.date(2025, 1, 16)
#     )

#     submit = st.form_submit_button("Apply Filter")

# if submit:
#     st.session_state["type_filter"] = type_filter
#     st.session_state["start_date"] = start_date
#     st.session_state["end_date"] = end_date

# type_filter = st.session_state.get("type_filter", "ทั้งหมด")
# start_date = st.session_state.get("start_date", datetime.date(2021, 9, 19))
# end_date = st.session_state.get("end_date", datetime.date(2025, 1, 16))

# # ----- filter by time -----
# filtered_time = df_cleansed[
#     (df_cleansed[["timestamp_year", "timestamp_month", "timestamp_date"]]
#         .apply(tuple, axis=1) >= (start_date.year, start_date.month, start_date.day))
#     &
#     (df_cleansed[["timestamp_year", "timestamp_month", "timestamp_date"]]
#         .apply(tuple, axis=1) <= (end_date.year, end_date.month, end_date.day))
# ]

# # ----- filter by type -----
# if type_filter != "ทั้งหมด":
#     gdf_filtered = filtered_time[filtered_time["type_clean"] == type_filter]
# else:
#     gdf_filtered = filtered_time
#     # เพื่อให้ text ในหัวข้อไม่ขึ้น None
#     type_filter = ""

# # เตรียม daily counts
# daily_counts = (
#     gdf_filtered
#     .groupby(["timestamp_year", "timestamp_month", "timestamp_date"])
#     .size()
#     .reset_index(name="count")
# )

# if daily_counts.empty:
#     st.warning("ไม่มีข้อมูลในช่วงเวลาหรือประเภทที่เลือก")
# else:
#     daily_counts["date"] = pd.to_datetime(
#         daily_counts[["timestamp_year", "timestamp_month", "timestamp_date"]]
#         .rename(columns={
#             "timestamp_year": "year",
#             "timestamp_month": "month",
#             "timestamp_date": "day"
#         })
#     )

#     # เพิ่มคอลัมน์ year_month เพื่อใช้ทำสี (optional)
#     daily_counts["year_month"] = daily_counts["date"].dt.to_period("M").astype(str)

#     st.markdown("---")
#     st.subheader(f"📈 จำนวนปัญหา {type_filter if type_filter else 'ทั้งหมด'} ตามเวลา (Altair Scatter)")

#     # ✅ Altair chart: line + scatter + tooltip + zoom/pan
#     base = alt.Chart(daily_counts).encode(
#         x=alt.X("date:T", title="วันที่"),
#         y=alt.Y("count:Q", title="จำนวนปัญหา"),
#         tooltip=["date:T", "count:Q", "year_month:N"]
#     )

#     line = base.mark_line(opacity=0.6)
#     points = base.mark_circle(size=60, opacity=0.8).encode(
#         color=alt.Color("year_month:N", title="เดือน")
#     )

#     chart = (line + points).interactive()

#     st.altair_chart(chart, use_container_width=True)

#     # แสดงตารางด้านล่างเผื่ออยากดูตัวเลข
#     st.dataframe(
#         daily_counts[["date", "count", "year_month"]]
#         .sort_values("date")
#     )
import datetime

import pandas as pd
import streamlit as st

st.set_page_config(layout="wide")
st.title("Bangkok Traffy – Scatter Insights Dashboard")
st.sidebar.header("Filters")

# -----------------------------
# 1) LOAD & PREPROCESS DATA
# -----------------------------
@st.cache_data
def load_data():
    df = pd.read_csv("./data/processed/cleansed_data.csv")

    # type_cleaned: list of categories per ticket
    if "type_cleaned" not in df.columns:
        df["type_cleaned"] = (
            df["type"]
              .astype(str)
              .str.replace("{", "")
              .str.replace("}", "")
              .str.split(",")
        )

    # ถ้ามี type_clean ใช้เป็น single label, ถ้าไม่มีก็ใช้ตัวแรกจาก type_cleaned
    if "type_clean" not in df.columns:
        df["type_clean"] = df["type_cleaned"].apply(lambda xs: xs[0].strip() if len(xs) > 0 else "ไม่ระบุ")

    # ------------------
    # สร้าง timestamp จริง
    # ------------------
    if {"timestamp_year", "timestamp_month", "timestamp_date"}.issubset(df.columns):
        df["timestamp_dt"] = pd.to_datetime(
            df[["timestamp_year", "timestamp_month", "timestamp_date"]]
            .rename(columns={
                "timestamp_year": "year",
                "timestamp_month": "month",
                "timestamp_date": "day"
            }),
            errors="coerce"
        )
    elif "timestamp" in df.columns:
        df["timestamp_dt"] = pd.to_datetime(df["timestamp"], errors="coerce")
    else:
        st.error("ไม่พบคอลัมน์ timestamp_year/month/date หรือ timestamp ในไฟล์ cleansed_data.csv")
        df["timestamp_dt"] = pd.NaT

    # hour / day / month / year
    df["hour"] = df["timestamp_dt"].dt.hour
    df["day_of_month"] = df["timestamp_dt"].dt.day
    df["month"] = df["timestamp_dt"].dt.month
    df["year"] = df["timestamp_dt"].dt.year
    df["date"] = df["timestamp_dt"].dt.date

    # ------------------
    # last_activity + resolve_time (ชม.)
    # ------------------
    if "last_activity" in df.columns:
        df["last_activity_dt"] = pd.to_datetime(df["last_activity"], errors="coerce")
        df["resolve_hours"] = (df["last_activity_dt"] - df["timestamp_dt"]).dt.total_seconds() / 3600.0
    else:
        df["last_activity_dt"] = pd.NaT
        df["resolve_hours"] = pd.NA

    # star rating
    if "star" in df.columns:
        df["star"] = pd.to_numeric(df["star"], errors="coerce")

    # count_reopen
    if "count_reopen" in df.columns:
        df["count_reopen"] = pd.to_numeric(df["count_reopen"], errors="coerce")

    # TODO: ปรับชื่อคอลัมน์ lat/lon ให้ตรงกับไฟล์จริง
    # สมมติว่ามี columns ชื่อ lat, lon
    if "lat" not in df.columns or "lon" not in df.columns:
        # ถ้าไม่มีให้สร้าง dummy ไว้ก่อน (จะไม่มี scatter แผนที่จริง ๆ)
        df["lat"] = pd.NA
        df["lon"] = pd.NA

    # district / subdistrict ถ้ามี
    if "district" not in df.columns and "district_name" in df.columns:
        df["district"] = df["district_name"]

    return df

df = load_data()

# -----------------------------
# 2) SIDEBAR FILTERS
# -----------------------------
# type list
type_list = sorted({t.strip() for row in df["type_cleaned"] for t in row})

type_filter = st.sidebar.selectbox(
    "เลือกประเภทปัญหา",
    options=["ทั้งหมด"] + type_list
)

# district filter (optional)
district_options = ["ทั้งหมด"]
if "district" in df.columns:
    district_options += sorted(df["district"].dropna().unique().tolist())

district_filter = st.sidebar.selectbox(
    "เลือกเขต (ถ้ามี)",
    options=district_options
)

# date range
min_date = df["date"].min() or datetime.date(2021, 1, 1)
max_date = df["date"].max() or datetime.date(2025, 12, 31)

start_date, end_date = st.sidebar.date_input(
    "เลือกช่วงวัน",
    value=[min_date, max_date],
    min_value=min_date,
    max_value=max_date,
)

# -----------------------------
# 3) APPLY FILTERS
# -----------------------------
filtered = df.copy()

# date filter
filtered = filtered[
    (filtered["date"] >= start_date) &
    (filtered["date"] <= end_date)
]

# type filter
if type_filter != "ทั้งหมด":
    filtered = filtered[filtered["type_clean"] == type_filter]

# district filter
if district_filter != "ทั้งหมด" and "district" in filtered.columns:
    filtered = filtered[filtered["district"] == district_filter]

st.write(
    f"แสดงข้อมูลทั้งหมด **{len(filtered)}** เคส "
    f"ประเภท: **{type_filter if type_filter != 'ทั้งหมด' else 'ทุกประเภท'}** "
    f"{' | เขต: ' + district_filter if district_filter != 'ทั้งหมด' else ''}"
)

if filtered.empty:
    st.warning("ไม่มีข้อมูลตามเงื่อนไขที่เลือก")
    st.stop()

# -----------------------------
# 4) สร้าง DataFrame ช่วยสำหรับบางกราฟ
# -----------------------------
# daily counts
daily_counts = (
    filtered
    .groupby("date")
    .size()
    .reset_index(name="count")
    .sort_values("date")
)
daily_counts["date_dt"] = pd.to_datetime(daily_counts["date"])

# rolling mean & std เผื่อใช้ anomaly detection
daily_counts["roll_mean_7"] = daily_counts["count"].rolling(window=7, min_periods=1).mean()
daily_counts["roll_std_7"] = daily_counts["count"].rolling(window=7, min_periods=1).std()
daily_counts["roll_std_7"].fillna(0, inplace=True)
daily_counts["is_anomaly"] = daily_counts["count"] > (daily_counts["roll_mean_7"] + 2 * daily_counts["roll_std_7"])

# -----------------------------
# 5) TABS
# -----------------------------
tab_time, tab_area, tab_problem, tab_perf, tab_anom = st.tabs(
    ["⏰ Time Patterns", "📍 Area / Location", "🧩 Problem Types", "⚙️ Performance", "🚨 Anomalies"]
)

# ============================
# TAB A: TIME PATTERNS
# ============================
with tab_time:
    st.subheader("A1) Scatter: จำนวนเคสต่อชั่วโมง (Hour-of-Day)")

    hour_counts = (
        filtered
        .groupby("hour")
        .size()
        .reset_index(name="count")
        .sort_values("hour")
    )

    st.scatter_chart(hour_counts, x="hour", y="count")
    st.caption("ดูว่าในหนึ่งวันช่วงเวลาไหนมีการแจ้งปัญหามากที่สุด")

    st.markdown("---")
    st.subheader("A2) Scatter: จำนวนเคสตามวันที่ในเดือน (Day-of-Month)")

    dom_counts = (
        filtered
        .groupby("day_of_month")
        .size()
        .reset_index(name="count")
        .sort_values("day_of_month")
    )
    st.scatter_chart(dom_counts, x="day_of_month", y="count")
    st.caption("รวมทุกเดือน ดูว่าเลขวันที่ไหนมีการแจ้งบ่อย (เช่น ต้นเดือน ปลายเดือน ฯลฯ)")

    st.markdown("---")
    st.subheader("A3) Scatter + Trend: จำนวนเคสรายวัน")

    st.scatter_chart(daily_counts, x="date_dt", y="count")
    st.line_chart(daily_counts.set_index("date_dt")[["roll_mean_7"]])
    st.caption("จุด = จำนวนเคสรายวัน, เส้น = ค่าเฉลี่ยเคลื่อนที่ 7 วัน (ช่วยเห็นเทรนด์ขึ้นหรือลง)")

# ============================
# TAB B: AREA / LOCATION
# ============================
with tab_area:
    st.subheader("B1) Scatter: พิกัด Lat/Lon (Colored by Month)")

    loc_df = filtered.dropna(subset=["lat", "lon"]).copy()
    if loc_df.empty:
        st.info("ยังไม่มีข้อมูล lat/lon ใน dataset หรือยังไม่ได้กำหนดชื่อคอลัมน์ lat / lon")
    else:
        # month label
        loc_df["month_label"] = loc_df["timestamp_dt"].dt.strftime("%Y-%m")
        # ใช้ scatter_chart โดยให้ color เป็น month_label
        st.scatter_chart(
            loc_df,
            x="lon",
            y="lat",
            color="month_label",
        )
        st.caption("กระจายจุดตามพิกัด และใช้สีแทนเดือนที่แจ้ง เพื่อดูการเปลี่ยนแปลงในพื้นที่ตามเวลา")

    st.markdown("---")
    st.subheader("B2) Scatter: เขต vs เวลาเฉลี่ยในการแก้ปัญหา (ชม.)")

    if "district" not in filtered.columns or filtered["resolve_hours"].dropna().empty:
        st.info("ต้องมีคอลัมน์ district และ resolve_hours (จาก timestamp + last_activity) จึงจะเห็นกราฟนี้ได้")
    else:
        district_resolve = (
            filtered
            .dropna(subset=["resolve_hours"])
            .groupby("district")["resolve_hours"]
            .mean()
            .reset_index(name="avg_resolve_hours")
            .sort_values("avg_resolve_hours")
        )
        st.scatter_chart(district_resolve, x="district", y="avg_resolve_hours")
        st.caption("ดูว่าเขตไหนแก้ปัญหาได้เร็ว / ช้ากว่าเขตอื่น (หน่วย: ชั่วโมง)")

# ============================
# TAB C: PROBLEM TYPES
# ============================
with tab_problem:
    st.subheader("C1) Scatter: จำนวนเคส vs เวลาเฉลี่ยในการแก้ปัญหา (ตามประเภทปัญหา)")

    if filtered["resolve_hours"].dropna().empty:
        st.info("ยังคำนวณ resolve_hours ไม่ได้ (ไม่มี last_activity) เลยยังทำกราฟนี้ไม่ได้")
    else:
        type_stats = (
            filtered
            .dropna(subset=["resolve_hours"])
            .groupby("type_clean")
            .agg(
                total_cases=("type_clean", "size"),
                avg_resolve_hours=("resolve_hours", "mean"),
            )
            .reset_index()
        )
        st.scatter_chart(
            type_stats,
            x="total_cases",
            y="avg_resolve_hours",
        )
        st.caption("ประเภทที่อยู่มุมขวาบน = เคสเยอะและแก้ช้า ควรเป็นเป้าหมายในการปรับปรุงก่อน")

    st.markdown("---")
    st.subheader("C2) Scatter: จำนวนเคส vs ค่าเฉลี่ยดาว (ความพึงพอใจ)")

    if "star" not in filtered.columns or filtered["star"].dropna().empty:
        st.info("ไม่มีคอลัมน์ star หรือยังไม่มีเรตติ้งเพียงพอ")
    else:
        type_star = (
            filtered
            .dropna(subset=["star"])
            .groupby("type_clean")
            .agg(
                total_cases=("type_clean", "size"),
                avg_star=("star", "mean"),
            )
            .reset_index()
        )
        st.scatter_chart(
            type_star,
            x="total_cases",
            y="avg_star",
        )
        st.caption("ประเภทที่เคสเยอะแต่คะแนนต่ำ = ปัญหาที่กระทบความพึงพอใจสูง")

# ============================
# TAB D: PERFORMANCE
# ============================
with tab_perf:
    st.subheader("D1) Scatter: เวลาในการแก้ปัญหา vs จำนวนครั้งที่ถูก reopen")

    if "count_reopen" not in filtered.columns or filtered[["resolve_hours", "count_reopen"]].dropna().empty:
        st.info("ต้องมีคอลัมน์ resolve_hours และ count_reopen จึงจะเห็นกราฟนี้ได้")
    else:
        perf_df = filtered.dropna(subset=["resolve_hours", "count_reopen"]).copy()
        st.scatter_chart(
            perf_df,
            x="resolve_hours",
            y="count_reopen"
        )
        st.caption("ถ้าจุดกระจุกอยู่โซนเวลาแก้นานและ reopen บ่อย แปลว่ามีปัญหาเชิงคุณภาพของการแก้ไข")

    st.markdown("---")
    st.subheader("D2) Scatter: เวลาเฉลี่ยในการแก้ปัญหา vs เขต")

    if "district" not in filtered.columns or filtered["resolve_hours"].dropna().empty:
        st.info("ไม่มี district หรือ resolve_hours ไม่พอ")
    else:
        district_perf = (
            filtered
            .dropna(subset=["resolve_hours"])
            .groupby("district")["resolve_hours"]
            .mean()
            .reset_index(name="avg_resolve_hours")
        )
        st.scatter_chart(
            district_perf,
            x="district",
            y="avg_resolve_hours"
        )
        st.caption("ใช้เปรียบเทียบ performance ระหว่างเขตแบบ high-level")

# ============================
# TAB E: ANOMALIES
# ============================
with tab_anom:
    st.subheader("E1) Scatter: Anomaly Detection ของจำนวนเคสรายวัน")

    if daily_counts.empty:
        st.info("ยังไม่มีข้อมูลรายวันเพียงพอ")
    else:
        # แยก 2 กลุ่ม: ปกติ vs anomaly
        normal_days = daily_counts[~daily_counts["is_anomaly"]]
        anomaly_days = daily_counts[daily_counts["is_anomaly"]]

        st.write("จุดสีฟ้า = วันปกติ, จุดสีแดง = วันที่จำนวนเคสสูงผิดปกติ (มากกว่าค่าเฉลี่ย + 2*std)")

        # ใช้ st.scatter_chart ทำสองกราฟซ้อนกัน (หรือ Nat จะไปปรับให้เป็น Altair ก็ได้)
        st.scatter_chart(
            normal_days,
            x="date_dt",
            y="count",
        )
        st.scatter_chart(
            anomaly_days,
            x="date_dt",
            y="count",
        )
        st.caption("ช่วยหาวันที่มีเหตุการณ์ผิดปกติ เช่น ฝนตกหนัก, น้ำท่วม, ไฟดับใหญ่ ฯลฯ")

        st.markdown("#### ตารางสรุปวันผิดปกติ")
        st.dataframe(
            anomaly_days[["date", "count", "roll_mean_7", "roll_std_7"]]
            .sort_values("date")
        )
