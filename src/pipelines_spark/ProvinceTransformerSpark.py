from pyspark.sql.functions import pandas_udf
from pyspark.sql.types import StringType
from rapidfuzz import fuzz, process
import re
import pandas as pd

from utils.ProvinceUtils import load_province_whitelist


class ProvinceTransformerSpark:
    """
    Fuzzy matcher using RapidFuzz + Spark PandasUDF.
    """

    def __init__(self, spark, path: str = "",):
        self.spark = spark
        self.path = path
        self.cutoff = 60

        self.whitelist = load_province_whitelist(self.path)
        self.choices = list(self.whitelist.keys())

        # --- broadcast to executors ---
        self.bc_choices = spark.sparkContext.broadcast(self.choices)
        self.bc_whitelist = spark.sparkContext.broadcast(self.whitelist)

        # Build the UDF once (important!)
        self.fuzzy_udf = self._build_udf()

    # ----------------------------------------------------------
    # INTERNAL: build Pandas UDF
    # ----------------------------------------------------------
    def _build_udf(self):

        bc_choices = self.bc_choices
        bc_whitelist = self.bc_whitelist
        cutoff = self.cutoff

        @pandas_udf(StringType())
        def udf(col: pd.Series) -> pd.Series:

            choices = bc_choices.value
            whitelist = bc_whitelist.value
            cache = {}  # re-used within each batch

            def fuzzy_single(text): 

                if text in cache: 
                    return cache[text] 
                if not text: 
                    cache[text] = None 
                    return None 
                
                t = str(text)
                t = re.sub(r"^(จังหวัด|จ\.)\s*", "", t)
                t = re.sub(r"\s+", " ", t).strip()

                for prefix in ["บาง", "คลอง"]:
                    t = re.sub(rf"({prefix})\1+", r"\1", t)

                text_norm = t.lower()

                match = process.extractOne( 
                    text_norm, 
                    choices, 
                    score_cutoff=cutoff, 
                    scorer=fuzz.WRatio 
                )

                if not match: 
                    cache[text] = None 
                    return None 
                best_alias = match[0] 
                province = whitelist[best_alias] 
                cache[text] = province 
                return province 
            
            return col.apply(fuzzy_single)

        return udf

    # ----------------------------------------------------------
    # PUBLIC API: apply to a Spark column
    # ----------------------------------------------------------
    def transform(self, df, input_col: str, output_col: str = "province"):
        return df.withColumn(output_col, self.fuzzy_udf(input_col))
