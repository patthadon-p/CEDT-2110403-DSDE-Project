# Import necessary modules
from typing import Any, cast

from pyspark.ml import Estimator, Pipeline, PipelineModel
from pyspark.ml.evaluation import RegressionEvaluator
from pyspark.ml.feature import VectorAssembler
from pyspark.ml.tuning import CrossValidator, CrossValidatorModel, ParamGridBuilder
from pyspark.sql import DataFrame

# Utility functions
from src.utils import evaluate_model, save_model


class ModelDefinePipelineSpark:

    def __init__(
        self,
        name: str,
        model: Estimator,
        input_columns: list[str],
        label_column: str,
        evaluators: list[str],
        param_dict: dict[str, list[object]],
        num_folds: int = 3,
    ) -> None:

        self.name = name
        self.model = model

        self.input_columns = input_columns
        self.label_column = label_column

        self.assembler = VectorAssembler(
            inputCols=self.input_columns,
            outputCol="features",
        )

        self.evaluators = evaluators
        self.evaluators_dict = self.create_evaluator_dict()

        self.param_dict = param_dict

        builder = ParamGridBuilder()

        for param_name, values in self.param_dict.items():
            # get the Param object from the estimator
            param = getattr(self.model, param_name)
            builder = builder.addGrid(param, values)

        self.param_grid = builder.build()

        self.num_folds = num_folds

        self.pipeline = Pipeline(stages=[self.assembler, self.model])
        self.cv = CrossValidator(
            estimator=self.pipeline,
            estimatorParamMaps=self.param_grid,
            evaluator=cast(RegressionEvaluator, list(self.evaluators_dict.values())[0]),
            numFolds=self.num_folds,
            parallelism=1,
        )

    def create_evaluator_dict(self) -> dict[str, RegressionEvaluator]:

        allowed_metrics = ["rmse", "mse", "r2", "mae", "var"]

        evaluator_dict: dict[str, RegressionEvaluator] = {}
        for metric in self.evaluators:
            if metric not in allowed_metrics:
                continue

            evaluator = RegressionEvaluator(
                labelCol=self.label_column,
                predictionCol="prediction",
                metricName=metric,  # type: ignore
            )

            evaluator_dict[metric] = evaluator

        return evaluator_dict

    def fit(
        self,
        X: DataFrame,
        save_name: str | None = None,
    ) -> CrossValidatorModel:
        self.cv_model = self.cv.fit(X)

        if save_name is not None:
            save_model(self.cv_model, save_name)

        return self.cv_model

    def evaluate(self, test_df: DataFrame) -> dict[str, float]:
        score_dict = evaluate_model(
            name=self.name,
            model=self.cv_model,
            test_df=test_df,
            evaluators=self.evaluators_dict,
        )
        return score_dict

    def set_model(self, cv_model: CrossValidatorModel) -> None:
        self.cv_model = cv_model
        return None

    def get_pipeline(self) -> Pipeline:
        return self.pipeline

    def get_cross_validator(self) -> CrossValidator:
        return self.cv

    def get_best_params(self) -> dict[str, Any]:
        best_pipeline = cast(PipelineModel, self.cv_model.bestModel)
        best_model = best_pipeline.stages[-1]

        param_map = best_model.extractParamMap()

        for p, v in param_map.items():
            if p.name in self.param_dict:
                print(p.name, "=", v)

        return {p.name: v for p, v in param_map.items() if p.name in self.param_dict}
