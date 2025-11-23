# Import necessary modules
from pyspark.ml import Transformer
from pyspark.sql import DataFrame
from pyspark.sql.functions import col, dayofmonth, month, to_timestamp, year


class DateTransformerSpark(Transformer):

    def __init__(self, columns: list[str] | None = None) -> None:
        self.columns = columns or ["timestamp", "last_activity"]

    def _transform(self, df: DataFrame) -> DataFrame:

        for c in self.columns:
            if c in df.columns:
                df = df.withColumn(c, to_timestamp(col(c)))

                df = df.withColumn(f"{c}_date", dayofmonth(col(c)))
                df = df.withColumn(f"{c}_month", month(col(c)))
                df = df.withColumn(f"{c}_year", year(col(c)))

                df = df.drop(c)

        return df
