# Import necessary modules
from io import BytesIO

import pandas as pd
import requests

# Utility functions
from src.utils.DatetimeUtils import get_buddhist_year


class PopulationScrapping:
    def __init__(
        self,
        url: str = "",
        year: str | None = None,
        level: str = "",
    ) -> None:

        # Mapping of administrative levels to their corresponding codes in the URL
        PopulationScrapping.LEVEL_CODE_MAPPING: dict[str, str] = {
            "province": "c",
            "district": "a",
            "subdistrict": "t",
            "village": "m",
        }

        # Columns present in the population data file
        PopulationScrapping.COLUMNS: list[str] = [
            "YYMM",
            "CC-CODE",
            "CC-DESC",
            "RCODE-CODE",
            "RCODE-DESC",
            "CCAATT-CODE",
            "CCAATT-DESC",
            "CCAATTMM-CODE",
            "CCAATTMM-DESC",
            "MALE",
            "FEMALE",
            "TOTAL",
            "HOUSE",
            "",
        ]

        self.url = url or "https://stat.bora.dopa.go.th/new_stat/webPage/statByYear.php"
        self.level = level or "subdistrict"
        self.year = year or get_buddhist_year()

        self.level_code = PopulationScrapping.LEVEL_CODE_MAPPING.get(
            self.level.lower(), "t"
        )

        self.target_url = (
            f"https://stat.bora.dopa.go.th/new_stat/file/{self.year[-2:]}/"
            f"stat_{self.level_code}{self.year[-2:]}.txt"
        )

        self.data_frame: pd.DataFrame | None = None

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

        if not file_bytes:
            return pd.DataFrame()

        self.data_frame = self._load_data(file_bytes)
        self.data_frame = pd.DataFrame() if self.data_frame is None else self.data_frame
        self.data_frame.columns = PopulationScrapping.COLUMNS

        return self.data_frame

    def fetch_and_clean(self) -> pd.DataFrame:
        df = self._run_scraper().copy()
        df = df.drop(
            columns=[
                "YYMM",
                "CC-CODE",
                "RCODE-CODE",
                "CCAATT-CODE",
                "CCAATTMM-CODE",
                "MALE",
                "FEMALE",
                "",
            ]
        )

        df = df[
            (df["CC-DESC"].str.strip() != "")
            & (df["RCODE-DESC"].str.strip() != "")
            & (df["CCAATT-DESC"].str.strip() != "")
            # & (df["CCAATTMM-DESC"].str.strip() != "")
        ]

        df["RCODE-DESC"] = df["RCODE-DESC"].str.replace("ท้องถิ่นเขต", "")

        df = df[df["CC-DESC"] == "กรุงเทพมหานคร"]
        df = df.drop(columns=["CC-DESC", "CCAATTMM-DESC"])
        df = df.dropna()
        df = df.reset_index(drop=True)

        self.data_frame = df

        return self.data_frame
