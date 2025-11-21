import pandas as pd
import matplotlib.pyplot as plt

class LineChartVisualizer:
    def __init__(self, df):
        self.df = df.copy()
        self.df["type_clean"] = (
            self.df["type"]
            .astype(str)
            .str.replace("{", "")
            .str.replace("}", "")
            .str.split(",")
        )
        self.df = self.df.explode("type_clean")
        self.df["type_clean"] = self.df["type_clean"].str.strip()

        if "timestamp_year" not in self.df.columns:
            raise ValueError("DataFrame must have a 'timestamp_year' column.")

    def plot(self):
        df_grouped = self.df.groupby(["timestamp_year", "type_clean"]).size().reset_index(name="count")
        df_pivot = df_grouped.pivot(index="timestamp_year", columns="type_clean", values="count").fillna(0)

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
