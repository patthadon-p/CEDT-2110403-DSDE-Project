# Import necessary libraries
import datetime
import os
import sys

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
    st.altair_chart(chart_time, width="stretch")

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
        st.info("ไม่มีเรื่องร้องเรียนใด ๆ ในช่วงเวลา / ประเภทที่เลือก จึงยังวิเคราะห์ไม่ได้")
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
            x=alt.X("total_score:Q", title="Total Score" , scale=alt.Scale(domain=[10, 40])),
            y=alt.Y("complaints:Q", title="Number of Complaints" , scale=alt.Scale(domain=[0, 20000])),
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

        chart_typeb = (all_points + zone_points + vline + hline).properties(width=700, height=500).interactive(bind_x=False, bind_y=False)
        st.altair_chart(chart_typeb, width="stretch")



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
    st.altair_chart(alt.hconcat(*charts), width="stretch" ,theme="streamlit")


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

            st.altair_chart(chart_multi, width="stretch")


# -----------------------------
# ลิ้งค์ปัญหาดูกับรายได้ต่อครัวเรือน
# -----------------------------

# -----------------------------
# 8) Pearson Heatmap: District Quality Metrics vs All Problem Types
# -----------------------------
st.markdown("---")
st.subheader("🔥 Pearson Heatmap – ความสัมพันธ์ระหว่างมิติคุณภาพเขตกับประเภทปัญหา")

# ใช้ข้อมูลตามช่วงเวลา (แต่ไม่ fix type_filter เพราะอยากดูทุกประเภทปัญหา)
corr_base = filtered_time.copy()

# ตัด NaN / ค่าว่างใน type_clean ออก (ไม่เอา NaN เลย)
corr_base = corr_base.dropna(subset=["type_clean"])
corr_base = corr_base[corr_base["type_clean"].astype(str).str.strip() != ""]

if corr_base.empty:
    st.info("ไม่มีข้อมูลประเภทปัญหาหลังตัด NaN / ค่าว่าง ออก จึงยังทำ Pearson heatmap ไม่ได้")
elif "district" not in corr_base.columns:
    st.error("ไม่พบคอลัมน์ 'district' ใน cleansed_data.csv (ต้องมี district เพื่อทำ heatmap)")
else:
    # 1) นับจำนวนร้องเรียนต่อ (เขต, ประเภทปัญหา)
    type_district_counts = (
        corr_base
        .groupby(["district", "type_clean"])
        .size()
        .reset_index(name="complaints")
    )

    # 2) Pivot ให้แต่ละประเภทปัญหาเป็นคอลัมน์ (wide format)
    pivot_types = (
        type_district_counts
        .pivot(index="district", columns="type_clean", values="complaints")
        .fillna(0)
        .reset_index()
    )

    # 3) รวมกับคะแนนเขตจาก df_score
    corr_df = df_score.merge(pivot_types, on="district", how="left").fillna(0)

    # ชื่อตัวชี้วัดคุณภาพเขต
    metric_cols = ["total_score", "public_service", "economy", "welfare", "environment"]

    # คอลัมน์ประเภทปัญหา = ทั้งหมดที่ไม่ใช่ metric และไม่ใช่ district
    type_cols = [
        c for c in corr_df.columns
        if c not in metric_cols + ["district"]
    ]

    if not type_cols:
        st.info("ไม่มีคอลัมน์ประเภทปัญหาที่จะแปลงเป็นตัวเลขสำหรับทำ Pearson heatmap")
    else:
        # (ถ้าอยากจำกัดจำนวนประเภทปัญหา ให้เลือกเฉพาะ Top N)
        # top_n = 20
        # รวมจำนวนต่อประเภท แล้วเลือก top_n
        # sums = corr_df[type_cols].sum().sort_values(ascending=False)
        # keep_types = sums.head(top_n).index.tolist()
        # type_cols = keep_types

        # 4) สร้าง correlation matrix (Pearson)
        corr_matrix = corr_df[metric_cols + type_cols].corr(method="pearson")

        # เอาเฉพาะส่วน metric (แถว) vs problem types (คอลัมน์)
        corr_sub = corr_matrix.loc[metric_cols, type_cols]

        # 5) แปลงเป็น long format สำหรับ Altair
        corr_long = (
            corr_sub
            .reset_index()
            .melt(id_vars="index", var_name="problem_type", value_name="corr")
            .rename(columns={"index": "metric"})
        )

        # 6) วาด heatmap
        heatmap = (
            alt.Chart(corr_long)
            .mark_rect()
            .encode(
                x=alt.X(
                    "problem_type:N",
                    title="ประเภทปัญหา",
                    sort=type_cols
                ),
                y=alt.Y(
                    "metric:N",
                    title="มิติคุณภาพเขต",
                    sort=metric_cols
                ),
                color=alt.Color(
                    "corr:Q",
                    title="Pearson r",
                    scale=alt.Scale(scheme="redblue", domain=[-1, 0, 1])
                ),
                tooltip=[
                    "metric:N",
                    "problem_type:N",
                    alt.Tooltip("corr:Q", title="Pearson r", format=".2f")
                ],
            )
            .properties(
                width=400,   # ขยายตามจำนวนประเภท
                height=400,
                title="Pearson Correlation: District Quality Metrics × Problem Types"
            )
        )

        st.altair_chart(heatmap, use_container_width=True)


