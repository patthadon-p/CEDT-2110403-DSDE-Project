# Setting up the environment
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import necessary modules
import pandas as pd
from sklearn.base import BaseEstimator, TransformerMixin


class DateTransformer(BaseEstimator, TransformerMixin):
    def __init__(self, columns=None):
        self.columns = columns or ["timestamp", "last_activity"]

    def fit(self, X, y=None):
        return self

    def transform(self, X):
        X = X.copy()

        for col in self.columns:
            X[col] = pd.to_datetime(X[col], errors="coerce")
            X[f"{col}_date"] = X[col].dt.day.astype("Int64")
            X[f"{col}_month"] = X[col].dt.month.astype("Int64")
            X[f"{col}_year"] = X[col].dt.year.astype("Int64")

        X = X.drop(columns=self.columns, errors="ignore")

        return X
