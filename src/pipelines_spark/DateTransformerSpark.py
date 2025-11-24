# Import necessary modules
from pyspark.ml import Transformer
from pyspark.sql import DataFrame
from pyspark.sql.functions import col, date_diff, dayofmonth, month, to_timestamp, year


class DateTransformerSpark(Transformer):

    def __init__(
        self, start_time_column: str | None = None, end_time_column: str | None = None
    ) -> None:
        self.start_time_column = start_time_column or "timestamp"
        self.end_time_column = end_time_column or "last_activity"
        self.resolution_time_column = "resolution_time"

    def _transform(self, df: DataFrame) -> DataFrame:

        for c in [self.start_time_column, self.end_time_column]:
            if c in df.columns:
                df = df.withColumn(c, to_timestamp(col(c)))

                df = df.withColumn(f"{c}_date", dayofmonth(col(c)))
                df = df.withColumn(f"{c}_month", month(col(c)))
                df = df.withColumn(f"{c}_year", year(col(c)))

        df = df.withColumn(
            self.resolution_time_column,
            date_diff(end=self.end_time_column, start=self.start_time_column),
        )
        df = df.drop(self.start_time_column, self.end_time_column)

        return df
