# Setting up the environment
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import necessary modules
import geopandas as gpd
from sklearn.base import BaseEstimator, TransformerMixin

# Utility functions
from utils.GeographicUtils import load_geographic_data

# Other Transformer
from .DistrictSubdistrictTransformer import DistrictSubdistrictTransformer


class CoordinateTransformer(BaseEstimator, TransformerMixin):
    def __init__(
        self,
        path="",
        coords_column=None,
        district_column=None,
        subdistrict_column=None,
        geo_district_column=None,
        geo_subdistrict_column=None,
    ):
        self.path = path

        self.coords_column = coords_column or "coords"

        self.district_column = district_column or "district"
        self.subdistrict_column = subdistrict_column or "subdistrict"

        self.geo_district_column = geo_district_column or "DISTRICT_N"
        self.geo_subdistrict_column = geo_subdistrict_column or "SUBDISTR_1"

        dst = DistrictSubdistrictTransformer(
            district_column=self.geo_district_column,
            subdistrict_column=self.geo_subdistrict_column,
        )

        self.bangkok_gdf = gpd.GeoDataFrame(
            dst.fit_transform(load_geographic_data(self.path))
        )

    def fit(self, X, y=None):
        return self

    def transform(self, X):

        def coords_check(row):
            district_points = row[self.district_column]
            subdistrict_points = row[self.subdistrict_column]

            district_region = row[self.geo_district_column]
            subdistrict_region = row[self.geo_subdistrict_column]

            check_district = district_region == district_points
            check_subdistrict = subdistrict_region == subdistrict_points
            return check_district and check_subdistrict

        df = X.copy()
        df[["longitude", "latitude"]] = (
            df[self.coords_column].str.split(",", expand=True).astype(float)
        )
        df = df.drop(columns=[self.coords_column])

        columns = df.columns.tolist()

        # Convert to geopandas
        points_gdf = gpd.GeoDataFrame(
            df, geometry=gpd.points_from_xy(df.longitude, df.latitude), crs="EPSG:4326"
        )

        # Spatial join to associate points with regions
        points_with_region = gpd.sjoin(
            points_gdf,
            self.bangkok_gdf,
            how="left",
            predicate="within",
        )

        coord_df = points_with_region[points_with_region.apply(coords_check, axis=1)]
        coord_df = coord_df.loc[:, columns]

        return coord_df
