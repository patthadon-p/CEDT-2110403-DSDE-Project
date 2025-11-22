# Import necessary libraries
import datetime

import altair as alt
import pandas as pd
import streamlit as st

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
    df = pd.read_csv(read_config_path("processed", "cleansed_data_path"))

    # list of categories
    df["type_cleaned"] = (
        df["type"]
        .astype(str)
        .str.replace("{", "", regex=False)
        .str.replace("}", "", regex=False)
        .str.split(",")
    )

    # single main category
    df["type_clean"] = df["type_cleaned"].apply(
        lambda x: x[0].strip() if isinstance(x, list) and len(x) > 0 else None
    )

    return df


@st.cache_data
def load_scores() -> pd.DataFrame:
    # web-scraped score data (50 districts)
    return pd.read_csv(read_config_path("scrapping", "bangkok_index_scrapped_path"))


# Load cleansed data and scores
df_cleansed = load_cleansed()
df_score = load_scores()


# -----------------------------
# 2) SIDEBAR FILTERS
# -----------------------------


@st.cache_data
def get_type_list(df: pd.DataFrame) -> list[str]:
    return sorted({t.strip() for row in df["type_cleaned"] for t in row})


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


# -----------------------------
# 4) SCATTER 1: DAILY COUNTS OVER TIME (ALTAIR)
# -----------------------------

daily_counts = (
    gdf_filtered.groupby(["timestamp_year", "timestamp_month", "timestamp_date"])
    .size()
    .reset_index(name="count")
)

if daily_counts.empty:
    st.warning("ไม่มีข้อมูลในช่วงเวลาหรือประเภทที่เลือก")
else:
    daily_counts["date"] = pd.to_datetime(
        daily_counts[["timestamp_year", "timestamp_month", "timestamp_date"]].rename(
            columns={
                "timestamp_year": "year",
                "timestamp_month": "month",
                "timestamp_date": "day",
            }
        )
    )

    daily_counts["year_month"] = daily_counts["date"].dt.to_period("M").astype(str)

    st.markdown("---")
    st.subheader(
        f"📈 จำนวนปัญหา {type_filter if type_filter else 'ทั้งหมด'} ตามเวลา (Altair Scatter)"
    )

    base = alt.Chart(daily_counts).encode(
        x=alt.X("date:T", title="วันที่"),
        y=alt.Y("count:Q", title="จำนวนปัญหา"),
        tooltip=["date:T", "count:Q", "year_month:N"],
    )

    line = base.mark_line(opacity=0.6)
    points = base.mark_circle(size=60, opacity=0.8).encode(
        color=alt.Color("year_month:N", title="เดือน", sort="ascending")
    )

    chart_time = (line + points).interactive()
    st.altair_chart(chart_time, use_container_width=True)

    st.dataframe(daily_counts[["date", "count", "year_month"]].sort_values("date"))


# -----------------------------
# 5) SCATTER 2: TOTAL_SCORE vs COMPLAINTS
# -----------------------------

st.markdown("---")
st.subheader("📌 Total Score vs Complaints ")

# ต้องมีคอลัมน์ 'district' ใน cleansed_data
if "district" not in gdf_filtered.columns:
    st.error("ไม่พบคอลัมน์ 'district' ใน cleansed_data.csv (ต้องมี district เพื่อรวมกับคะแนน)")
