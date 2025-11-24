import pyspark.sql.functions as F
from pyspark.ml.feature import CountVectorizer
from pyspark.sql import DataFrame


def multi_value_vectorizer(
    df: DataFrame,
    input_column: str,
    output_column: str,
    delimiter: str = ",",
    drop_original: bool = True,
) -> DataFrame:

    df_array = df.withColumn(
        input_column,
        F.when(
            F.col(input_column).isNotNull(),
            F.split(F.col(input_column), delimiter),
        ).otherwise(F.array().cast("array<string>")),
    )

    cv = CountVectorizer(inputCol=input_column, outputCol=output_column)

    model = cv.fit(df_array)
    df_out = model.transform(df_array)

    if drop_original:
        df_out = df_out.drop(input_column)

    return df_out
