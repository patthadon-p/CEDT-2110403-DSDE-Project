# Import necessary modules
from pyspark.ml import Pipeline, Transformer
from pyspark.sql import DataFrame

# Other Encoder
from .AddressEncoderSpark import AddressEncoderSpark
from .OrganizationEncoderSpark import OrganizationEncoderSpark
from .TypeEncoderSpark import TypeEncoderSpark


class EncoderPipelineSpark(Transformer):

    def __init__(
        self,
        district_column: str | None = None,
        subdistrict_column: str | None = None,
        organization_column: str | None = None,
        type_column: str | None = None,
    ) -> None:
        self.district_column = district_column
        self.subdistrict_column = subdistrict_column
        self.organization_column = organization_column
        self.type_column = type_column

        self.address_encoder = AddressEncoderSpark(
            district_column=self.district_column,
            subdistrict_column=self.subdistrict_column,
        )

        self.organization_encoder = OrganizationEncoderSpark(
            organization_column=self.organization_column
        )

        self.type_encoder = TypeEncoderSpark(
            type_column=self.type_column,
        )

    def _transform(self, df: DataFrame) -> DataFrame:
        encoder_pipeline = Pipeline(
            stages=[self.address_encoder, self.organization_encoder, self.type_encoder]
        )

        df_transformed = encoder_pipeline.fit(df).transform(df)

        return df_transformed
