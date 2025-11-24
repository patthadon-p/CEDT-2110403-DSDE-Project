# Import necessary modules
from pyspark.ml import Transformer
from pyspark.ml.feature import CountVectorizer
from pyspark.sql import DataFrame
from pyspark.sql import functions as F

from src.utils.EncoderUtils import multi_value_vectorizer


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

        encoded_df = multi_value_vectorizer(
            df,
            input_column=self.type,
            output_column=self.type_encoded,
        )

        return encoded_df
