"""
PySpark Model Management Utilities.

This module provides helper functions for managing PySpark MLlib models, 
including evaluating a fitted CrossValidatorModel against multiple metrics, 
saving the model securely (using atomic rename), and retrieving the saved 
model path.

Functions
---------
evaluate_model
    Calculates and displays evaluation metrics for a fitted model on a test DataFrame.
save_model
    Saves a fitted PySpark CrossValidatorModel atomically to prevent corruption.
get_model_path
    Retrieves the absolute path where a specified model is expected to be saved.
"""

# Import necessary modules
import shutil
from pathlib import Path

# Spark modules
from pyspark.ml.evaluation import RegressionEvaluator
from pyspark.ml.tuning import CrossValidatorModel
from pyspark.sql import DataFrame

# Utility functions
from .ConfigUtils import get_data_dir


def evaluate_model(
    name: str,
    model: CrossValidatorModel,
    test_df: DataFrame,
    evaluators: dict[str, RegressionEvaluator],
) -> dict[str, float]:
    """
    Calculates and displays evaluation metrics for a fitted PySpark model on a test DataFrame.

    The function applies the best model found by the CrossValidator to the test data, 
    then calculates all specified metrics (e.g., RMSE, R2) using the provided evaluators.

    Parameters
    ----------
    name : str
        The name of the model/experiment, used for display purposes.
    model : pyspark.ml.tuning.CrossValidatorModel
        The fitted PySpark CrossValidatorModel containing the best PipelineModel.
    test_df : pyspark.sql.DataFrame
        The test DataFrame used for calculating scores.
    evaluators : dict of {str: pyspark.ml.evaluation.RegressionEvaluator}
        A dictionary mapping metric names (e.g., 'rmse') to their configured 
        PySpark RegressionEvaluator instances.

    Returns
    -------
    dict of {str: float}
        A dictionary mapping each metric name to its calculated score.
    """

    score_dict = {}

    print(f"\n===== {name} Results =====")
    preds = model.bestModel.transform(test_df)
    for metric, evaluator in evaluators.items():
        score = evaluator.evaluate(preds)
        print(f"{metric.upper()}: {score}")

        score_dict[metric] = score

    print("==========================")

    return score_dict


def save_model(model: CrossValidatorModel, name: str | None = None) -> None:
    """
    Saves a fitted PySpark CrossValidatorModel atomically.

    The model is saved to a temporary '_new' directory first. If successful, 
    the old model directory (if present) is deleted, and the '_new' directory 
    is renamed to the final path. This prevents data corruption during save 
    if the process is interrupted.

    Parameters
    ----------
    model : pyspark.ml.tuning.CrossValidatorModel
        The fitted CrossValidatorModel to be saved.
    name : str or None, optional
        The specific name for the saved model directory. If None, defaults to "model". 
        The final directory name will be `<name>_cv_model_spark`.

    Returns
    -------
    None
        The function does not return a value.
    """
    
    save_name = name or "model"
    base_path = Path(get_data_dir()) / "model" / save_name

    old_path = Path(str(base_path) + "_cv_model_spark")
    new_path = Path(str(base_path) + "_cv_model_spark_new")

    # Remove the _new directory if it exists (cleanup)
    if new_path.exists():
        shutil.rmtree(new_path)

    # Save model to the _new path
    model.save(str(new_path))

    # Delete old model directory if exists
    if old_path.exists():
        shutil.rmtree(old_path)

    # Rename _new → normal name
    new_path.rename(old_path)

    print(f"✔ Model saved successfully to: {old_path}")


def get_model_path(name: str) -> Path:
    """
    Retrieves the absolute path where a PySpark CrossValidatorModel 
    with the given name is expected to be saved.

    The path structure is: `data/model/<name>_cv_model_spark`.

    Parameters
    ----------
    name : str
        The base name of the model (e.g., 'gbt_model').

    Returns
    -------
    pathlib.Path
        The absolute path to the saved PySpark model directory.
    """
    
    base_path = Path(get_data_dir()) / "model" / name
    model_path = Path(str(base_path) + "_cv_model_spark")
    return model_path
