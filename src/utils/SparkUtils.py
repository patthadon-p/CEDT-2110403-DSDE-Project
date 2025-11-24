# Add current directory to Python path for imports
import os
import sys

# Import spark, findspark, and sedona
import findspark
from dotenv import load_dotenv
from pyspark.sql import SparkSession
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


def create_spark_session(
    app_name: str | None = None,
) -> tuple[SparkSession, SparkSession]:
    """
    Creates and returns a SparkSession with Sedona enabled.

    Parameters
    ----------
    app_name : str, optional
        Name of the Spark application, by default "DataCleansingSpark".

    Returns
    -------
    SparkSession
        Configured SparkSession with Sedona support.
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
