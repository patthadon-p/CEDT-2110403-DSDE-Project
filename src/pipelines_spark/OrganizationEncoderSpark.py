"""
PySpark Transformer for Organization Feature Encoding.

This module provides the OrganizationEncoderSpark class, a PySpark ML Transformer
that converts the organization column (which may contain multiple comma-separated
values) into a numerical feature vector using **CountVectorizer**. This encoding
is a form of multi-hot encoding suitable for multi-label categorical data.

Classes
-------
OrganizationEncoderSpark
    A PySpark ML Transformer that processes the organization column, splits it
     into an array of strings, and applies CountVectorizer to generate a feature vector.
"""

# Import necessary modules
from pyspark.ml import Transformer
from pyspark.ml.feature import CountVectorizer, CountVectorizerModel  # noqa: F401
from pyspark.sql import DataFrame

from src.utils.EncoderUtils import multi_value_vectorizer


class OrganizationEncoderSpark(Transformer):
    """
    Encodes the organization column into a feature vector using PySpark's CountVectorizer.

    The organization column is first split by commas into an array of strings
    (multi-value handling), and then CountVectorizer is applied. The original
    organization column is dropped after encoding.

    Parameters
    ----------
    organization_column : str or None, optional
        Name of the input column containing organization names (which may be
        comma-separated). Defaults to "organization".
    model_filename : str or None, optional
        Name of the file used to save/load the fitted CountVectorizerModel.
        Defaults to "organization_vectorizer_model".

    Attributes
    ----------
    organization : str
        The final name of the input organization column.
    organization_encoded : str
        The name of the output vector column. Defaults to "<organization>_encoded".
    model_filename : str
        The final name of the file used to save/load the fitted CountVectorizerModel.
    """

    def __init__(
        self,
        organization_column: str | None = None,
        model_filename: str | None = None,
    ) -> None:
        """
        Initializes the PySpark Organization Encoder.

        Parameters
        ----------
        organization_column : str or None, optional
            Name of the input column containing organization names. Defaults to "organization".
        model_filename : str or None, optional
            Name of the file used to save/load the fitted CountVectorizerModel.
            Defaults to "organization_vectorizer_model".
        """

        self.organization = organization_column or "organization"
        self.organization_encoded = self.organization + "_encoded"
        self.model_filename = model_filename or "organization_vectorizer_model"

    def _transform(self, df: DataFrame) -> DataFrame:
        """
        Applies multi-value splitting and CountVectorizer feature encoding.

        Parameters
        ----------
        df : pyspark.sql.DataFrame
            The input DataFrame containing the organization column.

        Returns
        -------
        pyspark.sql.DataFrame
            The transformed DataFrame with the original organization column
            replaced by the CountVectorizer feature vector column.
        """

        encoded_df = multi_value_vectorizer(
            df,
            input_column=self.organization,
            output_column=self.organization_encoded,
            filename=self.model_filename,
            drop_original=True,
        )

        return encoded_df
