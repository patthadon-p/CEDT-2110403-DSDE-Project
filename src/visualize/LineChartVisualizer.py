import matplotlib.pyplot as plt
import pandas as pd

from matplotlib import rcParams

rcParams['font.family'] = 'Tahoma'

class LineChartVisualizer:
    def __init__(self, df: pd.DataFrame) -> None:
        self.df = df.copy()
        self.df = self.df.explode("type_cleaned")
        self.df["type_cleaned"] = self.df["type_cleaned"].str.strip()

        if "timestamp_year" not in self.df.columns:
            raise ValueError("DataFrame must have a 'timestamp_year' column.")

    def plot(self, figsize=(12, 6)):
        df_grouped = self.df.groupby(["timestamp_year", "type_cleaned"]).size().reset_index(name="count")
        df_pivot = df_grouped.pivot(index="timestamp_year", columns="type_cleaned", values="count").fillna(0)

        fig, ax = plt.subplots(figsize=figsize)

        colors = plt.cm.tab20.colors 
        fig, ax = plt.subplots(figsize=figsize)

        for i, problem_type in enumerate(df_pivot.columns):
            color = colors[i % len(colors)] 
            ax.plot(df_pivot.index, df_pivot[problem_type], marker='o', linestyle='-', label=problem_type, color=color)

        ax.set_title("Problem Counts by Type (2021-2025)")
        ax.set_xlabel("Year")
        ax.set_ylabel("Count")
        ax.set_xticks(df_pivot.index)
        ax.grid(True)
        ax.legend(title="Problem Type")

        return fig

