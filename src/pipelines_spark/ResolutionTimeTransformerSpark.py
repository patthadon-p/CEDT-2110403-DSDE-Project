"""
PySpark Transformer for Resolution Time Calculation.

This module provides the ResolutionTimeTransformerSpark class, a PySpark ML Transformer
designed to calculate the time difference (in days) between a start date and an
end date, where the date components (year, month, day) are provided in separate columns.
This is used to derive a key feature (time-to-resolution) for modeling.

Classes
-------
ResolutionTimeTransformerSpark
    A PySpark ML Transformer that reconstructs full dates from component columns
    and calculates the date difference, dropping the original component columns afterwards.
"""

# Import necessary modules

from pyspark.ml import Transformer
from pyspark.sql import DataFrame
from pyspark.sql import functions as F


class ResolutionTimeTransformerSpark(Transformer):
    """
    Reconstructs full dates from separate year, month, and day columns and calculates
    the resolution time (difference in days) between the start and end events.

    The process involves:
    1. Concatenating year, month, and day columns into a valid date string ('YYYY-MM-DD').
    2. Converting the string to a PySpark DateType.
    3. Calculating the difference in days using `F.datediff`.
    4. Dropping the original date component columns.

    Parameters
    ----------
    start_date_column : str or None, optional
        Name of the column containing the start date (day). Defaults to "timestamp_date".
    start_month_column : str or None, optional
        Name of the column containing the start month. Defaults to "timestamp_month".
    start_year_column : str or None, optional
        Name of the column containing the start year. Defaults to "timestamp_year".
    end_date_column : str or None, optional
        Name of the column containing the end date (day). Defaults to "last_activity_date".
    end_month_column : str or None, optional
        Name of the column containing the end month. Defaults to "last_activity_month".
    end_year_column : str or None, optional
        Name of the column containing the end year. Defaults to "last_activity_year".
    output_col : str or None, optional
        Name of the output column for the time difference in days. Defaults to "resolution_time".

    Attributes
    ----------
    start_date_column : str
        The final name of the start date column (day).
    start_month_column : str
        The final name of the start month column.
    start_year_column : str
        The final name of the start year column.
    end_date_column : str
        The final name of the end date column (day).
    end_month_column : str
        The final name of the end month column.
    end_year_column : str
        The final name of the end year column.
    output_col : str
        The final name of the resolution time column.
    """
    
    def __init__(
        self,
        start_date_column: str | None = None,
        start_month_column: str | None = None,
        start_year_column: str | None = None,
        end_date_column: str | None = None,
        end_month_column: str | None = None,
        end_year_column: str | None = None,
        output_col: str | None = None,
    ) -> None:
        """
        Initializes the PySpark Resolution Time Transformer.

        Parameters
        ----------
        start_date_column : str or None, optional
            Name of the column containing the start date (day). Defaults to "timestamp_date".
        start_month_column : str or None, optional
            Name of the column containing the start month. Defaults to "timestamp_month".
        start_year_column : str or None, optional
            Name of the column containing the start year. Defaults to "timestamp_year".
        end_date_column : str or None, optional
            Name of the column containing the end date (day). Defaults to "last_activity_date".
        end_month_column : str or None, optional
            Name of the column containing the end month. Defaults to "last_activity_month".
        end_year_column : str or None, optional
            Name of the column containing the end year. Defaults to "last_activity_year".
        output_col : str or None, optional
            Name of the output column for the time difference in days. Defaults to "resolution_time".
        """
        
        self.start_date_column = start_date_column or "timestamp_date"
        self.start_month_column = start_month_column or "timestamp_month"
        self.start_year_column = start_year_column or "timestamp_year"

        self.end_date_column = end_date_column or "last_activity_date"
        self.end_month_column = end_month_column or "last_activity_month"
        self.end_year_column = end_year_column or "last_activity_year"

        self.output_col = output_col or "resolution_time"

    def _transform(self, df: DataFrame) -> DataFrame:
        """
        Applies date reconstruction and date difference calculation.

        Parameters
        ----------
        df : pyspark.sql.DataFrame
            The input DataFrame containing the date component columns.

        Returns
        -------
        pyspark.sql.DataFrame
            The transformed DataFrame with the new resolution time feature and
            the original date component columns dropped.
        """
        
        # Build start date string
        start_date_str = F.concat_ws(
            "-",
            F.col(self.start_year_column),
            F.lpad(F.col(self.start_month_column), 2, "0"),
            F.lpad(F.col(self.start_date_column), 2, "0"),
        )

        # Build end date string
        end_date_str = F.concat_ws(
            "-",
            F.col(self.end_year_column),
            F.lpad(F.col(self.end_month_column), 2, "0"),
            F.lpad(F.col(self.end_date_column), 2, "0"),
        )

        # Convert strings to DateType
        start_date = F.to_date(start_date_str, "yyyy-MM-dd")
        end_date = F.to_date(end_date_str, "yyyy-MM-dd")

        # Add the difference column
        df = df.withColumn(self.output_col, F.datediff(end_date, start_date))

        df_transformed = df.drop(
            self.start_date_column,
            self.end_date_column,
            self.end_month_column,
            self.end_year_column,
        )

        return df_transformed
