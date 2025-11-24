# Import necessary modules
from pyspark.ml import Transformer
from pyspark.ml.feature import CountVectorizer
from pyspark.sql import DataFrame
from pyspark.sql import functions as F

from src.utils.EncoderUtils import multi_value_vectorizer


class OrganizationEncoderSpark(Transformer):

    def __init__(
        self,
        organization_column: str | None = None,
    ) -> None:
        self.organization = organization_column or "organization"
        self.organization_encoded = self.organization + "_encoded"

    def _transform(self, df: DataFrame) -> DataFrame:
        
        encoded_df = multi_value_vectorizer(
            df,
            input_column=self.organization,
            output_column=self.organization_encoded,
        )

        return encoded_df
