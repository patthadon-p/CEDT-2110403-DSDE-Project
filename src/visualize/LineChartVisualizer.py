"""
Line chart visualization utilities.

This module provides the LineChartVisualizer class, designed to generate
a multi-series line chart using Matplotlib. It visualizes the trend of
different categories (problem types) over time (by year).

Classes
-------
LineChartVisualizer
    A class for preparing data and generating a line chart to show the
    yearly trend of event counts for different problem types.
"""

# Import necessary libraries
import matplotlib.pyplot as plt
import pandas as pd
from matplotlib import rcParams
from matplotlib.figure import Figure

rcParams["font.family"] = "Tahoma"


class LineChartVisualizer:
    """
    Generates a multi-series line chart visualizing the count of problem types over years.

    The input DataFrame is expected to contain a list of categories in the
    'type_cleaned' column, which is exploded upon initialization.

    Parameters
    ----------
    df : pandas.DataFrame
        The input DataFrame containing, at a minimum, the 'timestamp_year'
        and 'type_cleaned' columns.

    Attributes
    ----------
    df : pandas.DataFrame
        The processed copy of the input DataFrame with the 'type_cleaned'
        column exploded and standardized.

    Raises
    ------
    ValueError
        If the input DataFrame is missing the required 'timestamp_year' column.
    """

    def __init__(self, df: pd.DataFrame) -> None:
        """
        Initializes the visualizer, preprocesses the DataFrame, and explodes
        the categorical columns.

        Parameters
        ----------
        df : pandas.DataFrame
            The input DataFrame containing, at a minimum, the 'timestamp_year'
            and 'type_cleaned' columns.
        """

        self.df = df.copy()
        self.df = self.df.explode("type_cleaned")
        self.df["type_cleaned"] = self.df["type_cleaned"].str.strip()

        if "timestamp_year" not in self.df.columns:
            raise ValueError("DataFrame must have a 'timestamp_year' column.")

    def plot(self, figsize: tuple = (12, 6)) -> Figure:
        """
        Generates and returns the Matplotlib Figure containing the line chart.

        The data is grouped by year and problem type, pivoted, and plotted as
        multiple line series showing trends from 2021-2025.

        Parameters
        ----------
        figsize : tuple, optional
            The size of the output figure (width, height) in inches. Default is (12, 6).

        Returns
        -------
        matplotlib.figure.Figure
            The generated Matplotlib figure object.
        """

        df_grouped = (
            self.df.groupby(["timestamp_year", "type_cleaned"])
            .size()
            .reset_index(name="count")
        )
        df_pivot = df_grouped.pivot_table(
            index="timestamp_year", columns="type_cleaned", values="count"
        ).fillna(0)

        fig, ax = plt.subplots(figsize=figsize)

        cmap = plt.cm.get_cmap("tab20")
        colors = [cmap(i) for i in range(cmap.N)]
        fig, ax = plt.subplots(figsize=figsize)

        for i, problem_type in enumerate(df_pivot.columns):
            color = colors[i % len(colors)]
            ax.plot(
                df_pivot.index,
                df_pivot[problem_type],
                marker="o",
                linestyle="-",
                label=problem_type,
                color=color,
            )

        ax.set_title("Problem Counts by Type (2021-2025)")
        ax.set_xlabel("Year")
        ax.set_ylabel("Count")
        ax.set_xticks(df_pivot.index)
        ax.grid(True)
        ax.legend(title="Problem Type")

        return fig
