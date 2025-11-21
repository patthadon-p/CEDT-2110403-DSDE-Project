"""
District and subdistrict name standardization utilities.

This module provides the DistrictSubdistrictTransformer class, a Scikit-learn
transformer designed to clean, normalize, and match district and subdistrict
names against a list of official names using fuzzy string matching. This
mitigates issues caused by misspellings or inconsistent text input.

Classes
-------
DistrictSubdistrictTransformer
    A transformer that standardizes district and subdistrict names using
    text normalization and caching fuzzy matching against a predefined list
    of official names.
"""

# Import necessary modules
import pandas as pd
from sklearn.base import BaseEstimator, TransformerMixin

# Utility functions
from ..utils.DistrictSubdistrictUtils import load_bangkok_official_area_names
from ..utils.FuzzyUtils import fuzzy_match, normalize


class DistrictSubdistrictTransformer(BaseEstimator, TransformerMixin):
    """
    Standardizes and corrects district and subdistrict names using fuzzy matching.

    This transformer sequentially applies two main steps to the target columns:
    1. **Text Normalization:** Cleans up whitespace and standardizes common
       Thai prefix repetitions (e.g., 'บางบาง' to 'บาง').
    2. **Fuzzy Matching:** Compares the normalized name against a pre-loaded
       list of official names and replaces it with the closest match, caching
       the results for efficiency.

    Parameters
    ----------
    path : str, optional
        File path to the JSON file containing the official district and
        subdistrict names (mapping dictionary). Default is "".
    district_column : str or None, optional
        Name of the column containing district names to be transformed.
        Defaults to "district".
    subdistrict_column : str or None, optional
        Name of the column containing subdistrict names to be transformed.
        Defaults to "subdistrict".

    Attributes
    ----------
    official_districts : list of str
        The list of standard district names used as fuzzy match targets.
    official_subdistricts : list of str
        The list of standard subdistrict names used as fuzzy match targets.
    _cache_district : dict
        Internal cache for storing matched district names ({input: official_name}).
    _cache_subdistrict : dict
        Internal cache for storing matched subdistrict names.
    """

    def __init__(
        self,
        path: str = "",
        district_column: str | None = None,
        subdistrict_column: str | None = None,
    ) -> None:
        self.path = path

        self.district_column = district_column or "district"
        self.subdistrict_column = subdistrict_column or "subdistrict"

        official_area_name = load_bangkok_official_area_names(self.path)

        self.official_districts = official_area_name.get("districts", [])
        self.official_subdistricts = official_area_name.get("subdistricts", [])

        self._cache_district = {}
        self._cache_subdistrict = {}

    def fit(
        self, X: pd.DataFrame, y: pd.Series | None = None
    ) -> "DistrictSubdistrictTransformer":
        """
        The fit method does nothing for this transformer, as it performs
        stateless, column-wise transformation and uses a predefined lookup list.

        Parameters
        ----------
        X : pandas.DataFrame
            The input data (not used for fitting).
        y : array-like of shape (n_samples,), default=None
            Target values (not used).

        Returns
        -------
        DistrictSubdistrictTransformer
            The fitted transformer (self).
        """

        return self

    def transform(self, X: pd.DataFrame) -> pd.DataFrame:
        """
        Transforms the DataFrame by normalizing and fuzzy matching district and
        subdistrict names.

        Parameters
        ----------
        X : pandas.DataFrame
            The input DataFrame containing the district and subdistrict columns.

        Returns
        -------
        pandas.DataFrame
            The transformed DataFrame with standardized district and subdistrict names.
        """

        df = X.copy()

        df[self.district_column] = (
            df[self.district_column]
            .apply(normalize)
            .apply(
                lambda x: fuzzy_match(x, self.official_districts, self._cache_district)
            )
        )

        df[self.subdistrict_column] = (
            df[self.subdistrict_column]
            .apply(normalize)
            .apply(
                lambda x: fuzzy_match(
                    x, self.official_subdistricts, self._cache_subdistrict
                )
            )
        )

        return df
