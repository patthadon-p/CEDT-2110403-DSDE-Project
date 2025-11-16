# Setting up the environment
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import necessary modules
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.pipeline import Pipeline

from .CoordinateTransformer import CoordinateTransformer
from .DistrictSubdistrictTransformer import DistrictSubdistrictTransformer

# Other Transformer
from .ProvinceTransformer import ProvinceTransformer


class AddressTransformer(BaseEstimator, TransformerMixin):
    def __init__(
        self,
        province_path="",
        bangkok_area_path="",
        geographic_data_path="",
        coords_column=None,
        province_column=None,
        district_column=None,
        subdistrict_column=None,
        geo_district_column=None,
        geo_subdistrict_column=None,
    ):
        self.province_path = province_path
        self.bangkok_area_path = bangkok_area_path
        self.geographic_data_path = geographic_data_path

        self.coords_column = coords_column

        self.province_column = province_column
        self.district_column = district_column
        self.subdistrict_column = subdistrict_column
        self.geo_district_column = geo_district_column
        self.geo_subdistrict_column = geo_subdistrict_column

        self.province_transformer = ProvinceTransformer(
            path=self.province_path,
            province_column=self.province_column,
        )

        self.districtsubdistrict_transformer = DistrictSubdistrictTransformer(
            path=self.bangkok_area_path,
            district_column=self.district_column,
            subdistrict_column=self.subdistrict_column,
        )

        self.coordinate_transformer = CoordinateTransformer(
            path=self.geographic_data_path,
            coords_column=self.coords_column,
            district_column=self.district_column,
            subdistrict_column=self.subdistrict_column,
            geo_district_column=self.geo_district_column,
            geo_subdistrict_column=self.geo_subdistrict_column,
        )

    def fit(self, X, y=None):
        return self

    def transform(self, X):
        df = X.copy()

        address_transformer = Pipeline(
            steps=[
                ("province_transformer", self.province_transformer),
                ("area_transformer", self.districtsubdistrict_transformer),
                ("coordinate_transformer", self.coordinate_transformer),
            ],
        )

        df_transformed = address_transformer.fit_transform(df)
        return df_transformed
