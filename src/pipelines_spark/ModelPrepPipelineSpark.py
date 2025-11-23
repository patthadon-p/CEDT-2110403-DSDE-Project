# Import necessary modules
from pyspark.ml import Transformer
from pyspark.sql import DataFrame

# Other Transformer
from .DataFilterTransformerSpark import DataFilterTransformerSpark
from .EncoderPipelineSpark import EncoderPipelineSpark
from .ResolutionTimeTransformerSpark import ResolutionTimeTransformerSpark


class ModelPrepPipelineSpark(Transformer):

    def __init__(
        self,
        filter_columns: dict[str, str] | None = None,
        drop_columns: list | None = None,
        district_column: str | None = None,
        encoded_column: str | None = None,
        subdistrict_column: str | None = None,
        organization_column: str | None = None,
        type_column: str | None = None,
        start_date_column: str | None = None,
        start_month_column: str | None = None,
        start_year_column: str | None = None,
        end_date_column: str | None = None,
        end_month_column: str | None = None,
        end_year_column: str | None = None,
        resolution_time_column: str | None = None,
    ) -> None:
        self.filter_columns = filter_columns
        self.drop_columns = drop_columns

        self.district_column = district_column
        self.subdistrict_column = subdistrict_column
        self.encoded_column = encoded_column
        self.organization_column = organization_column
        self.type_column = type_column

        self.start_date_column = start_date_column
        self.start_month_column = start_month_column
        self.start_year_column = start_year_column

        self.end_date_column = end_date_column
        self.end_month_column = end_month_column
        self.end_year_column = end_year_column

        self.resolution_time_column = resolution_time_column

        self.data_filter_transformer = DataFilterTransformerSpark(
            filter_columns=self.filter_columns,
            drop_columns=self.drop_columns,
        )

        self.encoder_pipeline = EncoderPipelineSpark(
            district_column=self.district_column,
            subdistrict_column=self.subdistrict_column,
            encoded_column=self.encoded_column,
            organization_column=self.organization_column,
            type_column=self.type_column,
        )

        self.resol_time_transformer = ResolutionTimeTransformerSpark(
            start_date_column=self.start_date_column,
            start_month_column=self.start_month_column,
            start_year_column=self.start_year_column,
            end_date_column=self.end_date_column,
            end_month_column=self.end_month_column,
            end_year_column=self.end_year_column,
            output_col=self.resolution_time_column,
        )

    def _transform(self, df: DataFrame) -> DataFrame:
        df_transformed = self.data_filter_transformer.transform(df)
        df_transformed = self.encoder_pipeline.transform(df_transformed)
        df_transformed = self.resol_time_transformer.transform(df_transformed)

        return df_transformed
