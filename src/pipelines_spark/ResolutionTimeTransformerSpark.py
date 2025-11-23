from pyspark.ml import Transformer
from pyspark.sql import DataFrame
from pyspark.sql.functions import col


class ResolutionTimeTransformerSpark(Transformer):

    def __init__(
        self,
        start_date_column: str | None = None,
        start_month_column: str | None = None,
        start_year_column: str | None = None,
        end_date_column: str | None = None,
        end_month_column: str | None = None,
        end_year_column: str | None = None,
    ):
        self.start_date_column = start_date_column or "timestamp_date"
        self.start_month_column = start_month_column or "timestamp_month"
        self.start_year_column = start_year_column or "timestamp_year"
        self.end_date_column = end_date_column or "last_activity_date"
        self.end_month_column = end_month_column or "last_activity_month"
        self.end_year_column = end_year_column or "last_activity_year"
        self.output_col = "resolution_time"

    def _transform(self, df: DataFrame) -> DataFrame:

        df_transformed = df.withColumn(
            self.output_col,
            (col(self.end_year_column) - col(self.start_year_column)) * 365
            + (col(self.end_month_column) - col(self.start_month_column)) * 30
            + (col(self.end_date_column) - col(self.start_date_column)),
        )

        df_transformed = df_transformed.drop(
            self.start_date_column,
            self.end_date_column,
            self.end_month_column,
            self.end_year_column,
        )

        return df_transformed
