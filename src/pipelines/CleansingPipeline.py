# Setting up the environment
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import necessary modules
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.pipeline import Pipeline

# Other Transformer
from .AddressTransformer import AddressTransformer
from .DateTransformer import DateTransformer
from .StateToStatusTransformer import StateToStatusTransformer


class CleansingPipeline(BaseEstimator, TransformerMixin):
    def __init__(
        self,
        province_path="",
        bangkok_area_path="",
        geographic_data_path="",
        state_mapping_path="",
        coords_column=None,
        province_column=None,
        district_column=None,
        subdistrict_column=None,
        geo_district_column=None,
        geo_subdistrict_column=None,
        date_columns=None,
        state_mapping=None,
        old_state_column=None,
        new_state_column=None,
    ):
        self.province_path = province_path
        self.bangkok_area_path = bangkok_area_path
        self.geographic_data_path = geographic_data_path
        self.state_mapping_path = state_mapping_path

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

    def fit(self, X, y=None):
        return self

    def transform(self, X):
        df = X.copy()

        cleansing_pipeline = Pipeline(
            steps=[
                ("date_transformer", self.date_transformer),
                ("address_transformer", self.address_transformer),
                ("status_transformer", self.state_to_status_transformer),
            ],
        )

        df_transformed = cleansing_pipeline.fit_transform(df)
        return df_transformed
