# Import necessary libraries
from pyspark.ml import Transformer
from pyspark.ml.util import DefaultParamsReadable, DefaultParamsWritable
from pyspark.sql import DataFrame
from pyspark.sql import functions as F
from pyspark.sql.types import StringType

# Utility Functions
from src.utils.FuzzyUtils import fuzzy_match, normalize
from src.utils.ProvinceUtils import load_province_whitelist


class ProvinceTransformerSpark(
    Transformer, DefaultParamsReadable, DefaultParamsWritable
):

    def __init__(self, path: str = "", province_column: str | None = None) -> None:
        super().__init__()
        self.path = path
        self.whitelist = load_province_whitelist(self.path)

        self.province_column = province_column or "province"
        self._cache_province = {}

    def _transform(self, df: DataFrame) -> DataFrame:

        cleaned_df = (
            df.withColumn(
                self.province_column,
                F.regexp_replace(
                    F.col(self.province_column).cast("string"), "จังหวัด", ""
                ),
            )
            .withColumn(
                self.province_column,
                F.regexp_replace(F.col(self.province_column).cast("string"), "จ.", ""),
            )
            .withColumn(self.province_column, F.trim(F.col(self.province_column)))
        )

        def province_udf(x: str | None) -> str | None:
            if x is None:
                return None
            normalized = normalize(x)
            return fuzzy_match(
                normalized, list(self.whitelist.keys()), self._cache_province, cutoff=90
            )

        spark_province_udf = F.udf(province_udf, StringType())

        df_transformed = cleaned_df.withColumn(
            self.province_column,
            spark_province_udf(F.col(self.province_column)),
        )

        def map_to_whitelist(x: str | None) -> str | None:
            return self.whitelist.get(x)

        map_udf = F.udf(map_to_whitelist, StringType())

        df_transformed = df_transformed.withColumn(
            self.province_column, map_udf(F.col(self.province_column))
        )

        df_transformed = df_transformed.filter(F.col(self.province_column).isNotNull())

        return df_transformed
