# Import necessary libraries
from pyspark.ml import Transformer
from pyspark.sql import DataFrame
from pyspark.sql.functions import col


class DataFilterTransformerSpark(Transformer):

    def __init__(
        self,
        filter_columns: dict[str, str] | None = None,
        drop_columns: list | None = None,
    ) -> None:
        self.filter_columns = filter_columns or {
            "province": "กรุงเทพมหานคร",
            "status": "done",
        }

        self.drop_columns = drop_columns or [
            "ticket_id",
            "comment",
            "coords",
            "address",
            "timestamp_date",
            "last_activity_date",
            "last_activity_month",
            "last_activity_year",
        ]

    def _transform(self, df: DataFrame) -> DataFrame:
        for column, value in self.filter_columns.items():
            if column in df.columns:
                df = df.filter(col(column).isin([value])).drop(column)

        df_transformed = df.drop(*self.drop_columns)

        return df_transformed
