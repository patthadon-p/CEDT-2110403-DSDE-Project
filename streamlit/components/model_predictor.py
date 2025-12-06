# External dependencies
import os
import sys
from datetime import date

import streamlit as st

# Project modules
from components.data_loader import load_and_process_predictor_data, load_geo_data
from components.utils import find_location_from_coords

# Spark dependencies
from pyspark.ml import Model
from pyspark.ml.feature import CountVectorizerModel, FeatureHasher, VectorAssembler
from pyspark.ml.linalg import VectorUDT
from pyspark.ml.tuning import CrossValidatorModel
from pyspark.sql import DataFrame, SparkSession
from pyspark.sql.types import IntegerType, StructField, StructType

# Ensure project root is in sys.path for imports
current_file = os.path.abspath(__file__)
project_root = os.path.abspath(os.path.join(current_file, "../../../"))

if project_root not in sys.path:
    sys.path.append(project_root)

from src.utils import create_spark_session, read_config_path


@st.cache_resource
def load_spark_and_models() -> (
    tuple[SparkSession, Model, dict[str, CountVectorizerModel], FeatureHasher]
):
    spark, _ = create_spark_session(app_name="TraffyTimePredictorPage")

    model = CrossValidatorModel.load(
        read_config_path(domain="model", key="best_model_path")
    ).bestModel

    encoding_model = {
        "type": CountVectorizerModel.load(
            read_config_path(domain="model", key="type_vectorizer_path")
        ),
        "organization": CountVectorizerModel.load(
            read_config_path(domain="model", key="organization_vectorizer_path")
        ),
    }

    hasher = FeatureHasher(
        inputCols=["district", "subdistrict"],
        outputCol="address_encoded",
        numFeatures=2048,
    )

    return spark, model, encoding_model, hasher


class TraffyTimePredictor:

    def __init__(self) -> None:
        self.d_map, self.p_types, self.orgs = load_and_process_predictor_data()

        # Create Spark session and load models
        self.spark, self.model, self.encoding_model, self.hasher = (
            load_spark_and_models()
        )

        self.schema = StructType(
            [
                StructField("timestamp_month", IntegerType()),
                StructField("timestamp_year", IntegerType()),
                StructField("address_encoded", VectorUDT()),
                StructField("latlong_encoded", VectorUDT()),
                StructField("organization_encoded", VectorUDT()),
                StructField("type_encoded", VectorUDT()),
            ]
        )

    def prepare_features(
        self,
        district: str,
        subdistrict: str,
        types: list[str],
        orgs: list[str],
        date: date,
        lat: float,
        long: float,
    ) -> DataFrame:
        tm = int(date.month)
        ty = int(date.year)

        df_cate = self.spark.createDataFrame(
            [(types, orgs)],
            ["type", "organization"],
        )

        for column, model in self.encoding_model.items():
            df_cate = model.transform(df_cate)
            df_cate = df_cate.withColumnRenamed("features", f"{column}_encoded")

        category_row = df_cate.first()

        df_addr = self.spark.createDataFrame(
            [(district, subdistrict)],
            ["district", "subdistrict"],
        )

        df_addr_hashed = self.hasher.transform(df_addr)
        address_row = df_addr_hashed.first()

        latlong_vec = VectorAssembler(
            inputCols=["lat", "long"], outputCol="latlong_encoded"
        )

        latlong_df = self.spark.createDataFrame(
            [(float(lat), float(long))],
            ["lat", "long"],
        )

        latlong_transformed = latlong_vec.transform(latlong_df)
        latlong_row = latlong_transformed.first()

        if (category_row is None) or (address_row is None) or (latlong_row is None):
            raise ValueError("DataFrame transformation resulted in empty dataset")

        feature_df = self.spark.createDataFrame(
            [
                (
                    int(tm),
                    int(ty),
                    address_row.address_encoded,
                    latlong_row.latlong_encoded,
                    category_row.organization_encoded,
                    category_row.type_encoded,
                )
            ],
            schema=self.schema,
        )

        return feature_df

    def predict(self, model_input: DataFrame) -> tuple[float, str]:
        prediction = self.model.transform(model_input)
        pred_value = prediction.select("prediction").collect()[0][0]

        lvl = (
            "Fast (เร็ว)"
            if pred_value < 3
            else "Normal (ปกติ)" if pred_value < 10 else "Slow (ช้า)"
        )
        return round(pred_value, 1), lvl


# --- State Management & Callbacks (Time Predictor - From Second Block) ---


def handle_pending_updates() -> None:
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


def clear_coordinates() -> None:
    st.session_state["confirmed_lat"] = None
    st.session_state["confirmed_long"] = None
    st.session_state["location_source"] = None
    st.session_state["geo_match_found"] = None

    # Reset Dropdowns to default
    st.session_state["sb_district"] = "--- Select District ---"
    st.session_state["sb_subdistrict"] = None
