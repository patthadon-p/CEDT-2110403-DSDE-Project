"""
PySpark Transformer for Address Feature Hashing and Coordinate Vectorization.

This module provides the AddressEncoderSpark class, a PySpark ML Transformer
that uses **Feature Hashing** to convert categorical address columns (district
and subdistrict) into one feature vector, and uses **VectorAssembler** to
combine continuous coordinate columns (latitude and longitude) into a second
feature vector. The final output is two sparse/dense feature columns.

Classes
-------
AddressEncoderSpark
    A PySpark ML Transformer that encodes standardized district and subdistrict
    names using FeatureHasher, and vectorizes latitude/longitude using VectorAssembler.
"""

# Import necessary libraries
from pyspark.ml import Pipeline, Transformer
from pyspark.ml.feature import FeatureHasher, VectorAssembler
from pyspark.sql import DataFrame


class AddressEncoderSpark(Transformer):
    """
    Encodes standardized address columns (district and subdistrict) into a
    hash feature vector, and combines latitude/longitude into a separate
    coordinate vector.

    The original address (district, subdistrict) and coordinate (latitude, longitude)
    columns are dropped after encoding.

    Parameters
    ----------
    district_column : str or None, optional
        Name of the input column containing standardized district names. Defaults to "district".
    subdistrict_column : str or None, optional
        Name of the input column containing standardized subdistrict names. Defaults to "subdistrict".
    latitude_column : str or None, optional
        Name of the input column containing latitude values. Defaults to "latitude".
    longitude_column : str or None, optional
        Name of the input column containing longitude values. Defaults to "longitude".
    address_encoded_column : str or None, optional
        Name of the output column for the hash vector (from district/subdistrict). Defaults to "address_encoded".
    latlong_encoded_column : str or None, optional
        Name of the output column for the coordinate vector (from latitude/longitude). Defaults to "latlong_encoded".

    Attributes
    ----------
    district_column : str
        The final name of the input district column.
    subdistrict_column : str
        The final name of the input subdistrict column.
    latitude_column : str
        The final name of the input latitude column.
    longitude_column : str
        The final name of the input longitude column.
    address_encoded_column : str
        The final name of the output hash vector column.
    latlong_encoded_column : str
        The final name of the output coordinate vector column.
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
        Initializes the PySpark Address Encoder, configuring column names and
        the FeatureHasher size.

        Parameters
        ----------
        district_column : str or None, optional
            Name of the input column containing standardized district names. Defaults to "district".
        subdistrict_column : str or None, optional
            Name of the input column containing standardized subdistrict names. Defaults to "subdistrict".
        latitude_column : str or None, optional
            Name of the input column containing latitude values. Defaults to "latitude".
        longitude_column : str or None, optional
            Name of the input column containing longitude values. Defaults to "longitude".
        address_encoded_column : str or None, optional
            Name of the output column for the hash vector (from district/subdistrict). Defaults to "address_encoded".
        latlong_encoded_column : str or None, optional
            Name of the output column for the coordinate vector (from latitude/longitude). Defaults to "latlong_encoded".
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
        Applies FeatureHasher and VectorAssembler to the address and coordinate
        columns, respectively, and drops the original input columns.

        Parameters
        ----------
        df : pyspark.sql.DataFrame
            The input DataFrame containing the address and coordinate columns.

        Returns
        -------
        pyspark.sql.DataFrame
            The transformed DataFrame with the two new feature vector columns
            (`address_encoded_column` and `latlong_encoded_column`), and
            the four original input columns dropped.
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
