# Import necessary modules
import json

from pyspark.ml import Transformer
from pyspark.sql import DataFrame

# Utility Functions
from src.utils.ConfigUtils import read_config_path


class IngestionPreprocessorSpark(Transformer):

    def __init__(
        self,
        filepath: str = "",
        drop_columns: list[str] | None = None,
        drop_na_columns: list[str] | None = None,
    ) -> None:

        self.filepath = filepath
        self.drop_columns = drop_columns or []
        self.drop_na_columns = drop_na_columns or []

        if self.filepath == "":
            self.filepath = read_config_path(
                key="raw_data_columns_path", filepath=self.filepath
            )

        with open(self.filepath, encoding="utf-8") as file:
            raw_data_columns = dict(json.load(file))

        self.rename_dict = raw_data_columns.get("columns", {})
        self.drop_columns = (
            drop_columns or raw_data_columns.get("drop_columns", []) or ["DROP"]
        )
        self.drop_na_columns = drop_na_columns or raw_data_columns.get(
            "drop_na_columns", []
        )

    def _transform(self, df: DataFrame) -> DataFrame:

        for old, new in self.rename_dict.items():
            if old in df.columns:
                df = df.withColumnRenamed(old, new)

        actual_drop_cols = [c for c in self.drop_columns if c in df.columns]
        if actual_drop_cols:
            df = df.drop(*actual_drop_cols)

        actual_na_cols = [c for c in self.drop_na_columns if c in df.columns]
        if actual_na_cols:
            df = df.na.drop(subset=actual_na_cols)

        return df
