"""
Bangkok Index data scraping and cleaning utilities.

This module provides the BangkokIndexScrapping class, designed to fetch,
parse, and clean administrative data (e.g., district rankings/scores)
from a public Google Sheet URL, handling common encoding and structure
issues inherent in raw data sources.

Classes
-------
BangkokIndexScrapping
    A utility class that scrapes data from a predefined URL, cleans column
    names, standardizes district names, converts columns to numeric types,
    and returns a clean DataFrame.
"""

# Import necessary modules
import json
from io import BytesIO
from pathlib import Path
from typing import Any

import pandas as pd
import requests

# Utility functions
from src.utils.ConfigUtils import get_data_dir, read_config_path


class BangkokIndexScrapping:
    """
    Handles scraping, loading, and cleaning of Bangkok Index data (e.g., district scores).

    The class initializes configuration from a JSON file, constructs the target
    URL, fetches the CSV data (typically a Google Sheet export), and applies
    multiple cleaning steps including column alignment, type casting, prefix
    removal, and final column renaming.

    Parameters
    ----------
    url : str, optional
        A custom base URL to override the one specified in the configuration file.
        Default is "".

    Attributes
    ----------
    config_path : str
        Path to the configuration JSON file.
    config : dict
        The full configuration dictionary loaded from the JSON file.
    url : str
        The base URL for the data source.
    target_url : str
        The specific Google Sheet URL used to fetch the raw CSV data.
    COLUMNS_TO_DROP_BY_NAME : list of str
        List of column names derived from index that should be dropped.
    COLUMNS_RENAME_MAPPING : dict
        Dictionary for renaming final columns.
    DISTRICT_NAME_COLUMN_INDEX : int
        Index of the column containing the district name.
    DISTRICT_REMOVE_PREFIX : list of str
        List of prefixes to remove from district names (e.g., 'เขต').
    COLUMN_NAMES : list of str
        The expected list of final column names.
    NUMERIC_COLUMNS : list of str
        List of columns expected to be converted to numeric type.
    data_frame : pandas.DataFrame
        The DataFrame storing the scraped and cleaned data.
    """
    
    def __init__(self, url: str = "") -> None:

        self.config_path = read_config_path(
            domain="scrapping", key="bangkok_index_scrapping_path"
        )

        with open(self.config_path, encoding="utf-8") as file:
            config = json.load(file)

        self.config: dict[str, Any] = config

        self.url = url or self.config.get("base_url", "")
        self.target_url = self.config.get("sheet_url", "")

        cols = self.config.get("COLUMN_NAMES", [])
        drop_indices = self.config.get("TO_DROP_COLUMNS_INDEX", [])
        self.COLUMNS_TO_DROP_BY_NAME = [cols[i] for i in drop_indices if i < len(cols)]

        self.COLUMNS_RENAME_MAPPING = self.config.get("COLUMNS_RENAME_MAPPING", {})

        self.DISTRICT_NAME_COLUMN_INDEX = self.config.get(
            "DISTRICT_NAME_COLUMN_INDEX", 1
        )
        self.DISTRICT_REMOVE_PREFIX = self.config.get("DISTRICT_REMOVE_PREFIX", [])
        self.COLUMN_NAMES = self.config.get("COLUMN_NAMES", [])
        self.NUMERIC_COLUMNS = self.config.get("NUMERIC_COLUMNS", [])

        self.data_frame: pd.DataFrame = pd.DataFrame()

    def _fetch_file(self) -> bytes | None:
        """
        Fetches the raw CSV data file from the target URL (Google Sheet export).

        Returns
        -------
        bytes or None
            The content of the CSV file as raw bytes if successful, otherwise None.
        """
        
        try:
            headers = {"User-Agent": "Mozilla/5.0"}
            response = requests.get(self.target_url, timeout=60, headers=headers)
            response.raise_for_status()
            return response.content
        except requests.exceptions.RequestException:
            return None

    def _load_data(self, file_bytes: bytes) -> pd.DataFrame | None:
        """
        Loads the raw file bytes into a pandas DataFrame and attempts to correct
        character encoding issues.

        The data is assumed to be comma-separated. It attempts to load with
        'latin-1' encoding and then re-encodes/decodes columns to mitigate
        common UTF-8 errors in Google Sheet exports.

        Parameters
        ----------
        file_bytes : bytes
            The raw content of the data file.

        Returns
        -------
        pandas.DataFrame or None
            A DataFrame containing the loaded data with attempted encoding correction,
            or None if a critical Unicode encoding error occurs.
        """
        
        try:
            file_like_object = BytesIO(file_bytes)
            df = pd.read_csv(
                file_like_object, encoding="latin-1", dtype=str, sep=",", header=None
            )

            for col in df.columns:
                try:
                    df[col] = (
                        df[col]
                        .astype(str)
                        .str.encode("latin1")
                        .str.decode("utf-8", errors="ignore")
                    )
                except UnicodeEncodeError:
                    return None

            return df

        except Exception:
            return None

    def _run_scraper(self) -> pd.DataFrame:
        """
        Coordinates the fetching and initial loading of the data.

        Returns
        -------
        pandas.DataFrame
            The raw DataFrame if fetching and loading were successful, otherwise
            an empty DataFrame.
        """
        
        file_bytes = self._fetch_file()

        if file_bytes is None:
            return pd.DataFrame()

        df = self._load_data(file_bytes)

        if df is None:
            return pd.DataFrame()

        return df

    def fetch_and_clean(
        self, save_to_csv: bool = False, save_path: str = "", file_name: str = ""
    ) -> pd.DataFrame:
        """
        Fetches the raw data, cleans it, standardizes columns, casts numeric types,
        and optionally saves the final DataFrame to a CSV file.

        The cleaning steps include:
        1. Dropping initial header rows (keeping rows from index 2 onwards).
        2. Aligning and assigning column names based on configuration.
        3. Removing configured prefixes (e.g., 'เขต') from the district name column.
        4. Dropping columns and rows based on configuration and calculated criteria.
        5. Converting specified columns to numeric types.
        6. Performing final renaming to simplify column headers (removing '/คะแนน').

        Parameters
        ----------
        save_to_csv : bool, optional
            If True, the cleaned DataFrame is saved to a CSV file. Defaults to False.
        save_path : str, optional
            The base directory path to save the CSV file. If empty, the path is
            derived from `get_data_dir()`. Default is "".
        file_name : str, optional
            The name of the CSV file. If empty, defaults to "bangkok_index_district_final.csv".

        Returns
        -------
        pandas.DataFrame
            The final, cleaned, and processed DataFrame, or an empty DataFrame
            if the data fetching or loading failed.
        """

        df = self._run_scraper().copy()

        if df.empty:
            return pd.DataFrame()

        if len(df) > 2:
            df = df.iloc[2:].reset_index(drop=True)
        else:
            return pd.DataFrame()

        expected_len = len(self.COLUMN_NAMES)
        current_len = len(df.columns)

        if expected_len == current_len:
            df.columns = self.COLUMN_NAMES
        else:
            if expected_len > current_len:
                df.columns = self.COLUMN_NAMES[:current_len]
            else:
                df = df.iloc[:, :expected_len]
                df.columns = self.COLUMN_NAMES

        district_col = self.COLUMN_NAMES[self.DISTRICT_NAME_COLUMN_INDEX]

        for prefix in self.DISTRICT_REMOVE_PREFIX:
            df[district_col] = (
                df[district_col]
                .astype(str)
                .str.replace(prefix, "", regex=False)
                .str.strip()
            )

        df = df[df[district_col].str.strip() != ""]
        df = df.drop(columns=self.COLUMNS_TO_DROP_BY_NAME, errors="ignore")

        for col in self.NUMERIC_COLUMNS:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce")

        df = df.dropna().reset_index(drop=True)

        to_drop_columns = ["Overall_Rank"] + [
            col for col in df.columns if "/อันดับ" in col
        ]
        df = df.drop(columns=to_drop_columns, errors="ignore")

        rename_mapping = {col: col.replace("/คะแนน", "") for col in df.columns}

        df = df.rename(columns=rename_mapping)
        df = df.rename(columns=self.COLUMNS_RENAME_MAPPING)

        self.data_frame = df.copy()

        if save_to_csv:
            save_path = save_path or str(get_data_dir() / "scrapped" / file_name)

            file_name = file_name or "bangkok_index_district_final.csv"

            final_path = Path(save_path) / file_name
            final_path.parent.mkdir(parents=True, exist_ok=True)

            df.to_csv(final_path, index=False, encoding="utf-8-sig")

        return df
