# Import necessary libraries
from pyspark.ml import Transformer
from pyspark.sql import DataFrame, SparkSession

# Utility Functions
from src.utils.StatusUtils import load_status_mapping


class StateToStatusTransformerSpark(Transformer):

    def __init__(
        self,
        spark: SparkSession,
        path: str = "",
        mapping: dict | None = None,
        old_column: str | None = None,
        new_column: str | None = None,
    ) -> None:
        super().__init__()

        self.spark = spark

        self.old_column = old_column or "state"
        self.new_column = new_column or "status"
        self.mapping = mapping or load_status_mapping(path)

        mapping_items = list(self.mapping.items())
        self.mapping_df = self.spark.createDataFrame(
            mapping_items, schema=[self.old_column, self.new_column]
        )

    def _transform(self, df: DataFrame) -> DataFrame:
        df_joined = df.join(self.mapping_df, on=self.old_column, how="left")

        if self.new_column != self.old_column:
            df_joined = df_joined.drop(self.old_column)

        return df_joined
