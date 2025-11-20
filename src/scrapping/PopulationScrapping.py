# Import necessary modules
import json
from io import BytesIO
from pathlib import Path

import pandas as pd
import requests

# Utility functions
from src.utils.ConfigUtils import read_config_path
from src.utils.DatetimeUtils import get_buddhist_year


class PopulationScrapping:
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
            for column, to_keep in population_scrapping["columns_name"].items()
            if to_keep.lower() == "false"
        ]

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
        try:
            response = requests.get(self.target_url, timeout=60)
            response.raise_for_status()
            return response.content

        except requests.exceptions.RequestException:
            return None

    def _load_data(self, file_bytes: bytes) -> pd.DataFrame | None:
        try:
            file_like_object = BytesIO(file_bytes)
            df = pd.read_csv(
                file_like_object, encoding="utf-8", dtype=str, sep="|", header=None
            )
            return df

        except Exception:
            return None

    def _run_scraper(self) -> pd.DataFrame:
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
        file_name = file_name or f"population_{self.level}_{self.year}.csv"

        save_path = save_path or str(
            Path(__file__).resolve().parents[2] / "data" / "scrapped" / file_name
        )

        df.to_csv(save_path, index=False)
        return None

    def fetch_and_clean(
        self, save_to_csv: bool = False, save_path: str = "", file_name: str = ""
    ) -> pd.DataFrame:
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

        df = df[~query_condition]

        df = df.dropna()
        df = df.reset_index(drop=True)

        self.data_frame = df.copy()

        if save_to_csv:
            self._save_to_csv(df, save_path, file_name)

        return self.data_frame
