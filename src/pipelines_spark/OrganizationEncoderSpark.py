# Import necessary modules
from pyspark.ml import Transformer
from pyspark.ml.feature import CountVectorizer
from pyspark.sql import DataFrame
from pyspark.sql import functions as F


class OrganizationEncoderSpark(Transformer):

    def __init__(
        self,
        organization_column: str | None = None,
    ) -> None:
        self.organization = organization_column or "organization"
        self.organization_encoded = self.organization + "_encoded"

    def _transform(self, df: DataFrame) -> DataFrame:

        df_array = df.withColumn(
            self.organization,
            F.when(
                F.col(self.organization).isNotNull(),
                F.split(F.col(self.organization), ","),
            ).otherwise(F.array()),
        )

        cv = CountVectorizer(
            inputCol=self.organization,
            outputCol=self.organization_encoded,
        )
        cv_model = cv.fit(df_array)
        encoded_df = cv_model.transform(df_array)

        encoded_df = encoded_df.drop(self.organization)

        return encoded_df
