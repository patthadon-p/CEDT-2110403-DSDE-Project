"""
Coordinate transformation and spatial validation utilities.

This module provides the CoordinateTransformer class, a Scikit-learn-compatible
transformer that performs spatial joining to validate if a data point's
coordinates fall within the reported administrative region (district/subdistrict).
This is crucial for data cleansing in geographic data science projects.

Classes
-------
CoordinateTransformer
    A transformer that extracts coordinates, performs a spatial join with
    geographic boundary data, and filters data points based on geometric
    and textual address consistency.
"""

# Import necessary modules
import geopandas as gpd
import pandas as pd
from sklearn.base import BaseEstimator, TransformerMixin

# Utility functions
from src.utils.GeographicUtils import load_geographic_data, save_geographic_data

# Other Transformer
from .DistrictSubdistrictTransformer import DistrictSubdistrictTransformer


class CoordinateTransformer(BaseEstimator, TransformerMixin):
    """
    Validates data points by checking if their coordinates fall within the
    claimed administrative boundaries.

    This transformer performs three main tasks:
    1. Extracts longitude and latitude from a combined coordinate string column.
    2. Performs a **spatial join**  between the data points and pre-loaded
        geographic region boundaries (`bangkok_gdf`).
    3. Filters the results to include only records where the spatially derived
        district/subdistrict matches the original text-based district/subdistrict columns.

    Parameters
    ----------
    path : str, optional
        File path to the geographic boundary data (e.g., GeoJSON, Shapefile),
        passed to `load_geographic_data`. Default is "".
    coords_column : str or None, optional
        Name of the column containing coordinate strings (e.g., "lat,lon").
        Defaults to "coords".
    district_column : str or None, optional
        Name of the input column containing the text-based district name.
        Defaults to "district".
    subdistrict_column : str or None, optional
        Name of the input column containing the text-based subdistrict name.
        Defaults to "subdistrict".
    geo_district_column : str or None, optional
        Name of the district column in the geographic boundary data (`bangkok_gdf`).
        Defaults to "DISTRICT_N".
    geo_subdistrict_column : str or None, optional
        Name of the subdistrict column in the geographic boundary data (`bangkok_gdf`).
        Defaults to "SUBDISTR_1".
    cutoff : int or None, optional
        The fuzzy matching cutoff score used when cleaning geographic names in the GeoDataFrame.
        Defaults to 60.
    prefix_bonus : bool or None, optional
        Whether to apply a bonus score for common prefixes during fuzzy matching in the GeoDataFrame cleaning.
        Defaults to True.

    Attributes
    ----------
    bangkok_gdf : geopandas.GeoDataFrame
        The pre-processed geographic boundary data used for spatial joining.
        **This GeoDataFrame is cleaned by `DistrictSubdistrictTransformer` upon initialization.**
    path : str
        The file path used to load the geographic boundary data.
    coords_column : str
        The final column name used for coordinate string input (e.g., "coords").
    district_column : str
        The final column name used for the input text-based district name.
    subdistrict_column : str
        The final column name used for the input text-based subdistrict name.
    geo_district_column : str
        The final column name for the district column in the geographic boundary data.
    geo_subdistrict_column : str
        The final column name for the subdistrict column in the geographic boundary data.
    cutoff : int
        The fuzzy matching cutoff score used.
    prefix_bonus : bool
        The status of the prefix bonus setting used for cleaning the GeoDataFrame.
    """

    def __init__(
        self,
        path: str = "",
        coords_column: str | None = None,
        district_column: str | None = None,
        subdistrict_column: str | None = None,
        geo_district_column: str | None = None,
        geo_subdistrict_column: str | None = None,
        cutoff: int | None = None,
        prefix_bonus: bool | None = None,
    ) -> None:
        """
        Initializes the transformer by loading and cleaning the geographic boundary data.

        The geographic boundary data is cleaned using `DistrictSubdistrictTransformer`
        and then saved locally before being stored in `self.bangkok_gdf`.

        Parameters
        ----------
        path : str, optional
            File path to the geographic boundary data. Default is "".
        coords_column : str or None, optional
            Name of the column containing coordinate strings. Defaults to "coords".
        district_column : str or None, optional
            Name of the input column containing the text-based district name. Defaults to "district".
        subdistrict_column : str or None, optional
            Name of the input column containing the text-based subdistrict name. Defaults to "subdistrict".
        geo_district_column : str or None, optional
            Name of the district column in the geographic boundary data. Defaults to "DISTRICT_N".
        geo_subdistrict_column : str or None, optional
            Name of the subdistrict column in the geographic boundary data. Defaults to "SUBDISTR_1".
        cutoff : int or None, optional
            The fuzzy matching cutoff score used when cleaning geographic names in the GeoDataFrame.
            Defaults to 60.
        prefix_bonus : bool or None, optional
            Whether to apply a bonus score for common prefixes during fuzzy matching in the GeoDataFrame cleaning.
            Defaults to True.
        """

        self.path = path

        self.coords_column = coords_column or "coords"

        self.district_column = district_column or "district"
        self.subdistrict_column = subdistrict_column or "subdistrict"

        self.geo_district_column = geo_district_column or "DISTRICT_N"
        self.geo_subdistrict_column = geo_subdistrict_column or "SUBDISTR_1"

        self.cutoff = cutoff or 60
        self.prefix_bonus = prefix_bonus if prefix_bonus is not None else True

        dst = DistrictSubdistrictTransformer(
            district_column=self.geo_district_column,
            subdistrict_column=self.geo_subdistrict_column,
            cutoff=self.cutoff,
            prefix_bonus=self.prefix_bonus,
        )

        self.bangkok_gdf = gpd.GeoDataFrame(
            dst.fit_transform(load_geographic_data(self.path))
        )

        save_geographic_data(self.bangkok_gdf)

    def fit(
        self, X: pd.DataFrame, y: pd.Series | None = None
    ) -> "CoordinateTransformer":
        """
        The fit method does nothing for this transformer, as it performs
        stateless, pure transformation logic using a pre-loaded GeoDataFrame.

        Parameters
        ----------
        X : pandas.DataFrame
            The input data (not used for fitting).
        y : array-like of shape (n_samples,), default=None
            Target values (not used).

        Returns
        -------
        CoordinateTransformer
            The fitted transformer (self).
        """

        return self

    def transform(self, X: pd.DataFrame) -> pd.DataFrame:
        """
        Performs coordinate extraction, spatial join, and filtering to validate
        data points against geographic boundaries.

        Parameters
        ----------
        X : pandas.DataFrame
            The input DataFrame containing the coordinate and address columns.

        Returns
        -------
        pandas.DataFrame
            The transformed DataFrame containing only the data points that
            are geometrically and textually consistent with the geographic
            boundary data.
        """

        def coords_check(row: dict) -> bool:
            """
            Internal helper function to check if the spatially derived
            district/subdistrict matches the original text columns.
            """

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
