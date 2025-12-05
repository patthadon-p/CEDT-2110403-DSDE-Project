# Import necessary modules
import shutil
from pathlib import Path

from pyspark.ml.evaluation import RegressionEvaluator

# Spark modules
from pyspark.ml.tuning import CrossValidatorModel
from pyspark.sql import DataFrame

# Utility functions
from .ConfigUtils import get_data_dir


def evaluate_model(
    name: str,
    model: CrossValidatorModel,
    test_df: DataFrame,
    evaluators: dict[str, RegressionEvaluator],
) -> None:
    print(f"\n===== {name} Results =====")
    preds = model.transform(test_df)
    for metric, evaluator in evaluators.items():
        score = evaluator.evaluate(preds)
        print(f"{metric.upper()}: {score}")
    print("==========================")


def save_model(model: CrossValidatorModel, name: str | None = None) -> None:

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
