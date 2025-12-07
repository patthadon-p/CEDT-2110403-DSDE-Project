"""
PySpark Utility for Multi-Value Feature Vectorization (CountVectorizer).

This module provides a utility function to apply PySpark's CountVectorizer
to columns containing multiple categorical values separated by a delimiter.
It handles null values, automatically fits/loads the necessary model,
and generates a sparse feature vector suitable for machine learning.

Functions
---------
multi_value_vectorizer
    Converts a string column with delimiter-separated values (e.g., tags, organizations)
    into a PySpark ArrayType, then applies CountVectorizer, with support for
    saving and loading the fitted model.
"""

# Import necessary modules
import os

import pyspark.sql.functions as F
from pyspark.ml.feature import CountVectorizer, CountVectorizerModel
from pyspark.sql import DataFrame

# Utility functions
from src.utils import get_data_dir


def multi_value_vectorizer(
    df: DataFrame,
    input_column: str,
    output_column: str,
    delimiter: str = ",",
    filename: str | None = None,
    drop_original: bool = True,
) -> DataFrame:
    """
    Converts a delimited string column into a CountVectorizer feature vector.

    The function first splits the input column by the specified delimiter into
    an ArrayType. It then checks if a fitted CountVectorizerModel exists locally;
    if so, it loads the model; otherwise, it fits a new model and saves it.
    Finally, it applies the model to the DataFrame.

    Parameters
    ----------
    df : pyspark.sql.DataFrame
        The input DataFrame containing the multi-value string column.
    input_column : str
        The name of the column containing the delimited string values.
    output_column : str
        The name of the output column for the generated sparse feature vector.
    delimiter : str, optional
        The character used to separate values within the input string column.
        Default is ",".
    filename : str or None, optional
        The specific name for the saved/loaded CountVectorizerModel directory.
        If None, defaults to "vectorizer_model".
    drop_original : bool, optional
        If True, the original `input_column` is dropped from the resulting DataFrame.
        Default is True.

    Returns
    -------
    pyspark.sql.DataFrame
        The transformed DataFrame containing the new sparse feature vector column
        (`output_column`), with the `input_column` potentially dropped.
    """

    df_array = df.withColumn(
        input_column,
        F.when(
            F.col(input_column).isNotNull(),
            F.split(F.col(input_column), delimiter),
        ).otherwise(F.array().cast("array<string>")),
    )

    save_path = (
        get_data_dir()
        / "model"
        / ("vectorizer_model" if filename is None else filename)
    )
    if os.path.isdir(save_path):
        model = CountVectorizerModel.load(str(save_path))
    else:
        cv = CountVectorizer(inputCol=input_column, outputCol=output_column)
        model = cv.fit(df_array)
        model.save(str(save_path))

    df_out = model.transform(df_array)

    if drop_original:
        df_out = df_out.drop(input_column)

    return df_out
