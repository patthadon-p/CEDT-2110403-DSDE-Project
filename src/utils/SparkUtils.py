"""
Utilities for initializing and configuring PySpark and Apache Sedona sessions.

This module handles setting up the necessary environment variables (HADOOP_HOME, SPARK_HOME),
configuring the Python path for PySpark executors, and creating a combined SparkSession
and SedonaContext tailored for geospatial processing.

Functions
---------
create_spark_session
    Initializes and returns a configured PySpark SparkSession and a SedonaContext.
"""

import os

# Add current directory to Python path for imports
import re
import sys

# Import spark, findspark, and sedona
import findspark
from dotenv import load_dotenv
from pyspark.ml.linalg import DenseVector, SparseVector, Vectors, VectorUDT
from pyspark.sql import DataFrame, SparkSession
from pyspark.sql import functions as F
from sedona.spark import SedonaContext

# Utility Functions
from src.utils import get_dot_env_path

# Add the parent directory (project root) to Python path so we can import from src
project_root = os.path.dirname(os.getcwd())
if project_root not in sys.path:
    sys.path.append(project_root)

# Load environment variables from .env file
load_dotenv(dotenv_path=get_dot_env_path())

HADOOP_HOME = os.getenv("HADOOP_HOME", "")
SPARK_HOME = os.getenv("SPARK_HOME", "")
JAVA_HOME = os.getenv("JAVA_HOME", "")

# Set Python executable for PySpark
os.environ["PYSPARK_PYTHON"] = sys.executable
os.environ["PYSPARK_DRIVER_PYTHON"] = sys.executable

# Set Hadoop, Spark and Java home
os.environ["HADOOP_HOME"] = HADOOP_HOME
os.environ["SPARK_HOME"] = SPARK_HOME
os.environ["JAVA_HOME"] = JAVA_HOME

# Update system PATH
os.environ["PATH"] += os.pathsep + os.path.join(HADOOP_HOME, "bin")

os.environ["SPARK_LOCAL_IP"] = "127.0.0.1"
os.environ["PYSPARK_SUBMIT_ARGS"] = "--conf spark.driver.host=127.0.0.1 pyspark-shell"


def create_spark_session(
    app_name: str | None = None,
) -> tuple[SparkSession, SparkSession]:
    """
    Creates and returns a SparkSession with Sedona enabled.

    The function loads environment variables, initializes findspark, and configures
    Spark with Kryo serialization and necessary Maven packages for Apache Sedona
    (GeoSpark).

    Parameters
    ----------
    app_name : str, optional
        Name of the Spark application, by default "DataCleansingSpark".

    Returns
    -------
    tuple[pyspark.sql.SparkSession, pyspark.sql.SparkSession]
        A tuple containing the configured SparkSession and the SedonaContext
        (which is also a SparkSession instance).
    """

    # Initialize findspark
    findspark.init(SPARK_HOME)

    # Initialize Spark session (reuse existing session if available)
    spark: SparkSession = (
        SparkSession.builder.appName(app_name or "DataCleansingSpark")  # type: ignore
        .config("spark.executorEnv.PYTHONPATH", project_root)
        .master("local[*]")
        .config("spark.driver.memory", "12g")
        .config("spark.executor.memory", "12g")
        .config("spark.serializer", "org.apache.spark.serializer.KryoSerializer")
        .config(
            "spark.kryo.registrator",
            "org.apache.sedona.core.serde.SedonaKryoRegistrator",
        )
        .config(
            "spark.jars.packages",
            "org.apache.sedona:sedona-spark-shaded-3.5_2.12:1.6.1,"
            "org.datasyslab:geotools-wrapper:1.6.0-28.2",
        )
        .getOrCreate()
    )

    # Initialize Sedona
    sedona = SedonaContext.create(spark)

    return spark, sedona


def preprocessed_data_converter(
    df: DataFrame,
) -> DataFrame:

    def _parse_sparse(s: str) -> SparseVector | None:
        if s is None:
            return None

        # Example: (2048,[834,1804],[1.0,1.0])
        match = re.match(r"\((\d+),\[(.*?)\],\[(.*?)\]\)", s)
        if not match:
            return None

        size = int(match.group(1))

        # indices: convert "834,1804" → [834,1804]
        indices = match.group(2)
        indices = [int(x) for x in indices.split(",")] if indices else []

        # values: convert "1.0,1.0" → [1.0,1.0]
        values = match.group(3)
        values = [float(x) for x in values.split(",")] if values else []

        return Vectors.sparse(size, indices, values)

    def _parse_dense(s: str) -> DenseVector | None:
        if s is None:
            return None

        # Remove brackets → "13.67891,100.66709"
        s = s.strip()[1:-1]
        values = [float(x) for x in s.split(",")] if s else []

        return Vectors.dense(values)

    parse_sparse_udf = F.udf(_parse_sparse, VectorUDT())
    parse_dense_udf = F.udf(_parse_dense, VectorUDT())

    df_prepared = (
        df.withColumn("address_encoded", parse_sparse_udf("address_encoded"))
        .withColumn("organization_encoded", parse_sparse_udf("organization_encoded"))
        .withColumn("type_encoded", parse_sparse_udf("type_encoded"))
        .withColumn("latlong_encoded", parse_dense_udf("latlong_encoded"))
    )

    return df_prepared
