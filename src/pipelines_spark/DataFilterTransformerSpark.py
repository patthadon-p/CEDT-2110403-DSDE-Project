from pyspark.ml import Transformer
from pyspark.sql import DataFrame
from pyspark.sql.functions import col


class DataFilterTransformerSpark(Transformer):

    def __init__(
        self,
        province_column: str | None = None,
        allowed_provinces: list | None = None,
        status_column: str | None = None,
        allowed_statuses: list | None = None,
        drop_columns: list | None = None,
    ):
        self.province_column = province_column or "province"
        self.allowed_provinces = allowed_provinces or ["กรุงเทพมหานคร"]
        self.status_column = status_column or "status"
        self.allowed_statuses = allowed_statuses or ["done"]
        self.drop_columns = drop_columns or [
            "ticket_id",
            "comment",
            "coords",
            "address",
        ]

    def _transform(self, df: DataFrame) -> DataFrame:
        df = df.filter(col(self.province_column).isin(self.allowed_provinces)).drop(
            self.province_column
        )
        df = df.filter(col(self.status_column).isin(self.allowed_statuses)).drop(
            self.status_column
        )
        df_transformed = df.drop(*self.drop_columns)

        return df_transformed
