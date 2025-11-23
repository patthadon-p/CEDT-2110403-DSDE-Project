# Import necessary modules
from pyspark.ml import Pipeline, Transformer
from pyspark.sql import DataFrame

# Other Encoder
from .OrganizationEncoderSpark import OrganizationEncoderSpark
from .TypeEncoderSpark import TypeEncoderSpark


class EncoderPipelineSpark(Transformer):

    def __init__(
        self,
        organization_column: str | None = None,
        type_column: str | None = None,
    ) -> None:
        self.organization_column = organization_column
        self.type_column = type_column

        self.organization_encoder = OrganizationEncoderSpark(
            organization_column=self.organization_column
        )

        self.type_encoder = TypeEncoderSpark(
            type_column=self.type_column,
        )

    def _transform(self, df: DataFrame) -> DataFrame:
        encoder_pipeline = Pipeline(
            stages=[self.organization_encoder, self.type_encoder]
        )

        df_transformed = encoder_pipeline.fit(df).transform(df)

        return df_transformed
