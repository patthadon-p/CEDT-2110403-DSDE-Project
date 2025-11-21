"""
Province name standardization utilities.

This module defines the ProvinceTransformer class, a Scikit-learn transformer
designed to clean and standardize province names in a DataFrame. It uses a
pre-loaded whitelist to map variations (including misspellings and abbreviations)
to their single official name, while tracking any unrecognized values.

It relies on external utility functions for loading the whitelist,
text normalization, and fuzzy string matching.

Classes
-------
ProvinceTransformer
    A transformer that standardizes province names, removing common prefixes
    and mapping variants to official names using a whitelist lookup.
"""

# Setting up the environment
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import necessary modules
import pandas as pd
from sklearn.base import BaseEstimator, TransformerMixin

# Utility functions
from utils.FuzzyUtils import fuzzy_match, normalize
from utils.ProvinceUtils import load_province_whitelist


class ProvinceTransformer(BaseEstimator, TransformerMixin):
    """
    Standardizes province names by cleaning prefixes and mapping variants
    to their official standard name using a lookup table (whitelist).

    This transformer performs the following steps on the target column:
    1. **Cleaning:** Removes common prefixes like "จังหวัด" (Province) and "จ." (Abbreviated Province).
    2. **Normalization & Fuzzy Match:** Applies text normalization and attempts to find a match
       in the whitelist keys using fuzzy matching.
    3. **Mapping:** Maps the resulting cleaned name using the loaded whitelist dictionary
       to get the official standard name.
    4. **Filtering:** Collects and stores any original values that could not
       be mapped (i.e., not found in the whitelist) for manual inspection.

    Parameters
    ----------
    path : str, optional
        File path to the JSON file containing the province whitelist mapping.
        Default is "".
    province_column : str or None, optional
        Name of the column containing province names to be transformed.
        Defaults to "province".

    Attributes
    ----------
    path : str
        The file path to the province whitelist used during initialization.
    whitelist : dict of {str: str}
        The loaded reverse lookup dictionary where keys are cleaned/variant names
        and values are the standard official names.
    province_column : str
        The name of the column being processed.
    filtered : list of str
        A running list of all non-standardized (unmapped) province names encountered
        during the transformation process.
    _cache_province : dict
        Internal cache used by the `fuzzy_match` function to store previous
        fuzzy matching results, improving performance.
    """

    def __init__(self, path: str = "", province_column: str | None = None) -> None:
        self.path = path

        self.whitelist = load_province_whitelist(self.path)

        self.province_column = province_column or "province"
        self.filtered = []

        self._cache_province = {}

    def fit(self, X: pd.DataFrame, y: pd.Series | None = None) -> "ProvinceTransformer":
        """
        The fit method does nothing for this transformer, as it performs
        stateless, column-wise transformation using a predefined lookup table.

        Parameters
        ----------
        X : pandas.DataFrame
            The input data (not used for fitting).
        y : array-like of shape (n_samples,), default=None
            Target values (not used).

        Returns
        -------
        ProvinceTransformer
            The fitted transformer (self).
        """

        return self

    def transform(self, X: pd.DataFrame) -> pd.DataFrame:
        """
        Transforms the DataFrame by cleaning province names, mapping them
        to standard names, and collecting unmapped variants.

        Parameters
        ----------
        X : pandas.DataFrame
            The input DataFrame containing the province column.

        Returns
        -------
        pandas.DataFrame
            The transformed DataFrame with the province column containing
            standardized names (or None if unmapped).
        """

        df = X.copy()

        df[self.province_column] = (
            df[self.province_column]
            .astype(str)
            .str.replace("จังหวัด", "", regex=False)  # แทน "จังหวัด" ด้วยช่องว่าง
            .str.replace("จ.", "", regex=False)  # แทน "จ." ด้วยช่องว่าง
            .str.strip()
        )

        df[self.province_column] = (
            df[self.province_column]
            .apply(normalize)
            .apply(
                lambda x: fuzzy_match(
                    x, list(self.whitelist.keys()), self._cache_province
                )
            )
        )

        # map values
        mapped = df[self.province_column].map(self.whitelist)

        # detect values not found in mapping
        mask_not_found = mapped.isna() & df[self.province_column].notna()

        # collect the original unmapped values
        self.filtered.extend(df.loc[mask_not_found, self.province_column].tolist())

        # assign mapped values back (unmapped become None)
        df[self.province_column] = mapped.where(mapped.notna(), None)

        return df

    def get_filtered_values(self) -> list[str]:
        """
        Retrieves the unique set of province name variants that were not found
        in the whitelist during transformation.

        This method is useful for identifying potential misspellings or
        missing entries that need to be added to the whitelist.

        Returns
        -------
        list of str
            A list containing unique, unmapped province names (variants).
        """
        return list(set(self.filtered))