# -----------------------------
# 9) Pearson Heatmap: Problem Type vs Problem Type
# -----------------------------

st.markdown("---")
st.subheader("🔥 Pearson Heatmap – ความสัมพันธ์ระหว่าง 'ประเภทปัญหา' ด้วยกันเอง")

# เลือกรูปแบบการแสดงผล: Full / Upper / Lower
triangle_mode = st.sidebar.selectbox(
    "แสดง Heatmap ความสัมพันธ์ระหว่างประเภทปัญหาแบบ:",
    ["Full Matrix", "Upper Triangle", "Lower Triangle"],
    index=2,
    key="problem_corr_triangle_mode"
)

# ใช้ข้อมูลตามช่วงเวลา (filtered_time ยังไม่ filter ตาม type_filter)
corr_problem = filtered_time.copy()

# ไม่เอา NaN / ช่องว่างใน type_clean
corr_problem = corr_problem.dropna(subset=["type_clean"])
corr_problem = corr_problem[
    corr_problem["type_clean"].astype(str).str.strip() != ""
]

if corr_problem.empty:
    st.info("ไม่มีข้อมูลประเภทปัญหาหลังตัด NaN / ค่าว่างออก จึงยังทำ Pearson heatmap (ปัญหากับปัญหา) ไม่ได้")
elif "district" not in corr_problem.columns:
    st.error("ไม่พบคอลัมน์ 'district' ใน cleansed_data.csv (ต้องมี district เพื่อทำ heatmap ปัญหากับปัญหา)")
else:
    # 1) นับจำนวนร้องเรียนต่อ (เขต, ประเภทปัญหา)
    type_district_counts = (
        corr_problem
        .groupby(["district", "type_clean"])
        .size()
        .reset_index(name="complaints")
    )

    # 2) Pivot: แถว = district, คอลัมน์ = type_clean, ค่า = จำนวนเรื่องร้องเรียน
    pivot_problems = (
        type_district_counts
        .pivot(index="district", columns="type_clean", values="complaints")
        .fillna(0)
    )

    if pivot_problems.shape[1] < 2:
        st.info("จำนวนประเภทปัญหาน้อยเกินไป (< 2) สำหรับทำ correlation ปัญหากับปัญหา")
    else:
        # 3) คำนวณ Pearson correlation ระหว่างประเภทปัญหาทั้งหมด
        corr_matrix_prob = pivot_problems.corr(method="pearson")

        # 4) แปลงเป็น long format
        corr_prob_long = (
            corr_matrix_prob
            .reset_index()
            .melt(id_vars="type_clean", var_name="problem_type_2", value_name="corr")
            .rename(columns={"type_clean": "problem_type_1"})
        )

        # สร้าง index mapping สำหรับ upper/lower triangle
        problem_list = list(corr_matrix_prob.index)
        index_map = {p: i for i, p in enumerate(problem_list)}

        corr_prob_long["i_idx"] = corr_prob_long["problem_type_1"].map(index_map)
        corr_prob_long["j_idx"] = corr_prob_long["problem_type_2"].map(index_map)

        # 5) เลือกว่าจะใช้ Full / Upper / Lower
        if triangle_mode == "Upper Triangle":
            corr_filtered = corr_prob_long[corr_prob_long["i_idx"] < corr_prob_long["j_idx"]]
            title_suffix = " (Upper Triangle)"
        elif triangle_mode == "Lower Triangle":
            corr_filtered = corr_prob_long[corr_prob_long["i_idx"] > corr_prob_long["j_idx"]]
            title_suffix = " (Lower Triangle)"
        else:
            corr_filtered = corr_prob_long
            title_suffix = " (Full Matrix)"

        # 6) วาด heatmap
        heatmap_prob = (
            alt.Chart(corr_filtered)
            .mark_rect()
            .encode(
                x=alt.X(
                    "problem_type_2:N",
                    title="ประเภทปัญหา (ตัวแปรที่ 2)",
                    sort=problem_list
                ),
                y=alt.Y(
                    "problem_type_1:N",
                    title="ประเภทปัญหา (ตัวแปรที่ 1)",
                    sort=problem_list
                ),
                color=alt.Color(
                    "corr:Q",
                    title="Pearson r",
                    scale=alt.Scale(scheme="redblue", domain=[-1, 0, 1])
                ),
                tooltip=[
                    "problem_type_1:N",
                    "problem_type_2:N",
                    alt.Tooltip("corr:Q", title="Pearson r", format=".2f")
                ]
            )
            .properties(
                width=40 * max(6, len(problem_list)),
                height=40 * max(6, len(problem_list)),
                title=f"Pearson Correlation: Problem Type × Problem Type{title_suffix}"
            )
        )

        st.altair_chart(heatmap_prob, use_container_width=True)

        st.markdown("#### 📋 ตารางค่า Pearson r ระหว่างประเภทปัญหาด้วยกันเอง (Full Matrix)")
        st.dataframe(corr_matrix_prob.round(2))


       