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
    base_path = Path(get_data_dir()) / "model" / name
    model_path = Path(str(base_path) + "_cv_model_spark")
    return model_path
