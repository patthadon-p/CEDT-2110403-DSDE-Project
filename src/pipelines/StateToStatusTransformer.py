"""
State and status column standardization utilities.

This module provides the StateToStatusTransformer class, a Scikit-learn
transformer designed to map raw categorical "state" values to standardized
"status" labels using a lookup dictionary. This ensures consistency in the
target variable or other key categorical features.

Classes
-------
StateToStatusTransformer
    A transformer that renames a column and replaces its values according to a
    predefined mapping dictionary loaded either directly or from a configuration file.
"""

# Import necessary modules
import pandas as pd
from sklearn.base import BaseEstimator, TransformerMixin

# Utility functions
from utils.StatusUtils import load_status_mapping


class StateToStatusTransformer(BaseEstimator, TransformerMixin):
    """
    Maps raw state values to standardized status values and renames the column.

    This transformer loads a mapping dictionary and applies it to the specified
    column, effectively standardizing the categorical values. It then renames
    the column to reflect its new standardized status.

    Parameters
    ----------
    path : str, optional
        File path for the JSON containing the status mapping. Used only if
        `mapping` is None. Default is "".
    mapping : dict or None, optional
        A predefined dictionary ({old_value: new_status}) to use for mapping.
        If provided, this overrides loading from the file path. Default is None.
    old_column : str or None, optional
        Name of the input column containing the raw state values. Defaults to "state".
    new_column : str or None, optional
        Name of the output column for the standardized status values. Defaults to "status".

    Attributes
    ----------
    mapping : dict
        The final dictionary used for value replacement (raw state -> standard status).
    old_column : str
        The name of the column containing raw input values.
    new_column : str
        The name the column will be renamed to after transformation.
    """

    def __init__(
        self,
        path: str = "",
        mapping: dict | None = None,
        old_column: str | None = None,
        new_column: str | None = None,
    ) -> None:
        self.old_column = old_column or "state"
        self.new_column = new_column or "status"

        if mapping is None:
            self.mapping = load_status_mapping(path)
        else:
            self.mapping = mapping

    def fit(
        self, X: pd.DataFrame, y: pd.Series | None = None
    ) -> "StateToStatusTransformer":
        """
        The fit method does nothing for this transformer, as it performs
        stateless mapping based on a predefined dictionary.

        Parameters
        ----------
        X : pandas.DataFrame
            The input data (not used for fitting).
        y : array-like of shape (n_samples,), default=None
            Target values (not used).

        Returns
        -------
        StateToStatusTransformer
            The fitted transformer (self).
        """

        return self

    def transform(self, X: pd.DataFrame) -> pd.DataFrame:
        """
        Transforms the DataFrame by mapping values and renaming the column.

        Parameters
        ----------
        X : pandas.DataFrame
            The input DataFrame containing the column with raw state values.

        Returns
        -------
        pandas.DataFrame
            The transformed DataFrame with the target column renamed to
            `new_column` and its values replaced according to `mapping`.
        """

        X = X.copy()

        X[self.old_column] = X[self.old_column].replace(self.mapping)
        X = X.rename(columns={self.old_column: self.new_column})

        return X
