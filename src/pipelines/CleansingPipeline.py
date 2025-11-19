# Setting up the environment
import os
import sys

import pandas as pd

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import necessary modules
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.pipeline import Pipeline

# Other Transformer
from .AddressTransformer import AddressTransformer
from .DateTransformer import DateTransformer
from .IngestionPreprocessor import IngestionPreprocessor
from .StateToStatusTransformer import StateToStatusTransformer


class CleansingPipeline(BaseEstimator, TransformerMixin):
    def __init__(
        self,
        ingest_path: str = "",
        province_path: str = "",
        bangkok_area_path: str = "",
        geographic_data_path: str = "",
        state_mapping_path: str = "",
        drop_columns: list[str] | None = None,
        drop_na_columns: list[str] | None = None,
        coords_column: str | None = None,
        province_column: str | None = None,
        district_column: str | None = None,
        subdistrict_column: str | None = None,
        geo_district_column: str | None = None,
        geo_subdistrict_column: str | None = None,
        date_columns: list[str] | None = None,
        state_mapping: dict | None = None,
        old_state_column: str | None = None,
        new_state_column: str | None = None,
    ) -> None:
        self.ingest_path = ingest_path
        self.province_path = province_path
        self.bangkok_area_path = bangkok_area_path
        self.geographic_data_path = geographic_data_path
        self.state_mapping_path = state_mapping_path

        self.drop_columns = drop_columns
        self.drop_na_columns = drop_na_columns

        self.coords_column = coords_column

        self.province_column = province_column
        self.district_column = district_column
        self.subdistrict_column = subdistrict_column
        self.geo_district_column = geo_district_column
        self.geo_subdistrict_column = geo_subdistrict_column

        self.date_columns = date_columns

        self.state_mapping = state_mapping
        self.old_state_column = old_state_column
        self.new_state_column = new_state_column

        self.ingest_pre_processor = IngestionPreprocessor(
            filepath=self.ingest_path,
            drop_columns=self.drop_columns,
            drop_na_columns=self.drop_na_columns,
        )

        self.date_transformer = DateTransformer(
            columns=self.date_columns,
        )

        self.address_transformer = AddressTransformer(
            province_path=self.province_path,
            bangkok_area_path=self.bangkok_area_path,
            geographic_data_path=self.geographic_data_path,
            coords_column=self.coords_column,
            province_column=self.province_column,
            district_column=self.district_column,
            subdistrict_column=self.subdistrict_column,
            geo_district_column=self.geo_district_column,
            geo_subdistrict_column=self.geo_subdistrict_column,
        )

        self.state_to_status_transformer = StateToStatusTransformer(
            path=self.state_mapping_path,
            mapping=self.state_mapping,
            old_column=self.old_state_column,
            new_column=self.new_state_column,
        )

    def fit(self, X: pd.DataFrame, y: pd.Series | None = None) -> "CleansingPipeline":
        return self

    def transform(self, X: pd.DataFrame) -> pd.DataFrame:
        df = X.copy()

        cleansing_pipeline = Pipeline(
            steps=[
                ("ingest_pre_processor", self.ingest_pre_processor),
                ("date_transformer", self.date_transformer),
                ("address_transformer", self.address_transformer),
                ("status_transformer", self.state_to_status_transformer),
            ],
        )

        df_transformed = pd.DataFrame(cleansing_pipeline.fit_transform(df))
        df_transformed = df_transformed.dropna()

        return df_transformed
