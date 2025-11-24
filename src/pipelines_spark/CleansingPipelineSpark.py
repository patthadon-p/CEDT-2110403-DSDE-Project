"""
PySpark Transformer for Comprehensive Data Cleansing Pipeline.

This module defines the high-level CleansingPipelineSpark class, which serves as
the primary entry point for pre-processing raw data in a Spark environment.
It orchestrates a sequence of specialized Spark transformers for ingestion
cleanup, date standardization, address enrichment, and status mapping to
ensure data quality and readiness for model consumption.

Classes
-------
CleansingPipelineSpark
    A PySpark meta-transformer that combines and sequentially executes all
    necessary data cleaning and feature engineering steps.
"""

# Import necessary modules
from pyspark.ml import Transformer
from pyspark.sql import DataFrame, SparkSession

# Other Transformer
from .AddressTransformerSpark import AddressTransformerSpark
from .DateTransformerSpark import DateTransformerSpark
from .IngestionPreprocessorSpark import IngestionPreprocessorSpark
from .StateToStatusTransformerSpark import StateToStatusTransformerSpark


class CleansingPipelineSpark(Transformer):
    """
    The main PySpark meta-transformer for comprehensive data cleansing and feature standardization.

    This class wraps a sequence of PySpark Transformers to apply several crucial
    data preparation steps sequentially on a Spark DataFrame, ensuring consistency
    across different data types (dates, addresses, status flags).

    The transformation steps executed in order are:
    1. **Ingestion Preprocessor:** Renames/drops columns and filters rows based on NaN values.
    2. **Date Transformer:** Converts date columns to date types and extracts date features.
    3. **Address Transformer:** Cleans province names, validates/standardizes addresses, and performs spatial enrichment.
    4. **State to Status Transformer:** Maps raw state values to standardized status codes.
    5. **Final Dropping:** Drops remaining rows containing null/NaN values.

    Parameters
    ----------
    spark : pyspark.sql.SparkSession
        The active SparkSession instance.
    sedona : pyspark.sql.SparkSession
        The active Sedona (Apache Sedona/GeoSpark) enabled SparkSession instance.
    ingest_path : str, optional
        File path for the JSON containing ingestion settings (rename/drop columns). Default is "".
    province_path : str, optional
        File path for the province name whitelist/mapping. Default is "".
    bangkok_area_path : str, optional
        File path for the Bangkok official area name mapping. Default is "".
    geographic_data_path : str, optional
        File path for the geographic data used for spatial joins. Default is "".
    state_mapping_path : str, optional
        File path for the JSON containing the state-to-status mapping. Default is "".
    drop_columns : list of str or None, optional
        List of columns to be dropped, passed to IngestionPreprocessorSpark. Default is None.
    drop_na_columns : list of str or None, optional
        List of columns whose rows must not contain NaN/null values, passed to IngestionPreprocessorSpark. Default is None.
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
    cutoff_district_subdistrict : int or None, optional
        Fuzzy matching cutoff score for DistrictSubdistrictTransformerSpark. Default is None.
    cutoff_coordinate : int or None, optional
        Fuzzy matching cutoff score for CoordinateTransformerSpark. Default is None.
    prefix_bonus_district_subdistrict : bool, optional
        Prefix matching bonus setting for DistrictSubdistrictTransformerSpark. Default is False.
    prefix_bonus_coordinate : bool, optional
        Prefix matching bonus setting for CoordinateTransformerSpark. Default is True.
    start_time_column : str or None, optional
        Name of the column containing the event start time. Default is None.
    end_time_column : str or None, optional
        Name of the column containing the event end time/resolution time. Default is None.
    state_mapping : dict or None, optional
        Direct mapping dictionary for state-to-status mapping. Default is None.
    old_state_column : str or None, optional
        Name of the column containing the raw state values. Default is None.
    new_state_column : str or None, optional
        Name of the output column for the standardized status values. Default is None.

    Attributes
    ----------
    ingest_pre_processor : IngestionPreprocessorSpark
        Instantiated transformer for initial column cleanup and row filtering.
    date_transformer : DateTransformerSpark
        Instantiated transformer for date standardization and feature extraction.
    address_transformer : AddressTransformerSpark
        Instantiated transformer for address cleanup and geographic enrichment.
    state_to_status_transformer : StateToStatusTransformerSpark
        Instantiated transformer for mapping state values to standard statuses.
    """
    
    def __init__(
        self,
        spark: SparkSession,
        sedona: SparkSession,
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
        cutoff_district_subdistrict: int | None = None,
        cutoff_coordinate: int | None = None,
        prefix_bonus_district_subdistrict: bool = False,
        prefix_bonus_coordinate: bool = True,
        start_time_column: str | None = None,
        end_time_column: str | None = None,
        state_mapping: dict | None = None,
        old_state_column: str | None = None,
        new_state_column: str | None = None,
    ) -> None:
        """
        Initializes the PySpark Cleansing Pipeline by instantiating all necessary sub-transformers.

        Parameters
        ----------
        spark : pyspark.sql.SparkSession
            The active SparkSession instance.
        sedona : pyspark.sql.SparkSession
            The active Sedona (Apache Sedona/GeoSpark) enabled SparkSession instance.
        ingest_path : str, optional
            File path for the JSON containing ingestion settings (rename/drop columns). Default is "".
        province_path : str, optional
            File path for the province name whitelist/mapping. Default is "".
        bangkok_area_path : str, optional
            File path for the Bangkok official area name mapping. Default is "".
        geographic_data_path : str, optional
            File path for the geographic data used for spatial joins. Default is "".
        state_mapping_path : str, optional
            File path for the JSON containing the state-to-status mapping. Default is "".
        drop_columns : list of str or None, optional
            List of columns to be dropped, passed to IngestionPreprocessorSpark. Default is None.
        drop_na_columns : list of str or None, optional
            List of columns whose rows must not contain NaN/null values, passed to IngestionPreprocessorSpark. Default is None.
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
        cutoff_district_subdistrict : int or None, optional
            Fuzzy matching cutoff score for DistrictSubdistrictTransformerSpark. Default is None.
        cutoff_coordinate : int or None, optional
            Fuzzy matching cutoff score for CoordinateTransformerSpark. Default is None.
        prefix_bonus_district_subdistrict : bool, optional
            Prefix matching bonus setting for DistrictSubdistrictTransformerSpark. Default is False.
        prefix_bonus_coordinate : bool, optional
            Prefix matching bonus setting for CoordinateTransformerSpark. Default is True.
        start_time_column : str or None, optional
            Name of the column containing the event start time. Default is None.
        end_time_column : str or None, optional
            Name of the column containing the event end time/resolution time. Default is None.
        state_mapping : dict or None, optional
            Direct mapping dictionary for state-to-status mapping. Default is None.
        old_state_column : str or None, optional
            Name of the column containing the raw state values. Default is None.
        new_state_column : str or None, optional
            Name of the output column for the standardized status values. Default is None.
        """
        
        self.spark = spark
        self.sedona = sedona

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

        self.cutoff_district_subdistrict = cutoff_district_subdistrict
        self.cutoff_coordinate = cutoff_coordinate

        self.prefix_bonus_district_subdistrict = prefix_bonus_district_subdistrict
        self.prefix_bonus_coordinate = prefix_bonus_coordinate

        self.start_time_column = start_time_column
        self.end_time_column = end_time_column

        self.state_mapping = state_mapping
        self.old_state_column = old_state_column
        self.new_state_column = new_state_column

        self.ingest_pre_processor = IngestionPreprocessorSpark(
            filepath=self.ingest_path,
            drop_columns=self.drop_columns,
            drop_na_columns=self.drop_na_columns,
        )

        self.date_transformer = DateTransformerSpark(
            start_time_column=self.start_time_column,
            end_time_column=self.end_time_column,
        )

        self.address_transformer = AddressTransformerSpark(
            spark=self.spark,
            sedona=self.sedona,
            province_path=self.province_path,
            bangkok_area_path=self.bangkok_area_path,
            geographic_data_path=self.geographic_data_path,
            coords_column=self.coords_column,
            province_column=self.province_column,
            district_column=self.district_column,
            subdistrict_column=self.subdistrict_column,
            geo_district_column=self.geo_district_column,
            geo_subdistrict_column=self.geo_subdistrict_column,
            cutoff_district_subdistrict=self.cutoff_district_subdistrict,
            cutoff_coordinate=self.cutoff_coordinate,
            prefix_bonus_district_subdistrict=self.prefix_bonus_district_subdistrict,
            prefix_bonus_coordinate=self.prefix_bonus_coordinate,
        )

        self.state_to_status_transformer = StateToStatusTransformerSpark(
            spark=self.spark,
            path=self.state_mapping_path,
            mapping=self.state_mapping,
            old_column=self.old_state_column,
            new_column=self.new_state_column,
        )

    def _transform(self, df: DataFrame) -> DataFrame:
        """
        Sequentially applies data cleansing and enrichment steps to the input DataFrame.

        The method executes the transformation steps in order:
        Ingestion -> Date -> Address -> Status, followed by dropping all remaining null/NaN rows.

        Parameters
        ----------
        df : pyspark.sql.DataFrame
            The input DataFrame (raw data).

        Returns
        -------
        pyspark.sql.DataFrame
            The transformed and cleansed DataFrame with standardized features and
            missing rows removed.
        """
        
        df_transformed = self.ingest_pre_processor.transform(df)
        df_transformed = self.date_transformer.transform(df_transformed)
        df_transformed = self.address_transformer.transform(df_transformed)
        df_transformed = self.state_to_status_transformer.transform(df_transformed)

        df_transformed = df_transformed.dropna()

        return df_transformed
