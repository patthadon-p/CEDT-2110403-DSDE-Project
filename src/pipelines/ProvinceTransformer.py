# Setting up the environment
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import necessary modules
from sklearn.base import BaseEstimator, TransformerMixin

# Utility functions
from utils.ProvinceUtils import load_province_whitelist


class ProvinceTransformer(BaseEstimator, TransformerMixin):
    def __init__(self, columns=None):
        self.columns = columns
        self.filtered = []

    def fit(self, X, y=None):
        return self

    def transform(self, X):
        df = X.copy()

        cols = self.columns
        if cols is None:
            cols = df.select_dtypes(include=["object", "string"]).columns

        # load whitelist mapping
        whitelist = load_province_whitelist()

        for c in cols:
            df[c] = (
                df[c]
                .astype(str)
                .str.replace("จังหวัด", "", regex=False)  # แทน "จังหวัด" ด้วยช่องว่าง
                .str.replace("จ.", "", regex=False)  # แทน "จ." ด้วยช่องว่าง
                .str.strip()
            )

            # map values
            mapped = df[c].map(whitelist)

            # detect values not found in mapping
            mask_not_found = mapped.isna() & df[c].notna()

            # collect the original unmapped values
            self.filtered.extend(df.loc[mask_not_found, c].tolist())

            # assign mapped values back (unmapped become None)
            df[c] = mapped.where(mapped.notna(), None)

        return df

    def get_filtered_values(self):
        return list(set(self.filtered))
