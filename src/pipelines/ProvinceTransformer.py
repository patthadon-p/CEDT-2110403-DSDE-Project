# Setting up the environment
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import necessary modules
from sklearn.base import BaseEstimator, TransformerMixin

# Utility functions
from utils.ProvinceUtils import load_province_whitelist


class ProvinceTransformer(BaseEstimator, TransformerMixin):
    def __init__(self, path="", province_column=None):
        self.path = path

        self.whitelist = load_province_whitelist(self.path)

        self.province_column = province_column or "province"
        self.filtered = []

    def fit(self, X, y=None):
        return self

    def transform(self, X):
        df = X.copy()

        df[self.province_column] = (
            df[self.province_column]
            .astype(str)
            .str.replace("จังหวัด", "", regex=False)  # แทน "จังหวัด" ด้วยช่องว่าง
            .str.replace("จ.", "", regex=False)  # แทน "จ." ด้วยช่องว่าง
            .str.strip()
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

    def get_filtered_values(self):
        return list(set(self.filtered))
