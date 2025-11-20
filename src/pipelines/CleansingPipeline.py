"""
Main data cleansing and standardization pipeline utilities.

This module defines the high-level CleansingPipeline class, which serves as
the primary entry point for pre-processing raw data. It orchestrates a
sequence of specialized transformers for date standardization, address
enrichment, and status mapping to ensure data quality and readiness for
model consumption.

Classes
-------
CleansingPipeline
    A meta-transformer that combines and sequentially executes all necessary
    data cleaning and feature engineering steps.
"""

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
    """
    The main meta-transformer for comprehensive data cleansing and feature standardization.

    This class wraps a Scikit-learn Pipeline to apply several crucial
    data preparation steps sequentially, ensuring consistency across
    different data types (dates, addresses, status flags).

    Parameters
    ----------
    # --- Ingestion Preprocessor Parameters ---
    ingest_path : str, optional
        File path for the JSON containing ingestion settings (rename/drop columns) for IngestionPreprocessor. Default is "".
    drop_columns : list of str or None, optional
        List of columns to be dropped, passed to IngestionPreprocessor. Default is None.
    drop_na_columns : list of str or None, optional
        List of columns whose rows must not contain NaN/null values, passed to IngestionPreprocessor. Default is None.

    # --- Utility File Paths (Passed to Sub-Transformers) ---
    province_path : str, optional
        File path for the province name whitelist/mapping, passed to AddressTransformer. Default is "".
    bangkok_area_path : str, optional
        File path for the Bangkok official area name mapping, passed to AddressTransformer. Default is "".
    geographic_data_path : str, optional
        File path for the geographic data (GeoDataFrame) used for spatial joins, passed to AddressTransformer. Default is "".
    state_mapping_path : str, optional
        File path for the JSON containing the state-to-status mapping, passed to StateToStatusTransformer. Default is "".

    # --- Column Names (Passed to AddressTransformer) ---
    coords_column : str or None, optional
        Name of the column containing coordinates. Default is None.
    province_column : str or None, optional
        Name of the column containing province names. Default is None.
    district_column : str or None, optional
        Name of the column containing district names. Default is None.
    subdistrict_column : str or None, optional
        Name of the column containing subdistrict names. Default is None.
    geo_district_column : str or None, optional
        Name of the column for the enriched district name from spatial join. Default is None.
    geo_subdistrict_column : str or None, optional
        Name of the column for the enriched subdistrict name from spatial join. Default is None.

    # --- Column Names (Passed to DateTransformer) ---
    date_columns : list of str or None, optional
        List of column names to be standardized as datetime objects. Default is None.

    # --- Status Mapping Parameters (Passed to StateToStatusTransformer) ---
    state_mapping : dict or None, optional
        Direct mapping dictionary (alternative to state_mapping_path). Default is None.
    old_state_column : str or None, optional
        Name of the column containing the raw state values. Default is None.
    new_state_column : str or None, optional
        Name of the output column for the standardized status values. Default is None.

    Attributes
    ----------
    ingest_pre_processor : IngestionPreprocessor
        Instantiated transformer for initial column cleanup and row filtering.
    date_transformer : DateTransformer
        Instantiated transformer for date standardization.
    address_transformer : AddressTransformer
        Instantiated transformer for address cleanup and enrichment.
    state_to_status_transformer : StateToStatusTransformer
        Instantiated transformer for mapping state values to standard statuses.

    See Also
    --------
    sklearn.pipeline.Pipeline : The underlying mechanism used for sequential transformation.
    .AddressTransformer.AddressTransformer : The sub-transformer for geographic data.
    """

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
        """
        Does nothing, as this meta-transformer relies on its sub-transformers
        which primarily handle pure transformation logic.

        Parameters
        ----------
        X : pandas.DataFrame
            The input data.
        y : array-like of shape (n_samples,), default=None
            Target values (not used).

        Returns
        -------
        CleansingPipeline
            The fitted transformer (self).
        """

        return self

    def transform(self, X: pd.DataFrame) -> pd.DataFrame:
        """
        Applies the sequential data cleansing and enrichment pipeline to the input DataFrame.

        Parameters
        ----------
        X : pandas.DataFrame
            The input DataFrame containing raw data.

        Returns
        -------
        pandas.DataFrame
            The transformed DataFrame with standardized dates, enriched addresses,
            and mapped status columns.
        """

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
