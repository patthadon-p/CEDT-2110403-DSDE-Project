# Setting up the environment
import json
import os
import sys

import pandas as pd

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import necessary modules
from sklearn.base import BaseEstimator, TransformerMixin

# Utility functions
from utils.ConfigUtils import read_config_path


class IngestionPreprocessor(BaseEstimator, TransformerMixin):
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
            drop_columns or raw_data_columns.get("drop_columns", []) or "DROP"
        )
        self.drop_na_columns = drop_na_columns or raw_data_columns.get(
            "drop_na_columns", []
        )

    def fit(
        self, X: pd.DataFrame, y: pd.Series | None = None
    ) -> "IngestionPreprocessor":
        return self

    def transform(self, X: pd.DataFrame) -> pd.DataFrame:
        df = X.copy()
        df_transformed = df.rename(columns=self.rename_dict)
        df_transformed = df_transformed.drop(columns=self.drop_columns)
        df_transformed = df_transformed.dropna(subset=self.drop_na_columns)

        return df_transformed
