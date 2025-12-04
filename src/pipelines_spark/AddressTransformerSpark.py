"""
PySpark Transformer for Address Data Standardization and Enrichment.

This module provides the AddressTransformerSpark class, a PySpark ML meta-Transformer
that sequentially applies specialized transformers to clean, standardize, and
spatially enrich address-related columns (province, district, subdistrict, and coordinates)
in a Spark DataFrame.

Classes
-------
AddressTransformerSpark
    A PySpark meta-transformer that orchestrates the sequential cleaning and enrichment
    of geographic and address columns using specialized Spark Transformers.
"""

# Import necessary modules
from pyspark.ml import Transformer
from pyspark.sql import DataFrame, SparkSession

# Other Transformer
from .CoordinateTransformerSpark import CoordinateTransformerSpark
from .DistrictSubdistrictTransformerSpark import DistrictSubdistrictTransformerSpark
from .ProvinceTransformerSpark import ProvinceTransformerSpark


class AddressTransformerSpark(Transformer):
    """
    A PySpark meta-transformer that applies a sequence of address-related transformations.

    This class combines several specialized Spark Transformers (for province names,
    district/subdistrict names, and coordinate validation/enrichment) into a
    single, coherent pipeline step.

    The sequence of transformation is:
    1. Province name standardization (`ProvinceTransformerSpark`).
    2. District/Subdistrict name standardization (`DistrictSubdistrictTransformerSpark`).
    3. Coordinate validation and spatial enrichment (`CoordinateTransformerSpark`).

    Parameters
    ----------
    spark : pyspark.sql.SparkSession
        The active SparkSession instance.
    sedona : pyspark.sql.SparkSession
        The active Sedona (Apache Sedona/GeoSpark) enabled SparkSession instance.
    province_path : str, optional
        File path for the province name whitelist/mapping. Default is "".
    bangkok_area_path : str, optional
        File path for the Bangkok official area name mapping. Default is "".
    geographic_data_path : str, optional
        File path for the geographic data used for spatial joins. Default is "".
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
    prefix_bonus_district_subdistrict : bool or None, optional
        Prefix matching bonus setting for DistrictSubdistrictTransformerSpark. Default is None.
    prefix_bonus_coordinate : bool or None, optional
        Prefix matching bonus setting for CoordinateTransformerSpark. Default is None.

    Attributes
    ----------
    province_transformer : ProvinceTransformerSpark
        The instantiated transformer for standardizing province names.
    districtsubdistrict_transformer : DistrictSubdistrictTransformerSpark
        The instantiated transformer for normalizing district/subdistrict names.
    coordinate_transformer : CoordinateTransformerSpark
        The instantiated transformer for coordinate-based spatial enrichment.
    """

    def __init__(
        self,
        spark: SparkSession,
        sedona: SparkSession,
        province_path: str = "",
        bangkok_area_path: str = "",
        geographic_data_path: str = "",
        coords_column: str | None = None,
        province_column: str | None = None,
        district_column: str | None = None,
        subdistrict_column: str | None = None,
        geo_district_column: str | None = None,
        geo_subdistrict_column: str | None = None,
        cutoff_district_subdistrict: int | None = None,
        cutoff_coordinate: int | None = None,
        prefix_bonus_district_subdistrict: bool | None = None,
        prefix_bonus_coordinate: bool | None = None,
    ) -> None:
        """
        Initializes the PySpark Address Meta-Transformer by instantiating sub-transformers.

        Parameters
        ----------
        spark : pyspark.sql.SparkSession
            The active SparkSession instance.
        sedona : pyspark.sql.SparkSession
            The active Sedona (Apache Sedona/GeoSpark) enabled SparkSession instance.
        province_path : str, optional
            File path for the province name whitelist/mapping. Default is "".
        bangkok_area_path : str, optional
            File path for the Bangkok official area name mapping. Default is "".
        geographic_data_path : str, optional
            File path for the geographic data used for spatial joins. Default is "".
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
        prefix_bonus_district_subdistrict : bool or None, optional
            Prefix matching bonus setting for DistrictSubdistrictTransformerSpark. Default is None.
        prefix_bonus_coordinate : bool or None, optional
            Prefix matching bonus setting for CoordinateTransformerSpark. Default is None.
        """

        self.spark = spark
        self.sedona = sedona

        self.province_path = province_path
        self.bangkok_area_path = bangkok_area_path
        self.geographic_data_path = geographic_data_path

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

        self.province_transformer = ProvinceTransformerSpark(
            path=self.province_path,
            province_column=self.province_column,
        )

        self.districtsubdistrict_transformer = DistrictSubdistrictTransformerSpark(
            path=self.bangkok_area_path,
            district_column=self.district_column,
            subdistrict_column=self.subdistrict_column,
            cutoff=self.cutoff_district_subdistrict,
            prefix_bonus=self.prefix_bonus_district_subdistrict,
        )

        self.coordinate_transformer = CoordinateTransformerSpark(
            spark=self.spark,
            sedona=self.sedona,
            path=self.geographic_data_path,
            coords_column=self.coords_column,
            district_column=self.district_column,
            subdistrict_column=self.subdistrict_column,
            geo_district_column=self.geo_district_column,
            geo_subdistrict_column=self.geo_subdistrict_column,
            cutoff=self.cutoff_coordinate,
            prefix_bonus=self.prefix_bonus_coordinate,
        )

    def _transform(self, df: DataFrame) -> DataFrame:
        """
        Sequentially applies address transformation steps to the input DataFrame.

        Parameters
        ----------
        df : pyspark.sql.DataFrame
            The input DataFrame.

        Returns
        -------
        pyspark.sql.DataFrame
            The transformed DataFrame with standardized and enriched address columns.
        """

        df_transformed = self.province_transformer.transform(df)
        df_transformed = self.districtsubdistrict_transformer.transform(df_transformed)
        df_transformed = self.coordinate_transformer.transform(df_transformed)

        return df_transformed
