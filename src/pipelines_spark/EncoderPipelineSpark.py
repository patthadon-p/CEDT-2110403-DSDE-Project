# Import necessary modules
from pyspark.ml import Transformer
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
        encoded_column: str | None = None,
        organization_column: str | None = None,
        type_column: str | None = None,
    ) -> None:

        self.district_column = district_column
        self.subdistrict_column = subdistrict_column
        self.encoded_column = encoded_column

        self.organization_column = organization_column
        self.type_column = type_column

        self.address_encoder = AddressEncoderSpark(
            district_column=self.district_column,
            subdistrict_column=self.subdistrict_column,
            encoded_column=self.encoded_column,
        )

        self.organization_encoder = OrganizationEncoderSpark(
            organization_column=self.organization_column
        )

        self.type_encoder = TypeEncoderSpark(
            type_column=self.type_column,
        )

    def _transform(self, df: DataFrame) -> DataFrame:
        df_transformed = self.address_encoder.transform(df)
        df_transformed = self.organization_encoder.transform(df_transformed)
        df_transformed = self.type_encoder.transform(df_transformed)

        return df_transformed
