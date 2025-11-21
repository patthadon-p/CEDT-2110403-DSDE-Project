import pandas as pd
import matplotlib
matplotlib.use("TkAgg") 
import matplotlib.pyplot as plt

class LineChartVisualizer:
    def __init__(self, df):
        self.df = df.copy()

        # Clean the 'type' column into 'type_clean'
        self.df["type_clean"] = (
            self.df["type"]
            .astype(str)
            .str.replace("{", "")
            .str.replace("}", "")
            .str.split(",")
        )
        self.df = self.df.explode("type_clean")
        self.df["type_clean"] = self.df["type_clean"].str.strip()

        # Ensure timestamp_year column exists
        if "timestamp_year" not in self.df.columns:
            raise ValueError("DataFrame must have a 'timestamp_year' column.")

    def plot(self):
        # Filter for years 2021-2025
        df_filtered = self.df[self.df["timestamp_year"].between(2021, 2025)]

        # Group by year and type, count occurrences
        df_grouped = df_filtered.groupby(["timestamp_year", "type_clean"]).size().reset_index(name="count")

        # Pivot for plotting: rows = year, columns = type, values = count
        df_pivot = df_grouped.pivot(index="timestamp_year", columns="type_clean", values="count").fillna(0)

        # Plot each type as a line
        plt.figure(figsize=(10,6))
        for problem_type in df_pivot.columns:
            plt.plot(df_pivot.index, df_pivot[problem_type], marker='o', linestyle='-', label=problem_type)

        plt.title("Problem Counts by Type (2021-2025)")
        plt.xlabel("Year")
        plt.ylabel("Count")
        plt.xticks(df_pivot.index)  # ensure all years are shown
        plt.legend(title="Problem Type")
        plt.grid(True)
        plt.savefig("../data/visualize/problem_counts.png", dpi=300, bbox_inches="tight")
