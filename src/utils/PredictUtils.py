"""
PySpark Model Prediction Utility.

This module provides a utility function to load a saved PySpark ML model
and run predictions on a new DataFrame.

Functions
---------
predict_with_model
    Loads a saved PipelineModel, CrossValidatorModel, or TrainValidationSplitModel
    and applies it to an input DataFrame, optionally returning the result as a Pandas DataFrame.
"""

import os

import pandas as pd
from pyspark.ml.pipeline import PipelineModel
from pyspark.ml.tuning import CrossValidatorModel, TrainValidationSplitModel
from pyspark.sql import DataFrame, SparkSession


def predict_with_model(
    spark: SparkSession,
    model_path: str,
    input_df: DataFrame,
    return_pandas: bool = False,
) -> DataFrame | pd.DataFrame:
    """
    Load a saved Spark ML model (PipelineModel, CrossValidatorModel,
    or TrainValidationSplitModel) and run prediction.

    Parameters
    ----------
    spark : SparkSession
        Active Spark session.
    model_path : str
        Directory with the saved model. The function attempts to load the model
        sequentially as CrossValidatorModel, TrainValidationSplitModel, and
        finally as a bare PipelineModel.
    input_df : DataFrame
        Spark DataFrame to predict on.
    return_pandas : bool, optional
        If True, returns the prediction results collected as a Pandas DataFrame. 
        Otherwise, returns the prediction results as a Spark DataFrame. 
        Default is False.

    Returns
    -------
    pyspark.sql.DataFrame or pandas.DataFrame
        The prediction DataFrame, containing the input columns plus the prediction 
        columns (e.g., 'prediction', 'rawPrediction', 'probability'). The return type 
        depends on the `return_pandas` parameter.
        
    Raises
    ------
    TypeError
        If input types are incorrect.
    ValueError
        If the model path does not exist.
    RuntimeError
        If the model cannot be loaded from the specified path.
    """

    # -----------------------------
    # TYPE VALIDATION
    # -----------------------------

    # Validate Spark session
    if not isinstance(spark, SparkSession):
        raise TypeError(f"'spark' must be a SparkSession, got {type(spark).__name__}")

    # Validate model path
    if not isinstance(model_path, str):
        raise TypeError(
            f"'model_path' must be a string, got {type(model_path).__name__}"
        )

    if not os.path.exists(model_path):
        raise ValueError(f"Model path '{model_path}' does not exist.")

    # Validate input DataFrame
    if not isinstance(input_df, DataFrame):
        raise TypeError(
            f"'input_df' must be a Spark DataFrame, got {type(input_df).__name__}"
        )

    # Validate return_pandas
    if not isinstance(return_pandas, bool):
        raise TypeError(
            f"'return_pandas' must be a boolean, got {type(return_pandas).__name__}"
        )

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
                raise RuntimeError(
                    f"Could not load model from '{model_path}': {str(e)}"
                ) from e

    # -----------------------------
    # PREDICT
    # -----------------------------
    predictions = model.transform(input_df)

    if return_pandas:
        return predictions.toPandas()

    return predictions
