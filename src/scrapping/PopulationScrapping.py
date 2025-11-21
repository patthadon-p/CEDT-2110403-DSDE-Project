"""
Data scraping and cleaning utilities for DOPA population statistics.

This module provides the PopulationScrapping class, which is responsible
for configuring the scraping process, constructing the target URL for
specific administrative levels and years (Buddhist calendar), downloading
the raw data file, and performing comprehensive data cleaning and
normalization before outputting the final pandas DataFrame.

Classes
-------
PopulationScrapping
    A class designed to fetch, load, clean, and standardize population
    data from the Department of Provincial Administration (DOPA) website.
"""

# Import necessary modules
import json
from io import BytesIO

import pandas as pd
import requests

# Utility functions
from src.utils.ConfigUtils import get_data_dir, read_config_path
from src.utils.DatetimeUtils import get_buddhist_year


class PopulationScrapping:
    """
    Handles scraping, loading, and cleaning of population data from the
    Department of Provincial Administration (DOPA) website.

    This class initializes configuration based on a JSON file, constructs the
    target URL for a specific administrative level and year (Buddhist calendar),
    fetches the data file, and performs data cleaning and transformation
    before returning the final DataFrame.

    Parameters
    ----------
    url : str, optional
        Base URL for the DOPA population data. Defaults to the value in the config file.
    year : int or str or None, optional
        The year of the data to fetch (in Buddhist calendar). Defaults to the
        current Buddhist year.
    level : str, optional
        The administrative level of the data (e.g., 'province', 'district').
        Defaults to the value in the config file.

    Attributes
    ----------
    population_scrapping_path : str
        Path to the configuration JSON file.
    url : str
        The base URL used for scraping.
    level : str
        The administrative level currently being processed.
    level_code : str
        The DOPA code corresponding to the administrative level.
    level_priority : int
        The priority level of the administrative level (used for cleaning).
    year : str
        The target year (Buddhist calendar) for the data.
    year_last_two_digits : str
        The last two digits of the target year.
    target_url : str
        The final full URL constructed to fetch the data file.
    data_frame : pandas.DataFrame
        The DataFrame storing the scraped and cleaned data.
    LEVELS : list of str
        Class attribute: List of available administrative levels.
    LEVEL_PRIORITY : dict of str: int
        Class attribute: Mapping of administrative level to its priority.
    LEVEL_CODE_MAPPING : dict of str: str
        Class attribute: Mapping of administrative level to its DOPA code.
    LEVEL_REMOVE_PREFIX : dict of str: list of str
        Class attribute: Mapping of administrative level to list of prefixes to remove from names.
    COLUMNS : list of str
        Class attribute: List of column names to apply to the scraped data.
    TO_DROP_COLUMNS : list of str
        Class attribute: List of column names to drop during cleaning.
    """

    def __init__(
        self,
        url: str = "",
        year: int | str | None = None,
        level: str = "",
    ) -> None:

        self.population_scrapping_path = read_config_path(
            domain="scrapping", key="population_scrapping_path"
        )

        with open(self.population_scrapping_path, encoding="utf-8") as file:
            population_scrapping = json.load(file)

        PopulationScrapping.LEVELS: list[str] = list(
            population_scrapping["levels"].keys()
        )

        # Priority mapping for administrative levels
        PopulationScrapping.LEVEL_PRIORITY: dict[str, int] = {
            level: obj["priority"]
            for level, obj in population_scrapping["levels"].items()
        }

        # Code mapping for administrative levels
        PopulationScrapping.LEVEL_CODE_MAPPING: dict[str, str] = {
            level: obj["code"] for level, obj in population_scrapping["levels"].items()
        }

        PopulationScrapping.LEVEL_REMOVE_PREFIX: dict[str, list[str]] = {
            level: obj["remove_prefix"]
            for level, obj in population_scrapping["levels"].items()
        }

        # Columns present in the population data file
        PopulationScrapping.COLUMNS: list[str] = list(
            population_scrapping["columns_name"].keys()
        )

        # Columns to drop from the population data file
        PopulationScrapping.TO_DROP_COLUMNS: list[str] = [
            column
            for column, obj in population_scrapping["columns_name"].items()
            if obj["drop"].lower() == "true"
        ]

        PopulationScrapping.DTYPE_MAPPING: dict[str, str] = {
            column: obj["dtype"]
            for column, obj in population_scrapping["columns_name"].items()
            if obj["drop"].lower() == "false"
        }

        self.url = url or population_scrapping["base_url"]

        self.level = level or population_scrapping["default_level"].strip().lower()
        self.level_code = population_scrapping["levels"][self.level]["code"]
        self.level_priority = population_scrapping["levels"][self.level]["priority"]

        self.year = str(year) if year is not None else get_buddhist_year()
        self.year_last_two_digits = self.year[-2:]

        self.level_code = PopulationScrapping.LEVEL_CODE_MAPPING.get(
            self.level, self.level_code
        )

        self.target_url = (
            f"https://stat.bora.dopa.go.th/new_stat/file/{self.year_last_two_digits}/"
            f"stat_{self.level_code}{self.year_last_two_digits}.txt"
        )

        self.data_frame: pd.DataFrame = pd.DataFrame()

    def _fetch_file(self) -> bytes | None:
        """
        Fetches the population data file from the constructed target URL.

        It attempts to download the file using an HTTP GET request.

        Returns
        -------
        bytes or None
            The content of the file as raw bytes if successful, otherwise None
            if a request error occurs.
        """

        try:
            response = requests.get(self.target_url, timeout=60)
            response.raise_for_status()
            return response.content

        except requests.exceptions.RequestException:
            return None

    def _load_data(self, file_bytes: bytes) -> pd.DataFrame | None:
        """
        Loads the raw file bytes into a pandas DataFrame.

        The data is assumed to be a pipe-separated (|) file without a header,
        and all columns are loaded as string type.

        Parameters
        ----------
        file_bytes : bytes
            The raw content of the data file.

        Returns
        -------
        pandas.DataFrame or None
            A DataFrame containing the loaded data, or None if an error occurs
            during the loading process.
        """

        try:
            file_like_object = BytesIO(file_bytes)
            df = pd.read_csv(
                file_like_object, encoding="utf-8", dtype=str, sep="|", header=None
            )
            return df

        except Exception:
            return None

    def _run_scraper(self) -> pd.DataFrame:
        """
        Coordinates the fetching and initial loading of the data.

        It attempts to fetch the file and, if successful, loads it into
        `self.data_frame` and assigns column names.

        Returns
        -------
        pandas.DataFrame
            The raw DataFrame with assigned column names, or an empty DataFrame
            if the file could not be fetched or loaded.
        """

        file_bytes = self._fetch_file()

        if file_bytes:
            loaded_data = pd.DataFrame(self._load_data(file_bytes))

            self.data_frame = (
                loaded_data if loaded_data is not None else self.data_frame
            )

            self.data_frame.columns = PopulationScrapping.COLUMNS
        else:
            self.data_frame = pd.DataFrame()

        return self.data_frame

    def _save_to_csv(
        self, df: pd.DataFrame, save_path: str = "", file_name: str = ""
    ) -> None:
        """
        Saves the processed DataFrame to a CSV file.

        Parameters
        ----------
        df : pandas.DataFrame
            The DataFrame to be saved.
        save_path : str, optional
            The full path (including directory and file name) where the file
            should be saved. If not provided, a default path relative to the
            script location is used.
        file_name : str, optional
            The name of the CSV file. If not provided, it defaults to
            "population_{level}_{year}.csv".

        Returns
        -------
        None
        """

        file_name = file_name or f"population_{self.level}_{self.year}.csv"

        save_path = save_path or str(get_data_dir() / "scrapped" / file_name)

        df.to_csv(save_path, index=False)
        return None

    def fetch_and_clean(
        self, save_to_csv: bool = False, save_path: str = "", file_name: str = ""
    ) -> pd.DataFrame:
        """
        Fetches the data, performs cleaning, normalization, and optional saving.

        The cleaning steps include:
        1. Dropping specified columns.
        2. Filtering out rows where administrative names (up to the current level) are blank.
        3. Removing specified prefixes (e.g., 'จังหวัด', 'อำเภอ') from administrative names.
        4. Dropping administrative name columns that are at a lower priority than the target level.

        Parameters
        ----------
        save_to_csv : bool, optional
            If True, the cleaned DataFrame is saved to a CSV file. Defaults to False.
        save_path : str, optional
            The path to save the CSV file (used only if `save_to_csv` is True).
        file_name : str, optional
            The name of the CSV file (used only if `save_to_csv` is True).

        Returns
        -------
        pandas.DataFrame
            The final, cleaned, and processed DataFrame.
        """

        df = self._run_scraper().copy()
        df = df.drop(columns=PopulationScrapping.TO_DROP_COLUMNS)

        check_blank_boolean = {
            level: df[f"{level}-name"].str.strip() == ""
            for level in PopulationScrapping.LEVELS
        }

        query_condition = pd.Series([False] * len(df))

        for level in PopulationScrapping.LEVELS:
            if PopulationScrapping.LEVEL_PRIORITY[level] <= self.level_priority:
                query_condition = query_condition | check_blank_boolean[level]
                for prefix in PopulationScrapping.LEVEL_REMOVE_PREFIX[level]:
                    df[f"{level}-name"] = (
                        df[f"{level}-name"]
                        .str.replace(prefix, "", regex=False)
                        .str.strip()
                    )
            else:
                df = df.drop(columns=[f"{level}-name"])
                PopulationScrapping.DTYPE_MAPPING.pop(f"{level}-name", None)

        df = df[~query_condition]

        df = df.dropna()
        df = df.reset_index(drop=True)

        for col, dtype in PopulationScrapping.DTYPE_MAPPING.items():
            if dtype == "int":
                df[col] = df[col].apply(lambda x: int(str(x).replace(",", "")))

        self.data_frame = df.copy()

        if save_to_csv:
            self._save_to_csv(df, save_path, file_name)

        return self.data_frame
