"""
PySpark Transformer for Problem Type Feature Encoding.

This module provides the TypeEncoderSpark class, a PySpark ML Transformer
that prepares the problem type column (which often contains a list/array string)
by cleaning it, splitting it into multiple tags, and converting the result into
a numerical feature vector using **CountVectorizer** (multi-hot encoding).

Classes
-------
TypeEncoderSpark
    A PySpark ML Transformer that cleans the raw problem type string, splits it
    into an array of tags, and applies CountVectorizer to generate a feature vector.
"""

# Import necessary modules
from pyspark.ml import Transformer
from pyspark.ml.feature import CountVectorizer, CountVectorizerModel  # noqa: F401
from pyspark.sql import DataFrame
from pyspark.sql import functions as F

from src.utils.EncoderUtils import multi_value_vectorizer


class TypeEncoderSpark(Transformer):
    """
    Encodes the problem type column into a feature vector using PySpark's CountVectorizer.

    The input `type_column` is first cleaned (removing surrounding brackets/braces),
    split by commas into an array of strings (multi-value handling), and then
    CountVectorizer is applied to create the feature vector. The original
    type column is dropped after encoding.

    Parameters
    ----------
    type_column : str or None, optional
        Name of the input column containing problem type strings (which may be
        in a list/array format like '["type1", "type2"]'). Defaults to "type".
    model_filename : str or None, optional
        Name of the file used to save/load the fitted CountVectorizerModel.
        Defaults to "type_vectorizer_model".

    Attributes
    ----------
    type : str
        The final name of the input type column.
    type_encoded : str
        The name of the output vector column. Defaults to "<type>_encoded".
    model_filename : str
        The final name of the file used to save/load the fitted CountVectorizerModel.
    """

    def __init__(
        self,
        type_column: str | None = None,
        model_filename: str | None = None,
    ) -> None:
        """
        Initializes the PySpark Type Encoder.

        Parameters
        ----------
        type_column : str or None, optional
            Name of the input column containing problem type strings. Defaults to "type".
        """

        self.type = type_column or "type"
        self.type_encoded = self.type + "_encoded"
        self.model_filename = model_filename or "type_vectorizer_model"

    def _transform(self, df: DataFrame) -> DataFrame:
        """
        Applies cleaning, multi-value splitting, and CountVectorizer feature encoding.

        The cleaning step uses `substring` to remove the first and last characters,
        assuming they are array/list delimiters (e.g., brackets/braces).

        Parameters
        ----------
        df : pyspark.sql.DataFrame
            The input DataFrame containing the problem type column.

        Returns
        -------
        pyspark.sql.DataFrame
            The transformed DataFrame with the original type column
            replaced by the CountVectorizer feature vector column.
        """

        df = df.withColumn(
            self.type, F.expr(f"substring({self.type}, 2, length({self.type})-2)")
        )

        encoded_df = multi_value_vectorizer(
            df,
            input_column=self.type,
            output_column=self.type_encoded,
            filename=self.model_filename,
            drop_original=True,
        )

        return encoded_df