else:
    # นับจำนวนเรื่องร้องเรียนต่อเขต จากข้อมูลที่ถูก filter แล้ว
    complaints_by_district = (
        gdf_filtered.groupby("district").size().reset_index(name="complaints")
    )

    # รวมคะแนนเขต (50 เขต) กับจำนวนร้องเรียน
    df_typeb = df_score.merge(complaints_by_district, on="district", how="left")

    # ถ้าเขตไหนไม่มีเรื่องร้องเรียนในช่วงเวลานี้ให้ใส่ 0
    df_typeb["complaints"] = df_typeb["complaints"].fillna(0)

    if df_typeb["complaints"].sum() == 0:
        st.info("ไม่มีเรื่องร้องเรียนใด ๆ ในช่วงเวลา / ประเภทที่เลือก จึงยังวิเคราะห์ Type B ไม่ได้")
    else:
        # เกณฑ์แบ่งกลุ่ม (ปรับ quantile ได้ตามใจ)
        low_score_threshold = df_typeb["total_score"].quantile(0.3)
        high_complaints_threshold = df_typeb["complaints"].quantile(0.7)

        def label_type(row: pd.Series) -> str:
            if (
                row["total_score"] < low_score_threshold
                and row["complaints"] > high_complaints_threshold
            ):
                return "Danger Zone"
            elif (
                row["total_score"] >= low_score_threshold
                and row["complaints"] > high_complaints_threshold
            ):
                return "Active Zone"
            elif (
                row["total_score"] < low_score_threshold
                and row["complaints"] <= high_complaints_threshold
            ):
                return "Silent Risk Zone"
            else:
                return "Good Zone"

        df_typeb["zone"] = df_typeb.apply(label_type, axis=1)

        # base chart
        base_tb = alt.Chart(df_typeb).encode(
            x=alt.X("total_score:Q", title="Total Score"),
            y=alt.Y("complaints:Q", title="Number of Complaints"),
            tooltip=["district:N", "total_score:Q", "complaints:Q", "zone:N"],
        )

        # จุดทั้งหมด (สีเทาจาง)
        all_points = base_tb.mark_circle(size=70, opacity=0.3, color="lightgray")

        # จุดของแต่ละ zone (โดยเฉพาะ Type B)
        zone_points = base_tb.mark_circle(size=130, opacity=0.9).encode(
            color=alt.Color(
                "zone:N",
                title="Zone",
                scale=alt.Scale(
                    domain=[
                        "Danger Zone",
                        "Good Zone",
                        "Active Zone",
                        "Silent Risk Zone",
                    ],
                    range=["red", "#1f77b4", "#ff7f0e", "#2ca02c"],
                ),
            )
        )

        # เส้นแบ่ง threshold (แนวตั้ง–แนวนอน)
        vline = (
            alt.Chart(pd.DataFrame({"x": [low_score_threshold]}))
            .mark_rule(strokeDash=[4, 4], color="black")
            .encode(x="x:Q")
        )

        hline = (
            alt.Chart(pd.DataFrame({"y": [high_complaints_threshold]}))
            .mark_rule(strokeDash=[4, 4], color="black")
            .encode(y="y:Q")
        )

        chart_typeb = (all_points + zone_points + vline + hline).interactive()

        st.altair_chart(chart_typeb, use_container_width=True)

        st.markdown("#### 📋 ตารางสรุป Total Score + Complaints + Zone")
        st.dataframe(
            df_typeb[["district", "total_score", "complaints", "zone"]]
            .sort_values(["zone", "complaints"], ascending=[True, False])
            .reset_index(drop=True)
        )


# -----------------------------
# 6) Scatter: District Quality vs Complaints (4 มิติ)
# -----------------------------

st.markdown("---")
st.subheader("📌 Scatter Plot - จำนวนร้องเรียน เทียบกับมิติคุณภาพเขต")

# ต้องมี district เพื่อรวมกับคะแนน
if "district" not in gdf_filtered.columns:
    st.error(
        "ไม่พบคอลัมน์ 'district' ใน cleansed_data.csv (ต้องมี district เพื่อสร้าง Scatter)"
    )
else:
    # นับจำนวนร้องเรียนต่อเขตหลัง filter
    complaints_by_district = (
        gdf_filtered.groupby("district").size().reset_index(name="complaints")
    )

    # รวมกับคะแนนเขต
    df_scatter = df_score.merge(complaints_by_district, on="district", how="left")
    df_scatter["complaints"] = df_scatter["complaints"].fillna(0)

    metrics = ["public_service", "economy", "welfare", "environment"]

    # Scatter Plot function
    def make_scatter(x_col: str, df: pd.DataFrame) -> alt.Chart:
        return (
            alt.Chart(df)
            .mark_circle(size=120, opacity=0.7)
            .encode(
                x=alt.X(f"{x_col}:Q", title=x_col.replace("_", " ").title()),
                y=alt.Y(
                    "complaints:Q",
                    title=f"📈 จำนวนปัญหา {type_filter if type_filter else 'ทั้งหมด'}",
                ),
                color=alt.Color(
                    "complaints:Q", scale=alt.Scale(scheme="redyellowblue")
                ),
                tooltip=["district", x_col, "complaints"],
            )
            .properties(width=300, height=300, title=f"{x_col} vs complaints")
            .interactive()
        )

    # วาด 4 Scatter แยก panel
    charts = [make_scatter(m, df_scatter) for m in metrics]
    st.altair_chart(alt.hconcat(*charts), use_container_width=True)

    # แสดงตาราง
    st.markdown(
        f"### 📈 ตารางคะแนนเขตและจำนวนเรื่องร้องเรียน — {type_filter if type_filter else 'ทุกประเภท'}"
    )

    st.dataframe(
        df_scatter[["district"] + metrics + ["complaints"]].sort_values(
            "complaints", ascending=False
        )
    )


