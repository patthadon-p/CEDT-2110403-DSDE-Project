# Spark modules
from pyspark.ml.linalg import SparseVector
from pyspark.sql import DataFrame
from pyspark.sql.functions import col, concat_ws, udf
from pyspark.sql.types import ArrayType, IntegerType


def preprocessed_data_sampler(
    df: DataFrame,
    samplng_fraction: float = 0.1,
) -> tuple[DataFrame, DataFrame]:

    def _get_indices(v: SparseVector) -> list[int]:
        if v is None:
            return []
        return v.indices.tolist()

    extract_indices_udf = udf(_get_indices, ArrayType(IntegerType()))

    df_grouped = (
        df.withColumn("address_indices", extract_indices_udf(col("address_encoded")))
        .withColumn("type_indices", extract_indices_udf(col("type_encoded")))
        .withColumn("address_group", concat_ws("_", col("address_indices")))
        .withColumn("type_group", concat_ws("_", col("type_indices")))
        .withColumn("strata", concat_ws("__", "address_group", "type_group"))
    )

    strata_values = [
        row["strata"] for row in df_grouped.select("strata").distinct().collect()
    ]
    fractions = dict.fromkeys(strata_values, samplng_fraction)

    sampled_df = df_grouped.sampleBy("strata", fractions, seed=42)

    train_df, test_df = sampled_df.randomSplit([0.8, 0.2], seed=42)

    return train_df, test_df
