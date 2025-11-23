# Setting up the environment
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pyspark.ml import Transformer
from pyspark.ml.util import DefaultParamsReadable, DefaultParamsWritable
from pyspark.sql import DataFrame
from pyspark.sql import functions as F
from pyspark.sql.types import StringType

from utils.DistrictSubdistrictUtils import load_bangkok_official_area_names
from utils.FuzzyUtils import fuzzy_match, normalize


class DistrictSubdistrictTransformerSpark(
    Transformer, DefaultParamsReadable, DefaultParamsWritable
):

    def __init__(
        self,
        path: str = "",
        district_column: str | None = None,
        subdistrict_column: str | None = None,
        cutoff: int | None = None,
        prefix_bonus: bool | None = None,
    ) -> None:
        super().__init__()
        self.path = path
        self.district_column = district_column or "district"
        self.subdistrict_column = subdistrict_column or "subdistrict"

        self.cutoff = cutoff or 60
        self.prefix_bonus = prefix_bonus if prefix_bonus is not None else False

        official_area_name = load_bangkok_official_area_names(self.path)

        self.official_districts = official_area_name.get("districts", [])
        self.official_subdistricts = official_area_name.get("subdistricts", [])

        self._cache_district = {}
        self._cache_subdistrict = {}

    def _transform(self, df: DataFrame) -> DataFrame:

        def district_udf(x: str | None) -> str | None:
            if x is None:
                return None
            normalized = normalize(x)
            return fuzzy_match(
                normalized,
                self.official_districts,
                self._cache_district,
                cutoff=self.cutoff,
                prefix_bonus=self.prefix_bonus,
            )

        def subdistrict_udf(x: str | None) -> str | None:
            if x is None:
                return None
            normalized = normalize(x)
            return fuzzy_match(
                normalized,
                self.official_subdistricts,
                self._cache_subdistrict,
                cutoff=self.cutoff,
                prefix_bonus=self.prefix_bonus,
            )

        spark_district_udf = F.udf(district_udf, StringType())
        spark_subdistrict_udf = F.udf(subdistrict_udf, StringType())

        df_transformed = df.withColumn(
            self.district_column,
            spark_district_udf(F.col(self.district_column)),
        ).withColumn(
            self.subdistrict_column,
            spark_subdistrict_udf(F.col(self.subdistrict_column)),
        )

        return df_transformed