# -----------------------------
# 7) Multi-color Scatter: Metric vs Complaints per Top 5 Problem Types
# -----------------------------

st.markdown("---")
st.subheader("🎨 Scatter แบบหลายสี: มิติคุณภาพเขต vs จำนวนร้องเรียน (Top 5 ประเภทปัญหา)")

metrics_all = ["total_score", "public_service", "economy", "welfare", "environment"]
metric_x_multi = st.selectbox(
    "เลือกมิติคุณภาพเขตสำหรับแกน X", metrics_all, key="metric_x_multi"
)

# 1) ใช้เฉพาะ filter ตามช่วงเวลา
filtered_time_only = filtered_time.copy()

# 2) ตัด NaN / ค่าว่างออกจาก type_clean (ไม่เอา NaN เลย)
filtered_time_only = filtered_time_only.dropna(subset=["type_clean"])
filtered_time_only = filtered_time_only[
    filtered_time_only["type_clean"].astype(str).str.strip() != ""
]

if filtered_time_only.empty:
    st.info("ไม่มีข้อมูลประเภทปัญหาหลังตัด NaN / ค่าว่าง ออก")
elif "district" not in filtered_time_only.columns:
    st.error(
        "ไม่พบคอลัมน์ 'district' ใน cleansed_data.csv (ต้องมี district เพื่อสร้าง Scatter)"
    )
else:
    # 3) หา Top 5 ประเภทปัญหาที่พบมากที่สุดในช่วงเวลานี้
    top5_types = filtered_time_only["type_clean"].value_counts().head(5).index.tolist()

    if len(top5_types) == 0:
        st.info("ไม่มีประเภทปัญหาเพียงพอสำหรับสร้าง Top 5 ในช่วงเวลา / เงื่อนไขที่เลือก")
    else:
        st.write("Top 5 ประเภทปัญหาในช่วงเวลานี้:", top5_types)

        # 4) ใช้เฉพาะแถวที่เป็น Top 5 ประเภทปัญหา
        top5_df = filtered_time_only[filtered_time_only["type_clean"].isin(top5_types)]

        # 5) นับจำนวนร้องเรียนต่อ (เขต, ประเภทปัญหา)
        type_district_counts = (
            top5_df.groupby(["district", "type_clean"])
            .size()
            .reset_index(name="complaints")
        )

        # 6) รวมกับคะแนนเขต
        df_multi = type_district_counts.merge(df_score, on="district", how="left")

        if df_multi.empty:
            st.info("ไม่มีข้อมูลเพียงพอสำหรับสร้างกราฟแบบหลายสี")
        else:
            chart_multi = (
                alt.Chart(df_multi)
                .mark_circle(size=90, opacity=0.7)
                .encode(
                    x=alt.X(
                        f"{metric_x_multi}:Q",
                        title=metric_x_multi.replace("_", " ").title(),
                    ),
                    y=alt.Y("complaints:Q", title="จำนวนร้องเรียน (ต่อเขต ต่อประเภทปัญหา)"),
                    color=alt.Color(
                        "type_clean:N", title="ประเภทปัญหา", sort=top5_types
                    ),
                    tooltip=[
                        "district:N",
                        "type_clean:N",
                        alt.Tooltip(f"{metric_x_multi}:Q", title=metric_x_multi),
                        "complaints:Q",
                    ],
                )
                .properties(
                    width=600,
                    height=400,
                    title=f"{metric_x_multi} vs จำนวนร้องเรียน (Top 5 ประเภทปัญหา)",
                )
                .interactive()
            )

            st.altair_chart(chart_multi, use_container_width=True)


# -----------------------------
# ลิ้งค์ปัญหาดูกับรายได้ต่อครัวเรือน
# -----------------------------
