# Import necessary modules
from pyspark.ml import Pipeline, Transformer
from pyspark.sql import DataFrame

# Other Transformer
from .DataFilterTransformerSpark import DataFilterTransformerSpark
from .EncoderPipelineSpark import EncoderPipelineSpark
from .ResolutionTimeTransformerSpark import ResolutionTimeTransformerSpark


class ModelPrepPipelineSpark(Transformer):

    def __init__(
        self,
        province_column: str | None = None,
        allowed_provinces: list | None = None,
        status_column: str | None = None,
        allowed_statuses: list | None = None,
        drop_columns: list | None = None,
        district_column: str | None = None,
        subdistrict_column: str | None = None,
        organization_column: str | None = None,
        type_column: str | None = None,
        start_date_column: str | None = None,
        start_month_column: str | None = None,
        start_year_column: str | None = None,
        end_date_column: str | None = None,
        end_month_column: str | None = None,
        end_year_column: str | None = None,
    ) -> None:
        self.province_column = province_column
        self.allowed_provinces = allowed_provinces
        self.status_column = status_column
        self.allowed_statuses = allowed_statuses
        self.drop_columns = drop_columns

        self.district_column = district_column
        self.subdistrict_column = subdistrict_column
        self.organization_column = organization_column
        self.type_column = type_column

        self.start_date_column = start_date_column
        self.start_month_column = start_month_column
        self.start_year_column = start_year_column
        self.end_date_column = end_date_column
        self.end_month_column = end_month_column
        self.end_year_column = end_year_column

        self.data_filter_transformer = DataFilterTransformerSpark(
            province_column=self.province_column,
            allowed_provinces=self.allowed_provinces,
            status_column=self.status_column,
            allowed_statuses=self.allowed_statuses,
            drop_columns=self.drop_columns,
        )

        self.encoder_pipeline = EncoderPipelineSpark(
            district_column=self.district_column,
            subdistrict_column=self.subdistrict_column,
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
        )

    def _transform(self, df: DataFrame) -> DataFrame:
        model_prep_pipeline = Pipeline(
            stages=[
                self.data_filter_transformer,
                self.encoder_pipeline,
                self.resol_time_transformer,
            ]
        )

        df_transformed = model_prep_pipeline.fit(df).transform(df)

        return df_transformed
