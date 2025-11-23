# Import necessary modules

from pyspark.ml import Transformer
from pyspark.sql import DataFrame
from pyspark.sql import functions as F


class ResolutionTimeTransformerSpark(Transformer):

    def __init__(
        self,
        start_date_column: str | None = None,
        start_month_column: str | None = None,
        start_year_column: str | None = None,
        end_date_column: str | None = None,
        end_month_column: str | None = None,
        end_year_column: str | None = None,
        output_col: str | None = None,
    ) -> None:
        self.start_date_column = start_date_column or "timestamp_date"
        self.start_month_column = start_month_column or "timestamp_month"
        self.start_year_column = start_year_column or "timestamp_year"

        self.end_date_column = end_date_column or "last_activity_date"
        self.end_month_column = end_month_column or "last_activity_month"
        self.end_year_column = end_year_column or "last_activity_year"

        self.output_col = output_col or "resolution_time"

    def _transform(self, df: DataFrame) -> DataFrame:

        # Build start date string
        start_date_str = F.concat_ws(
            "-",
            F.col(self.start_year_column),
            F.lpad(F.col(self.start_month_column), 2, "0"),
            F.lpad(F.col(self.start_date_column), 2, "0"),
        )

        # Build end date string
        end_date_str = F.concat_ws(
            "-",
            F.col(self.end_year_column),
            F.lpad(F.col(self.end_month_column), 2, "0"),
            F.lpad(F.col(self.end_date_column), 2, "0"),
        )

        # Convert strings to DateType
        start_date = F.to_date(start_date_str, "yyyy-MM-dd")
        end_date = F.to_date(end_date_str, "yyyy-MM-dd")

        # Add the difference column
        df = df.withColumn(self.output_col, F.datediff(end_date, start_date))

        df_transformed = df.drop(
            self.start_date_column,
            self.end_date_column,
            self.end_month_column,
            self.end_year_column,
        )

        return df_transformed
