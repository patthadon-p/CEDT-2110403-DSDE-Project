"""
Address data transformation pipeline utilities.

This module provides the core AddressTransformer class, which acts as a
meta-transformer. It wraps a Scikit-learn Pipeline to sequentially apply
multiple specialized transformers (ProvinceTransformer, DistrictSubdistrictTransformer,
and CoordinateTransformer) for standardizing and enriching address-related fields
in a dataset.

Classes
-------
AddressTransformer
    A meta-transformer that orchestrates the sequential cleaning and enrichment
    of geographic and address columns.
"""

# Import necessary modules
import pandas as pd
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.pipeline import Pipeline

# Other Transformer
from .CoordinateTransformer import CoordinateTransformer
from .DistrictSubdistrictTransformer import DistrictSubdistrictTransformer
from .ProvinceTransformer import ProvinceTransformer


class AddressTransformer(BaseEstimator, TransformerMixin):
    """
    A meta-transformer that applies a sequence of address-related transformations.

    This class combines several specialized transformers (for province names,
    district/subdistrict names, and coordinate validation/enrichment) into a
    single, coherent pipeline step.

    Parameters
    ----------
    province_path : str, optional
        File path for the province name whitelist/mapping. Default is "".
    bangkok_area_path : str, optional
        File path for the Bangkok official area name mapping. Default is "".
    geographic_data_path : str, optional
        File path for the geographic data (GeoDataFrame) used for spatial joins.
        Default is "".
    coords_column : str or None, optional
        Name of the column containing coordinates (e.g., 'latitude_longitude').
        Default is None.
    province_column : str or None, optional
        Name of the column containing province names. Default is None.
    district_column : str or None, optional
        Name of the column containing district names. Default is None.
    subdistrict_column : str or None, optional
        Name of the column containing subdistrict names. Default is None.
    geo_district_column : str or None, optional
        Name of the column for the enriched district name from spatial join.
        Default is None.
    geo_subdistrict_column : str or None, optional
        Name of the column for the enriched subdistrict name from spatial join.
        Default is None.

    Attributes
    ----------
    province_transformer : ProvinceTransformer
        The instantiated transformer for standardizing province names.
    districtsubdistrict_transformer : DistrictSubdistrictTransformer
        The instantiated transformer for normalizing district/subdistrict names.
    coordinate_transformer : CoordinateTransformer
        The instantiated transformer for coordinate-based spatial enrichment.

    See Also
    --------
    sklearn.pipeline.Pipeline : The underlying mechanism used for sequential transformation.
    """

    def __init__(
        self,
        province_path: str = "",
        bangkok_area_path: str = "",
        geographic_data_path: str = "",
        coords_column: str | None = None,
        province_column: str | None = None,
        district_column: str | None = None,
        subdistrict_column: str | None = None,
        geo_district_column: str | None = None,
        geo_subdistrict_column: str | None = None,
    ) -> None:
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

    def fit(self, X: pd.DataFrame, y: pd.Series | None = None) -> "AddressTransformer":
        """
        Does nothing, as this transformer relies on its sub-transformers,
        which typically do not require fitting.

        Parameters
        ----------
        X : pandas.DataFrame
            The input data.
        y : array-like of shape (n_samples,), default=None
            Target values (not used).

        Returns
        -------
        AddressTransformer
            The fitted transformer (self).
        """

        return self

    def transform(self, X: pd.DataFrame) -> pd.DataFrame:
        """
        Applies the sequential transformation pipeline to the input DataFrame.

        Parameters
        ----------
        X : pandas.DataFrame
            The input DataFrame containing address-related columns.

        Returns
        -------
        pandas.DataFrame
            The transformed DataFrame with cleaned and enriched address columns.
        """

        df = X.copy()

        address_transformer = Pipeline(
            steps=[
                ("province_transformer", self.province_transformer),
                ("area_transformer", self.districtsubdistrict_transformer),
                ("coordinate_transformer", self.coordinate_transformer),
            ],
        )

        df_transformed = pd.DataFrame(address_transformer.fit_transform(df))
        return df_transformed
