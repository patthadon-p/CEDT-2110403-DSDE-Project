# Import necessary modules
from pyspark.ml import Transformer
from pyspark.ml.feature import CountVectorizer
from pyspark.sql import DataFrame
from pyspark.sql import functions as F


class TypeEncoderSpark(Transformer):

    def __init__(
        self,
        type_column: str | None = None,
    ) -> None:
        self.type = type_column or "type"
        self.type_encoded = self.type + "_encoded"

    def _transform(self, df: DataFrame) -> DataFrame:

        df = df.withColumn(
            self.type, F.expr(f"substring({self.type}, 2, length({self.type})-2)")
        )

        df_array = df.withColumn(
            self.type,
            F.when(
                F.col(self.type).isNotNull(),
                F.split(F.col(self.type), ","),
            ).otherwise(F.array()),
        )

        cv = CountVectorizer(
            inputCol=self.type,
            outputCol=self.type_encoded,
        )
        cv_model = cv.fit(df_array)
        encoded_df = cv_model.transform(df_array)

        encoded_df = encoded_df.drop(self.type)

        return encoded_df
