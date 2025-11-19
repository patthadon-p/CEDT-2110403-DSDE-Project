from io import BytesIO

import pandas as pd
import requests

from src.utils.DatetimeUtils import get_buddhist_year_last_two_digits

LEVEL_CODE_MAPPING: dict[str, str] = {
    "province": "c",
    "district": "t",
    "subdistrict": "a",
    "village": "m",
}


class PopulationScrapping:

    def __init__(
        self,
        url: str = "",
        year: int | None = None,
        level: str = "subdistrict",
        filetype: str = "xls",
    ) -> None:

        self.url = url or "https://stat.bora.dopa.go.th/new_stat/webPage/statByYear.php"
        self.level = level
        self.filetype = filetype

        if year is None:
            year_2digit_str = get_buddhist_year_last_two_digits()
            self.year = 2500 + int(year_2digit_str)
        else:
            self.year = year
            year_2digit_str = str(self.year)[2:].zfill(2)

        level_code = LEVEL_CODE_MAPPING.get(self.level.lower(), "t")

        self.target_url = (
            f"https://stat.bora.dopa.go.th/new_stat/file/{year_2digit_str}/"
            f"stat_{level_code}{year_2digit_str}.{self.filetype}"
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

            df = pd.read_excel(file_like_object, engine="xlrd")
            return df

        except Exception:
            return None

    def run_scraper(self) -> pd.DataFrame | None:

        file_bytes = self._fetch_file()

        if not file_bytes:
            return None

        self.data_frame = self._load_data(file_bytes)

        return self.data_frame
