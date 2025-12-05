# Import necessary modules
import os

import pyspark.sql.functions as F
from pyspark.ml.feature import CountVectorizer, CountVectorizerModel
from pyspark.sql import DataFrame

# Utility functions
from src.utils import get_data_dir


def multi_value_vectorizer(
    df: DataFrame,
    input_column: str,
    output_column: str,
    delimiter: str = ",",
    filename: str | None = None,
    drop_original: bool = True,
) -> DataFrame:

    df_array = df.withColumn(
        input_column,
        F.when(
            F.col(input_column).isNotNull(),
            F.split(F.col(input_column), delimiter),
        ).otherwise(F.array().cast("array<string>")),
    )

    save_path = (
        get_data_dir()
        / "model"
        / ("vectorizer_model" if filename is None else filename)
    )
    if os.path.isdir(save_path):
        model = CountVectorizerModel.load(str(save_path))
    else:
        cv = CountVectorizer(inputCol=input_column, outputCol=output_column)
        model = cv.fit(df_array)
        model.save(str(save_path))

    df_out = model.transform(df_array)

    if drop_original:
        df_out = df_out.drop(input_column)

    return df_out
