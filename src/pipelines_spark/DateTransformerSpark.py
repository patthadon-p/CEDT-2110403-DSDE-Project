"""
PySpark Transformer for Datetime Feature Engineering.

This module provides the DateTransformerSpark class, a PySpark ML Transformer
designed to convert timestamp columns to a standardized format, extract temporal
features (year, month, day), and calculate the difference between two timestamps
(resolution time).

Classes
-------
DateTransformerSpark
    A PySpark ML Transformer that standardizes and extracts temporal features
    from specified timestamp columns, and calculates time differences.
"""

# Import necessary modules
from pyspark.ml import Transformer
from pyspark.sql import DataFrame
from pyspark.sql.functions import col, date_diff, dayofmonth, month, to_timestamp, year


class DateTransformerSpark(Transformer):
    """
    Converts specified timestamp columns to PySpark datetime objects, extracts
    temporal features, and calculates the time difference between the start and end columns.

    For each specified start and end column:
    1. Converts the column to a PySpark TimestampType (`to_timestamp`).
    2. Extracts and creates three new **Integer** columns: `_date`, `_month`, and `_year`.
    3. Calculates the difference in **days** between the end time and the start time (`date_diff`).
    4. Drops the original timestamp columns.

    Parameters
    ----------
    start_time_column : str or None, optional
        Name of the column containing the start timestamp. Defaults to "timestamp".
    end_time_column : str or None, optional
        Name of the column containing the end/resolution timestamp. Defaults to "last_activity".

    Attributes
    ----------
    start_time_column : str
        The final name of the start timestamp column.
    end_time_column : str
        The final name of the end timestamp column.
    resolution_time_column : str
        The name of the output column for the time difference (in days). Defaults to "resolution_time".
    """

    def __init__(
        self, start_time_column: str | None = None, end_time_column: str | None = None
    ) -> None:
        """
        Initializes the PySpark Date Transformer and sets the target column names.

        Parameters
        ----------
        start_time_column : str or None, optional
            Name of the column containing the start timestamp. Defaults to "timestamp".
        end_time_column : str or None, optional
            Name of the column containing the end/resolution timestamp. Defaults to "last_activity".
        """

        self.start_time_column = start_time_column or "timestamp"
        self.end_time_column = end_time_column or "last_activity"
        self.resolution_time_column = "resolution_time"

    def _transform(self, df: DataFrame) -> DataFrame:
        """
        Applies timestamp conversion, feature extraction, and resolution time calculation
        to the input DataFrame.

        Parameters
        ----------
        df : pyspark.sql.DataFrame
            The input DataFrame containing the timestamp columns.

        Returns
        -------
        pyspark.sql.DataFrame
            The transformed DataFrame with new temporal features and the resolution time column,
            and the original timestamp columns dropped.
        """

        for c in [self.start_time_column, self.end_time_column]:
            if c in df.columns:
                df = df.withColumn(c, to_timestamp(col(c)))

                df = df.withColumn(f"{c}_date", dayofmonth(col(c)))
                df = df.withColumn(f"{c}_month", month(col(c)))
                df = df.withColumn(f"{c}_year", year(col(c)))

        df = df.withColumn(
            self.resolution_time_column,
            date_diff(end=self.end_time_column, start=self.start_time_column),
        )
        df = df.drop(self.start_time_column, self.end_time_column)

        return df
