"""
PySpark Transformer for Address Feature Hashing.

This module provides the AddressEncoderSpark class, a PySpark ML Transformer
that uses **Feature Hashing** to convert categorical address columns (district
and subdistrict) into a single, high-dimensional numerical feature vector.
This is suitable for feeding categorical data into machine learning models
when the cardinality is high.

Classes
-------
AddressEncoderSpark
    A PySpark ML Transformer that encodes standardized district and subdistrict
    names into a sparse feature vector using FeatureHasher.
"""

# Import necessary libraries
from pyspark.ml import Pipeline, Transformer
from pyspark.ml.feature import FeatureHasher, VectorAssembler
from pyspark.sql import DataFrame


class AddressEncoderSpark(Transformer):
    """
    Encodes standardized address columns (district and subdistrict) into a
    single feature vector using PySpark's FeatureHasher.

    The original district and subdistrict columns are dropped after encoding.

    Parameters
    ----------
    district_column : str or None, optional
        Name of the input column containing standardized district names. Defaults to "district".
    subdistrict_column : str or None, optional
        Name of the input column containing standardized subdistrict names. Defaults to "subdistrict".
    encoded_column : str or None, optional
        Name of the output column for the hash vector. Defaults to "address_encoded".

    Attributes
    ----------
    district_column : str
        The final name of the input district column.
    subdistrict_column : str
        The final name of the input subdistrict column.
    encoded_column : str
        The final name of the output encoded column.
    num_features : int
        The size of the hash table (feature vector dimension). Defaults to 2048.
    """

    def __init__(
        self,
        district_column: str | None = None,
        subdistrict_column: str | None = None,
        latitude_column: str | None = None,
        longitude_column: str | None = None,
        address_encoded_column: str | None = None,
        latlong_encoded_column: str | None = None,
    ) -> None:
        """
        Initializes the PySpark Address Encoder.

        Parameters
        ----------
        district_column : str or None, optional
            Name of the input column containing standardized district names. Defaults to "district".
        subdistrict_column : str or None, optional
            Name of the input column containing standardized subdistrict names. Defaults to "subdistrict".
        encoded_column : str or None, optional
            Name of the output column for the hash vector. Defaults to "address_encoded".
        """

        self.district_column = district_column or "district"
        self.subdistrict_column = subdistrict_column or "subdistrict"
        self.latitude_column = latitude_column or "latitude"
        self.longitude_column = longitude_column or "longitude"
        self.address_encoded_column = address_encoded_column or "address_encoded"
        self.latlong_encoded_column = latlong_encoded_column or "latlong_encoded"
        self.num_features = 2048

    def _transform(self, df: DataFrame) -> DataFrame:
        """
        Applies the FeatureHasher to the specified address columns and drops the original columns.

        Parameters
        ----------
        df : pyspark.sql.DataFrame
            The input DataFrame containing the address columns.

        Returns
        -------
        pyspark.sql.DataFrame
            The transformed DataFrame with the address columns replaced by the
            new hash-encoded feature vector column (`encoded_column`).
        """

        hasher = FeatureHasher(
            inputCols=[self.district_column, self.subdistrict_column],
            outputCol=self.address_encoded_column,
            numFeatures=self.num_features,
        )

        assembler = VectorAssembler(
            inputCols=[self.latitude_column, self.longitude_column],
            outputCol=self.latlong_encoded_column,
        )

        pipeline = Pipeline(stages=[hasher, assembler])
        model = pipeline.fit(df)
        encoded_df = model.transform(df)

        encoded_df = encoded_df.drop(
            self.district_column,
            self.subdistrict_column,
            self.latitude_column,
            self.longitude_column,
        )

        return encoded_df
