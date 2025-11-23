# Import necessary modules
from pyspark.ml import Transformer
from pyspark.sql import DataFrame, SparkSession
from pyspark.sql import functions as F

# Utility Functions
from src.utils.GeographicUtils import load_geographic_data

# Other Transformer
from .DistrictSubdistrictTransformerSpark import DistrictSubdistrictTransformerSpark


class CoordinateTransformerSpark(Transformer):
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
