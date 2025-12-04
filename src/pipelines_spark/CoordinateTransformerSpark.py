"""
PySpark Transformer for Coordinate Validation and Spatial Join (Sedona).

This module provides the CoordinateTransformerSpark class, a PySpark ML Transformer
that performs **spatial validation** by checking if a data point's coordinates
fall within the reported administrative region (district/subdistrict). It utilizes
**Apache Sedona (GeoSpark)** for efficient geospatial operations on a Spark DataFrame.

Classes
-------
CoordinateTransformerSpark
    A PySpark ML Transformer that extracts coordinates, performs a spatial join
    using Sedona's ST_Within function, and filters data points based on geometric
    and textual address consistency.
"""

# Import necessary modules
from pyspark.ml import Transformer
from pyspark.sql import DataFrame, SparkSession
from pyspark.sql import functions as F

# Utility Functions
from src.utils.GeographicUtils import load_geographic_data

# Other Transformer
from .DistrictSubdistrictTransformerSpark import DistrictSubdistrictTransformerSpark


class CoordinateTransformerSpark(Transformer):
    """
    Validates data points by checking if their coordinates fall within the
    claimed administrative boundaries using Apache Sedona/GeoSpark spatial functions.

    This transformer performs the following steps:
    1. Extracts longitude/latitude from a combined coordinate string.
    2. Converts the geographic boundary data (polygons) and data points into
       Sedona geometry types.
    3. Performs a **spatial join** (`ST_Within`) to enrich point data with region names.
    4. Filters the result to include only records where the spatially derived
       district/subdistrict matches the original text-based columns.

    Parameters
    ----------
    spark : pyspark.sql.SparkSession
        The active SparkSession instance.
    sedona : pyspark.sql.SparkSession
        The active Sedona (Apache Sedona/GeoSpark) enabled SparkSession instance.
    path : str, optional
        File path to the geographic boundary data (e.g., GeoJSON, Shapefile). Default is "".
    coords_column : str or None, optional
        Name of the column containing coordinate strings (e.g., "lon,lat"). Defaults to "coords".
    district_column : str or None, optional
        Name of the input column containing the text-based district name. Defaults to "district".
    subdistrict_column : str or None, optional
        Name of the input column containing the text-based subdistrict name. Defaults to "subdistrict".
    geo_district_column : str or None, optional
        Name of the district column in the geographic boundary data. Defaults to "DISTRICT_N".
    geo_subdistrict_column : str or None, optional
        Name of the subdistrict column in the geographic boundary data. Defaults to "SUBDISTR_1".
    cutoff : int or None, optional
        The fuzzy matching cutoff score used when cleaning geographic names in the GeoDataFrame. Defaults to 60.
    prefix_bonus : bool or None, optional
        Whether to apply a bonus score for common prefixes during fuzzy matching in the GeoDataFrame cleaning. Defaults to True.

    Attributes
    ----------
    spark : pyspark.sql.SparkSession
        The active SparkSession instance.
    sedona : pyspark.sql.SparkSession
        The active Sedona enabled SparkSession instance.
    gdf : pyspark.sql.DataFrame
        The pre-processed geographic boundary DataFrame with the geometry loaded as a Sedona WKT expression.
    coords_column : str
        The final column name used for coordinate string input.
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
        spark: SparkSession,
        sedona: SparkSession,
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

        The geographic boundary GeoDataFrame is loaded, cleaned using `DistrictSubdistrictTransformerSpark`,
        and converted into a Spark DataFrame with Sedona geometry ready for spatial joins.

        Parameters
        ----------
        spark : pyspark.sql.SparkSession
            The active SparkSession instance.
        sedona : pyspark.sql.SparkSession
            The active Sedona enabled SparkSession instance.
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
            The fuzzy matching cutoff score used when cleaning geographic names in the GeoDataFrame. Defaults to 60.
        prefix_bonus : bool or None, optional
            Whether to apply a bonus score for common prefixes during fuzzy matching in the GeoDataFrame cleaning. Defaults to True.
        """

        self.spark = spark
        self.sedona = sedona

        self.path = path
        self.coords_column = coords_column or "coords"

        self.district_column = district_column or "district"
        self.subdistrict_column = subdistrict_column or "subdistrict"

        self.geo_district_column = geo_district_column or "DISTRICT_N"
        self.geo_subdistrict_column = geo_subdistrict_column or "SUBDISTR_1"

        self.cutoff = cutoff or 60
        self.prefix_bonus = prefix_bonus if prefix_bonus is not None else True

        dst = DistrictSubdistrictTransformerSpark(
            district_column=self.geo_district_column,
            subdistrict_column=self.geo_subdistrict_column,
            cutoff=self.cutoff,
            prefix_bonus=self.prefix_bonus,
        )

        gdf = load_geographic_data(self.path)
        gdf["geometry_wkt"] = gdf.geometry.to_wkt()
        gdf = gdf.drop(columns="geometry")

        gdf = self.spark.createDataFrame(gdf)

        self.gdf = dst.transform(gdf)
        self.gdf = self.gdf.withColumn(
            "geom_polygon", F.expr("ST_GeomFromWKT(geometry_wkt)")
        )

        # save_geographic_data(self.gdf.toPandas())

    def _transform(self, df: DataFrame) -> DataFrame:
        """
        Applies coordinate extraction, spatial join, and filtering to validate
        data points against the pre-loaded geographic boundaries.

        Parameters
        ----------
        df : pyspark.sql.DataFrame
            The input DataFrame containing the coordinate and address columns.

        Returns
        -------
        pyspark.sql.DataFrame
            The transformed DataFrame containing only the data points that
            are geometrically and textually consistent with the geographic
            boundary data. Original columns are preserved.
        """

        # Split coordinates into latitude, longitude (you used lat then lon)
        df = df.withColumn(
            "longitude",
            F.split(F.col(self.coords_column), ",").getItem(0).cast("double"),
        ).withColumn(
            "latitude",
            F.split(F.col(self.coords_column), ",").getItem(1).cast("double"),
        )

        # Drop original coords column if desired
        df = df.drop(self.coords_column)
        columns = df.columns

        # Create Sedona point geometry from lon/lat
        # Note: ST_Point expects (x, y) => (longitude, latitude)
        df_points = df.withColumn(
            "geom_point",
            F.expr("ST_Point(cast(longitude as double), cast(latitude as double))"),
        )

        pts = df_points.alias("pts")
        polys = self.gdf.alias("polys")

        # Spatial join points with polygons
        joined = pts.join(
            F.broadcast(polys),
            F.expr("ST_Within(pts.geom_point, polys.geom_polygon)"),
            how="left",
        )

        # Filter rows where district and subdistrict match
        joined = joined.filter(
            (F.col(self.district_column) == F.col(self.geo_district_column))
            & (F.col(self.subdistrict_column) == F.col(self.geo_subdistrict_column))
        )

        joined = joined.select(*columns)

        return joined
