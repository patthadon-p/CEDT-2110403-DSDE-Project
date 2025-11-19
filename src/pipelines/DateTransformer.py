"""
Date feature transformation utilities.

This module provides the DateTransformer class, a Scikit-learn-compatible
transformer designed to clean and standardize date columns in a DataFrame.
It converts columns to datetime format, handles parsing errors, and extracts
useful temporal features (day, month, year) for machine learning models.

Classes
-------
DateTransformer
    A transformer that converts specified columns to datetime objects and
    extracts time-based features, dropping the original column.
"""

# Setting up the environment
import os
import sys

import pandas as pd

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import necessary modules
from sklearn.base import BaseEstimator, TransformerMixin


class DateTransformer(BaseEstimator, TransformerMixin):
    """
    Converts specified columns to datetime objects and extracts new date features.

    For each specified column:
    1. Converts the column to a datetime format (coercing errors to NaT).
    2. Extracts and creates three new integer columns: `_date`, `_month`, and `_year`.
    3. Drops the original datetime column.

    Parameters
    ----------
    columns : list of str or None, optional
        List of column names to transform. Defaults to ["timestamp", "last_activity"].

    Attributes
    ----------
    columns : list of str
        The final list of columns that will be processed.
    """

    def __init__(self, columns: list[str] = None) -> None:
        self.columns = columns or ["timestamp", "last_activity"]

    def fit(self, X: pd.DataFrame, y: pd.Series = None) -> "DateTransformer":
        """
        The fit method does nothing for this transformer, as it performs
        stateless, column-wise transformation logic.

        Parameters
        ----------
        X : pandas.DataFrame
            The input data (not used for fitting).
        y : array-like of shape (n_samples,), default=None
            Target values (not used).

        Returns
        -------
        DateTransformer
            The fitted transformer (self).
        """

        return self

    def transform(self, X: pd.DataFrame) -> pd.DataFrame:
        """
        Transforms the DataFrame by standardizing date columns and extracting features.

        Parameters
        ----------
        X : pandas.DataFrame
            The input DataFrame containing the date columns to be processed.

        Returns
        -------
        pandas.DataFrame
            The transformed DataFrame with the original date columns replaced
            by the new `_date`, `_month`, and `_year` feature columns.
        """

        X = X.copy()

        for col in self.columns:
            X[col] = pd.to_datetime(X[col], errors="coerce")
            X[f"{col}_date"] = X[col].dt.day.astype("Int64")
            X[f"{col}_month"] = X[col].dt.month.astype("Int64")
            X[f"{col}_year"] = X[col].dt.year.astype("Int64")

        X = X.drop(columns=self.columns, errors="ignore")

        return X
