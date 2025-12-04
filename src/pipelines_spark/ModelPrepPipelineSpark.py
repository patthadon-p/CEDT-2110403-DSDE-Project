"""
PySpark Transformer for Model Preparation Pipeline.

This module provides the ModelPrepPipelineSpark class, a PySpark ML meta-Transformer
that sequentially executes the final stages of data cleaning, feature engineering,
and feature encoding necessary to prepare a Spark DataFrame for machine learning.

Classes
-------
ModelPrepPipelineSpark
    A PySpark meta-transformer that combines filtering, feature encoding, and
    resolution time calculation into a single pipeline ready for modeling.
"""

# Import necessary modules
from pyspark.ml import Transformer
from pyspark.sql import DataFrame

# Other Transformer
from .DataFilterTransformerSpark import DataFilterTransformerSpark
from .EncoderPipelineSpark import EncoderPipelineSpark


class ModelPrepPipelineSpark(Transformer):
    """
    The main PySpark meta-transformer for preparing data for machine learning models.

    This class orchestrates a sequence of specialized transformations to ensure
    the data is clean, filtered, and all categorical features are properly encoded.

    The sequence of transformation is:
    1. **Data Filter:** Filters rows by specified values and drops raw/identifier columns.
    2. **Encoder Pipeline:** Applies feature hashing and categorical encoding (Address, Organization, Type).
    3. **Resolution Time Transformer:** Creates features related to event resolution time.

    Parameters
    ----------
    filter_columns : dict of {str: str} or None, optional
        Filtering dictionary passed to DataFilterTransformerSpark. Default is None.
    drop_columns : list or None, optional
        List of columns to be dropped, passed to DataFilterTransformerSpark. Default is None.
    district_column : str or None, optional
        District column name passed to EncoderPipelineSpark. Default is None.
    subdistrict_column : str or None, optional
        Subdistrict column name passed to EncoderPipelineSpark. Default is None.
    encoded_column : str or None, optional
        Output column name for address encoding. Default is None.
    organization_column : str or None, optional
        Organization column name for encoding. Default is None.
    type_column : str or None, optional
        Problem type column name for encoding. Default is None.
    start_date_column : str or None, optional
        Start date feature column (e.g., 'timestamp_date') passed to ResolutionTimeTransformerSpark. Default is None.
    start_month_column : str or None, optional
        Start month feature column (e.g., 'timestamp_month') passed to ResolutionTimeTransformerSpark. Default is None.
    start_year_column : str or None, optional
        Start year feature column (e.g., 'timestamp_year') passed to ResolutionTimeTransformerSpark. Default is None.
    end_date_column : str or None, optional
        End date feature column (e.g., 'last_activity_date') passed to ResolutionTimeTransformerSpark. Default is None.
    end_month_column : str or None, optional
        End month feature column (e.g., 'last_activity_month') passed to ResolutionTimeTransformerSpark. Default is None.
    end_year_column : str or None, optional
        End year feature column (e.g., 'last_activity_year') passed to ResolutionTimeTransformerSpark. Default is None.
    resolution_time_column : str or None, optional
        Output column name for the calculated resolution time feature. Default is None.

    Attributes
    ----------
    data_filter_transformer : DataFilterTransformerSpark
        Instantiated transformer for initial filtering and column dropping.
    encoder_pipeline : EncoderPipelineSpark
        Instantiated pipeline for handling all categorical feature encoding.
    resol_time_transformer : ResolutionTimeTransformerSpark
        Instantiated transformer for generating resolution time features.
    """

    def __init__(
        self,
        filter_columns: dict[str, str] | None = None,
        drop_columns: list | None = None,
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
        Initializes the PySpark Model Preparation Pipeline by instantiating sub-transformers.

        Parameters
        ----------
        filter_columns : dict of {str: str} or None, optional
            Filtering dictionary passed to DataFilterTransformerSpark. Default is None.
        drop_columns : list or None, optional
            List of columns to be dropped, passed to DataFilterTransformerSpark. Default is None.
        district_column : str or None, optional
            District column name passed to EncoderPipelineSpark. Default is None.
        subdistrict_column : str or None, optional
            Subdistrict column name passed to EncoderPipelineSpark. Default is None.
        encoded_column : str or None, optional
            Output column name for address encoding. Default is None.
        organization_column : str or None, optional
            Organization column name for encoding. Default is None.
        type_column : str or None, optional
            Problem type column name for encoding. Default is None.
        start_date_column : str or None, optional
            Start date feature column (e.g., 'timestamp_date') passed to ResolutionTimeTransformerSpark. Default is None.
        start_month_column : str or None, optional
            Start month feature column (e.g., 'timestamp_month') passed to ResolutionTimeTransformerSpark. Default is None.
        start_year_column : str or None, optional
            Start year feature column (e.g., 'timestamp_year') passed to ResolutionTimeTransformerSpark. Default is None.
        end_date_column : str or None, optional
            End date feature column (e.g., 'last_activity_date') passed to ResolutionTimeTransformerSpark. Default is None.
        end_month_column : str or None, optional
            End month feature column (e.g., 'last_activity_month') passed to ResolutionTimeTransformerSpark. Default is None.
        end_year_column : str or None, optional
            End year feature column (e.g., 'last_activity_year') passed to ResolutionTimeTransformerSpark. Default is None.
        resolution_time_column : str or None, optional
            Output column name for the calculated resolution time feature. Default is None.
        """

        self.filter_columns = filter_columns
        self.drop_columns = drop_columns

        self.district_column = district_column
        self.subdistrict_column = subdistrict_column
        self.latitude_column = latitude_column
        self.longitude_column = longitude_column
        self.address_encoded_column = address_encoded_column
        self.latlong_encoded_column = latlong_encoded_column
        self.organization_column = organization_column
        self.type_column = type_column

        self.data_filter_transformer = DataFilterTransformerSpark(
            filter_columns=self.filter_columns,
            drop_columns=self.drop_columns,
        )

        self.encoder_pipeline = EncoderPipelineSpark(
            district_column=self.district_column,
            subdistrict_column=self.subdistrict_column,
            latitude_column=self.latitude_column,
            longitude_column=self.longitude_column,
            address_encoded_column=self.address_encoded_column,
            latlong_encoded_column=self.latlong_encoded_column,
            organization_column=self.organization_column,
            type_column=self.type_column,
        )

    def _transform(self, df: DataFrame) -> DataFrame:
        """
        Sequentially applies filtering, encoding, and resolution time feature engineering to the input DataFrame.

        Parameters
        ----------
        df : pyspark.sql.DataFrame
            The input DataFrame.

        Returns
        -------
        pyspark.sql.DataFrame
            The transformed DataFrame ready for use in a machine learning model.
        """

        df_transformed = self.data_filter_transformer.transform(df)
        df_transformed = self.encoder_pipeline.transform(df_transformed)

        return df_transformed
