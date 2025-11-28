"""
PySpark Transformer for Feature Encoding Pipeline.

This module provides the EncoderPipelineSpark class, a PySpark ML meta-Transformer
that combines multiple specialized encoders (Address, Organization, and Type)
into a single, sequential pipeline step. This is essential for preparing
categorical features for machine learning models in a Spark environment.

Classes
-------
EncoderPipelineSpark
    A PySpark meta-transformer that orchestrates the sequential encoding of
    address, organization, and problem type columns using specialized Spark Encoders.
"""

# Import necessary modules
from pyspark.ml import Transformer
from pyspark.sql import DataFrame

# Other Encoder
from .AddressEncoderSpark import AddressEncoderSpark
from .OrganizationEncoderSpark import OrganizationEncoderSpark
from .TypeEncoderSpark import TypeEncoderSpark


class EncoderPipelineSpark(Transformer):
    """
    A PySpark meta-transformer that orchestrates the sequential encoding of key categorical features.

    This class combines AddressEncoderSpark, OrganizationEncoderSpark, and TypeEncoderSpark
    into a single step, ensuring all necessary feature engineering is applied consistently.

    The sequence of encoding is:
    1. Address Feature Hashing (`AddressEncoderSpark`).
    2. Organization Encoding (`OrganizationEncoderSpark`).
    3. Problem Type Encoding (`TypeEncoderSpark`).

    Parameters
    ----------
    district_column : str or None, optional
        Name of the district column used for address encoding. Default is None (will use AddressEncoderSpark default).
    subdistrict_column : str or None, optional
        Name of the subdistrict column used for address encoding. Default is None (will use AddressEncoderSpark default).
    encoded_column : str or None, optional
        Name of the output column for the address hash vector. Default is None (will use AddressEncoderSpark default).
    organization_column : str or None, optional
        Name of the column containing organization names. Default is None (will use OrganizationEncoderSpark default).
    type_column : str or None, optional
        Name of the column containing problem types. Default is None (will use TypeEncoderSpark default).

    Attributes
    ----------
    address_encoder : AddressEncoderSpark
        The instantiated transformer for address feature hashing.
    organization_encoder : OrganizationEncoderSpark
        The instantiated transformer for organization encoding.
    type_encoder : TypeEncoderSpark
        The instantiated transformer for problem type encoding.
    """
    
    def __init__(
        self,
        district_column: str | None = None,
        subdistrict_column: str | None = None,
        latitude_column: str | None = None,
        longitude_column: str | None = None,
        address_encoded_column: str | None = None,
        latlong_encoded_column: str | None = None,
        organization_column: str | None = None,
        type_column: str | None = None,
    ) -> None:
        """
        Initializes the PySpark Encoder Pipeline by instantiating all specialized encoders.

        Parameters
        ----------
        district_column : str or None, optional
            Name of the district column used for address encoding. Default is None.
        subdistrict_column : str or None, optional
            Name of the subdistrict column used for address encoding. Default is None.
        encoded_column : str or None, optional
            Name of the output column for the address hash vector. Default is None.
        organization_column : str or None, optional
            Name of the column containing organization names. Default is None.
        type_column : str or None, optional
            Name of the column containing problem types. Default is None.
        """

        self.district_column = district_column
        self.subdistrict_column = subdistrict_column
        self.latitude_column = latitude_column
        self.longitude_column = longitude_column
        self.address_encoded_column = address_encoded_column
        self.latlong_encoded_column = latlong_encoded_column

        self.organization_column = organization_column
        self.type_column = type_column

        self.address_encoder = AddressEncoderSpark(
            district_column=self.district_column,
            subdistrict_column=self.subdistrict_column,
            latitude_column=self.latitude_column,
            longitude_column=self.longitude_column,
            address_encoded_column=self.address_encoded_column,
            latlong_encoded_column=self.latlong_encoded_column,
        )

        self.organization_encoder = OrganizationEncoderSpark(
            organization_column=self.organization_column
        )

        self.type_encoder = TypeEncoderSpark(
            type_column=self.type_column,
        )

    def _transform(self, df: DataFrame) -> DataFrame:
        """
        Sequentially applies all feature encoding steps to the input DataFrame.

        Parameters
        ----------
        df : pyspark.sql.DataFrame
            The input DataFrame containing the raw categorical columns.

        Returns
        -------
        pyspark.sql.DataFrame
            The transformed DataFrame with encoded and hash vector columns added.
        """
       
        df_transformed = self.address_encoder.transform(df)
        df_transformed = self.organization_encoder.transform(df_transformed)
        df_transformed = self.type_encoder.transform(df_transformed)

        return df_transformed
