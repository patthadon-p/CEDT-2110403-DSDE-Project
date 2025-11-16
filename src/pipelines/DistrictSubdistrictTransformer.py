# Setting up the environment
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import necessary modules
import re

from rapidfuzz import process
from sklearn.base import BaseEstimator, TransformerMixin

# Utility functions
from utils.DistrictSubdistrictUtils import load_bangkok_official_area_names


class DistrictSubdistrictTransformer(BaseEstimator, TransformerMixin):
    def __init__(self, path="", district_column=None, subdistrict_column=None):
        self.path = path

        self.district_column = district_column or "district"
        self.subdistrict_column = subdistrict_column or "subdistrict"

        official_area_name = load_bangkok_official_area_names(self.path)

        self.official_districts = official_area_name.get("districts", [])
        self.official_subdistricts = official_area_name.get("subdistricts", [])

        self._cache_district = {}
        self._cache_subdistrict = {}

    def fit(self, X, y=None):
        return self

    def transform(self, X):
        def _normalize(text):
            if text is None:
                return None
            t = str(text)
            t = re.sub(r"\s+", " ", t).strip()
            t = re.sub(r"(บาง)\1+", r"\1", t)
            return t

        def _fuzzy_match(text, choices, cache):
            if text in cache:
                return cache[text]

            if text is None or text == "":
                return text

            match = process.extractOne(text, choices, score_cutoff=60)
            result = match[0] if match else text
            cache[text] = result
            return result

        df = X.copy()

        df[self.district_column] = (
            df[self.district_column]
            .apply(_normalize)
            .apply(
                lambda x: _fuzzy_match(x, self.official_districts, self._cache_district)
            )
        )

        df[self.subdistrict_column] = (
            df[self.subdistrict_column]
            .apply(_normalize)
            .apply(
                lambda x: _fuzzy_match(
                    x, self.official_subdistricts, self._cache_subdistrict
                )
            )
        )

        return df
