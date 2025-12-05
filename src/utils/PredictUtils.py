from pyspark.sql import DataFrame, SparkSession
from pyspark.ml.pipeline import PipelineModel
from pyspark.ml.tuning import CrossValidatorModel, TrainValidationSplitModel
import os


def predict_with_model(
    spark: SparkSession,
    model_path: str,
    input_df: DataFrame,
    return_list: bool = False
):
    """
    Load a saved Spark ML model (PipelineModel, CrossValidatorModel,
    or TrainValidationSplitModel) and run prediction.

    Parameters
    ----------
    spark : SparkSession
        Active Spark session.
    model_path : str
        Directory with the saved model.
    input_df : DataFrame
        Spark DataFrame to predict on.
    return_list : bool
        If True, return Python list of predictions. Otherwise return a DataFrame.

    Returns
    -------
    DataFrame or list
        Prediction DataFrame or list of predictions.
    """

    # -----------------------------
    # TYPE VALIDATION
    # -----------------------------

    # Validate Spark session
    if not isinstance(spark, SparkSession):
        raise TypeError(f"'spark' must be a SparkSession, got {type(spark).__name__}")

    # Validate model path
    if not isinstance(model_path, str):
        raise TypeError(f"'model_path' must be a string, got {type(model_path).__name__}")

    if not os.path.exists(model_path):
        raise ValueError(f"Model path '{model_path}' does not exist.")

    # Validate input DataFrame
    if not isinstance(input_df, DataFrame):
        raise TypeError(f"'input_df' must be a Spark DataFrame, got {type(input_df).__name__}")

    # Validate return_list
    if not isinstance(return_list, bool):
        raise TypeError(f"'return_list' must be a boolean, got {type(return_list).__name__}")

    # -----------------------------
    # MODEL LOADING
    # -----------------------------
    model = None

    try:
        model = CrossValidatorModel.load(model_path)
        model = model.bestModel
    except Exception:
        try:
            model = TrainValidationSplitModel.load(model_path)
            model = model.bestModel
        except Exception:
            try:
                model = PipelineModel.load(model_path)
            except Exception as e:
                raise RuntimeError(f"Could not load model from '{model_path}': {str(e)}")

    # -----------------------------
    # PREDICT
    # -----------------------------
    predictions = model.transform(input_df)

    if return_list:
        return [row.prediction for row in predictions.select("prediction").collect()]

    return predictions
