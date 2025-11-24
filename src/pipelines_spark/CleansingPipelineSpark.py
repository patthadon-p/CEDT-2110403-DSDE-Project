# Import necessary modules
from pyspark.ml import Transformer
from pyspark.sql import DataFrame, SparkSession

# Other Transformer
from .AddressTransformerSpark import AddressTransformerSpark
from .DateTransformerSpark import DateTransformerSpark
from .IngestionPreprocessorSpark import IngestionPreprocessorSpark
from .StateToStatusTransformerSpark import StateToStatusTransformerSpark


class CleansingPipelineSpark(Transformer):

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

        df_transformed = self.ingest_pre_processor.transform(df)
        df_transformed = self.date_transformer.transform(df_transformed)
        df_transformed = self.address_transformer.transform(df_transformed)
        df_transformed = self.state_to_status_transformer.transform(df_transformed)

        df_transformed = df_transformed.dropna()

        return df_transformed
