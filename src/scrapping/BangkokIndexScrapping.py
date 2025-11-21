# Import necessary modules
import json
from io import BytesIO
from pathlib import Path
from typing import Any

import pandas as pd
import requests

# Utility functions
from src.utils.ConfigUtils import read_config_path


class BangkokIndexScrapping:

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

        self.DISTRICT_NAME_COLUMN_INDEX = self.config.get(
            "DISTRICT_NAME_COLUMN_INDEX", 1
        )
        self.DISTRICT_REMOVE_PREFIX = self.config.get("DISTRICT_REMOVE_PREFIX", [])
        self.COLUMN_NAMES = self.config.get("COLUMN_NAMES", [])
        self.NUMERIC_COLUMNS = self.config.get("NUMERIC_COLUMNS", [])

        self.data_frame: pd.DataFrame = pd.DataFrame()

    def _fetch_file(self) -> bytes | None:
        try:
            headers = {"User-Agent": "Mozilla/5.0"}
            response = requests.get(self.target_url, timeout=60, headers=headers)
            response.raise_for_status()
            return response.content
        except requests.exceptions.RequestException:
            return None

    def _load_data(self, file_bytes: bytes) -> pd.DataFrame | None:
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

        df.insert(0, "จังหวัด", "กรุงเทพมหานคร")

        district_col_final = "เขต"
        cols = ["จังหวัด", district_col_final] + [
            col for col in df.columns if col not in ("จังหวัด", district_col_final)
        ]
        df = df[cols]

        self.data_frame = df.copy()

        if save_to_csv:
            save_path = save_path or str(
                Path(__file__).resolve().parents[2] / "data" / "scrapped" / file_name
            )

            file_name = file_name or "bangkok_index_district_final.csv"

            final_path = Path(save_path) / file_name
            final_path.parent.mkdir(parents=True, exist_ok=True)

            df.to_csv(final_path, index=False, encoding="utf-8-sig")

        return df
