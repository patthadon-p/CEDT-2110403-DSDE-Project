"""
PySpark Utility for Stratified Sampling on Encoded Data.

This module provides a utility function for performing stratified random
sampling on a PySpark DataFrame based on the indices of specified encoded
feature vectors. This ensures that the training and testing datasets maintain
a representative distribution of key categorical combinations.

Functions
---------
preprocessed_data_sampler
    Performs stratified sampling based on the indices of the "address_encoded" 
    and "type_encoded" columns, and then splits the result into training and testing sets.
"""

# Spark modules
from pyspark.ml.linalg import SparseVector
from pyspark.sql import DataFrame
from pyspark.sql.functions import col, concat_ws, udf
from pyspark.sql.types import ArrayType, IntegerType


def preprocessed_data_sampler(
    df: DataFrame,
    sampling_fraction: float = 0.1,
) -> tuple[DataFrame, DataFrame]:
    """
    Performs stratified sampling and splits the resulting sample into training and testing sets.

    The stratification is based on combining the indices from the sparse vectors 
    in the `address_encoded` and `type_encoded` columns. This grouping (strata) 
    is then used to draw a balanced sample.

    Parameters
    ----------
    df : pyspark.sql.DataFrame
        The input PySpark DataFrame, expected to contain "address_encoded" 
        and "type_encoded" columns (pyspark.ml.linalg.SparseVector).
    sampling_fraction : float, optional
        The fraction of the data to sample from each stratum. Default is 0.1.

    Returns
    -------
    tuple of (pyspark.sql.DataFrame, pyspark.sql.DataFrame)
        A tuple containing the training DataFrame (80%) and the testing DataFrame (20%) 
        from the stratified sample.

    Notes
    -----
    The indices of SparseVectors are used as strata keys because they represent 
    the actual unique categories assigned during feature encoding (Feature Hashing/CountVectorizer).
    """
    
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
    fractions = dict.fromkeys(strata_values, sampling_fraction)

    sampled_df = df_grouped.sampleBy("strata", fractions, seed=42)

    train_df, test_df = sampled_df.randomSplit([0.8, 0.2], seed=42)

    return train_df, test_df
