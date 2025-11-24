# Import necessary libraries
from pyspark.ml import Pipeline, Transformer
from pyspark.ml.feature import FeatureHasher, VectorAssembler
from pyspark.sql import DataFrame


class AddressEncoderSpark(Transformer):

    def __init__(
        self,
        district_column: str | None = None,
        subdistrict_column: str | None = None,
        latitude_column: str | None = None,
        longitude_column: str | None = None,
        address_encoded_column: str | None = None,
        latlong_encoded_column: str | None = None,
    ) -> None:
        self.district_column = district_column or "district"
        self.subdistrict_column = subdistrict_column or "subdistrict"
        self.latitude_column = latitude_column or "latitude"
        self.longitude_column = longitude_column or "longitude"
        self.address_encoded_column = address_encoded_column or "address_encoded"
        self.latlong_encoded_column = latlong_encoded_column or "latlong_encoded"
        self.num_features = 2048

    def _transform(self, df: DataFrame) -> DataFrame:

        hasher = FeatureHasher(
            inputCols=[self.district_column, self.subdistrict_column],
            outputCol=self.address_encoded_column,
            numFeatures=self.num_features,
        )

        assembler = VectorAssembler(
            inputCols=[self.latitude_column, self.longitude_column],
            outputCol=self.latlong_encoded_column,
        )

        pipeline = Pipeline(stages=[hasher, assembler])
        model = pipeline.fit(df)
        encoded_df = model.transform(df)

        encoded_df = encoded_df.drop(
            self.district_column,
            self.subdistrict_column,
            self.latitude_column,
            self.longitude_column,
        )

        return encoded_df
