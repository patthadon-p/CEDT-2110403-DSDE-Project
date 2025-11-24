# Import necessary modules
from pyspark.ml import Transformer
from pyspark.sql import DataFrame, SparkSession

# Other Transformer
from .CoordinateTransformerSpark import CoordinateTransformerSpark
from .DistrictSubdistrictTransformerSpark import DistrictSubdistrictTransformerSpark
from .ProvinceTransformerSpark import ProvinceTransformerSpark


class AddressTransformerSpark(Transformer):

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

        df_transformed = self.province_transformer.transform(df)
        df_transformed = self.districtsubdistrict_transformer.transform(df_transformed)
        df_transformed = self.coordinate_transformer.transform(df_transformed)

        return df_transformed
