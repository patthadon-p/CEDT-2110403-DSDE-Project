# Import necessary libraries
from pyspark.ml import Transformer
from pyspark.ml.feature import FeatureHasher
from pyspark.sql import DataFrame


class AddressEncoderSpark(Transformer):

    def __init__(
        self,
        district_column: str | None = None,
        subdistrict_column: str | None = None,
        encoded_column: str | None = None,
    ) -> None:
        self.district_column = district_column or "district"
        self.subdistrict_column = subdistrict_column or "subdistrict"
        self.encoded_column = encoded_column or "address_encoded"
        self.num_features = 2048

    def _transform(self, df: DataFrame) -> DataFrame:

        hasher = FeatureHasher(
            inputCols=[self.district_column, self.subdistrict_column],
            outputCol=self.encoded_column,
            numFeatures=self.num_features,
        )

        encoded_df = hasher.transform(df)

        encoded_df = encoded_df.drop(
            self.district_column,
            self.subdistrict_column,
        )

        return encoded_df
