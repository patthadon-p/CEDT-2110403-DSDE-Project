import matplotlib.pyplot as plt
import pandas as pd

class LineChartVisualizer:
    def __init__(self, df: pd.DataFrame) -> None:
        self.df = df.copy()
        self.df = self.df.explode("type_cleaned")
        self.df["type_cleaned"] = self.df["type_cleaned"].str.strip()

        if "timestamp_year" not in self.df.columns:
            raise ValueError("DataFrame must have a 'timestamp_year' column.")

    def plot(self):
        df_grouped = self.df.groupby(["timestamp_year", "type_cleaned"]).size().reset_index(name="count")
        df_pivot = df_grouped.pivot(index="timestamp_year", columns="type_cleaned", values="count").fillna(0)

        fig, ax = plt.subplots(figsize=(10, 6))

        for problem_type in df_pivot.columns:
            ax.plot(df_pivot.index, df_pivot[problem_type], marker='o', linestyle='-', label=problem_type)

        ax.set_title("Problem Counts by Type (2021-2025)")
        ax.set_xlabel("Year")
        ax.set_ylabel("Count")
        ax.set_xticks(df_pivot.index)
        ax.grid(True)
        ax.legend(title="Problem Type")

        return fig
