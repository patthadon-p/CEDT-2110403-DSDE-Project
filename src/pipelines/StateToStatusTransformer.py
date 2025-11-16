# Setting up the environment
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import necessary modules
from sklearn.base import BaseEstimator, TransformerMixin

# Utility functions
from utils.StatusUtils import load_status_mapping


class StateToStatusTransformer(BaseEstimator, TransformerMixin):
    def __init__(self, path="", old_column="state", new_column="status", mapping=None):
        self.old_column = old_column
        self.new_column = new_column

        if mapping is None:
            self.mapping = load_status_mapping(path)
        else:
            self.mapping = mapping

    def fit(self, X, y=None):
        return self

    def transform(self, X):
        X = X.copy()

        X[self.old_column] = X[self.old_column].replace(self.mapping)
        X = X.rename(columns={self.old_column: self.new_column})

        return X
