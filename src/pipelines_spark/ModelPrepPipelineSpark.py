# Import necessary modules
from pyspark.ml import Transformer
from pyspark.sql import DataFrame

# Other Transformer
from .DataFilterTransformerSpark import DataFilterTransformerSpark
from .EncoderPipelineSpark import EncoderPipelineSpark


class ModelPrepPipelineSpark(Transformer):

    def __init__(
        self,
        filter_columns: dict[str, str] | None = None,
        drop_columns: list | None = None,
        district_column: str | None = None,
        encoded_column: str | None = None,
        subdistrict_column: str | None = None,
        organization_column: str | None = None,
        type_column: str | None = None,
    ) -> None:
        self.filter_columns = filter_columns
        self.drop_columns = drop_columns

        self.district_column = district_column
        self.subdistrict_column = subdistrict_column
        self.encoded_column = encoded_column
        self.organization_column = organization_column
        self.type_column = type_column

        self.data_filter_transformer = DataFilterTransformerSpark(
            filter_columns=self.filter_columns,
            drop_columns=self.drop_columns,
        )

        self.encoder_pipeline = EncoderPipelineSpark(
            district_column=self.district_column,
            subdistrict_column=self.subdistrict_column,
            encoded_column=self.encoded_column,
            organization_column=self.organization_column,
            type_column=self.type_column,
        )

    def _transform(self, df: DataFrame) -> DataFrame:
        df_transformed = self.data_filter_transformer.transform(df)
        df_transformed = self.encoder_pipeline.transform(df_transformed)

        return df_transformed
