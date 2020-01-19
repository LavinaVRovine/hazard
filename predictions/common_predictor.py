from sklearn.metrics import accuracy_score, brier_score_loss
from sklearn.externals import joblib

from abc import ABC
import pandas as pd
import numpy as np
import mlflow
import mlflow.sklearn

from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import RandomizedSearchCV

from config import ROOT_DIR

pd.set_option("display.width", 1000)
pd.set_option("display.max_columns", 50)

RANDOM_STATE = 7
DEBUG_PARAMS = {
    "bootstrap": [False],
    "max_depth": [None],
    "max_features": ["sqrt"],
    "min_samples_leaf": [2],
    "min_samples_split": [5],
    "n_estimators": [400],
}


class CommonPredictor(ABC):
    def __init__(self, debug: bool = False):
        self.name = type(self).__name__

        self.model = None
        self.model = self.load_saved_model()
        self.X_train, self.X_test, self.y_train, self.y_test = (None, None, None, None)
        self.training_columns = []
        self.y_col_name = ""
        self.debug = debug
        self.best_params = None

    @staticmethod
    def abs_distance_from_mean(y_pred_proba):
        return abs(y_pred_proba - 0.5).mean()

    def load_saved_model(self):
        return joblib.load(f"{ROOT_DIR}/saved_models/{self.name}.joblib")

    def save_model(self, classifier) -> bool:

        if (
            input("U are going to rewrite model. Are you sure?" " Spec 'yes' if so")
            == "yes"
        ):
            joblib.dump(classifier, f"{ROOT_DIR}/saved_models/{self.name}.joblib")
            return True
        else:
            print("New model not set")
            return False

    def eval_performance(self, y_pred, y_pred_probas):
        acc = accuracy_score(self.y_test, y_pred)
        brier = brier_score_loss(self.y_test, y_pred_probas[:, 1])
        mean_to_rand = self.abs_distance_from_mean(y_pred_probas[:, 1])
        return dict(acc=acc, brier=brier, mean_to_rand=mean_to_rand)

    def predict_one_match(self, row):

        labels = self.model.classes_
        win_chance = labels[0]
        lose_chance = labels[1]
        # FIXME dulicate
        row = row[self.training_columns]

        probabilities = self.model.predict_proba(row)
        return {win_chance: probabilities[0][0], lose_chance: probabilities[0][1]}

    def train_on_whole(self, best_params: dict):
        model = self.model.__class__(**best_params)
        model.fit(
            pd.concat([self.X_train, self.X_test]),
            pd.concat([self.y_train, self.y_test]),
        )
        return model

    def transform_data(self, df):
        return df.pop(self.y_col_name), df.loc[:, self.training_columns].fillna(0)

    def set_data(self, df: pd.DataFrame) -> bool:
        y, df = self.transform_data(df)
        self.X_train, self.X_test, self.y_train, self.y_test = train_test_split(
            df, y, test_size=0.2, random_state=RANDOM_STATE if self.debug else None
        )

        return True

    def train_new_model(self, df: pd.DataFrame, runs=100) -> None:

        self.set_data(df)

        # Number of trees in random forest
        n_estimators = [int(x) for x in np.linspace(start=200, stop=1000, num=10)]
        # Number of features to consider at every split
        # max_features = ["auto", "sqrt", ]
        max_features = [len(self.X_train.columns) - 2, len(self.X_train.columns) - 4]
        max_leaf_nodes = [10, 20, 30, 40]
        # Maximum number of levels in tree
        max_depth = [int(x) for x in np.linspace(10, 110, num=11)]
        max_depth.append(None)
        # Minimum number of samples required to split a node
        min_samples_split = [2, 5, 10]
        # Minimum number of samples required at each leaf node
        min_samples_leaf = [1, 2, 4]
        # Method of selecting samples for training each tree
        bootstrap = [True, False]  # Create the random grid
        random_grid = {
            "n_estimators": n_estimators,
            "max_features": max_features,
            "max_depth": max_depth,
            "min_samples_split": min_samples_split,
            "min_samples_leaf": min_samples_leaf,
            "bootstrap": bootstrap,
            "max_leaf_nodes": max_leaf_nodes
        }
        rf_model = RandomForestClassifier()
        model = RandomizedSearchCV(
            rf_model,
            param_distributions=DEBUG_PARAMS if self.debug else random_grid,
            n_iter=1 if self.debug else runs,
            cv=3,
            random_state=RANDOM_STATE if self.debug else None,
        )

        model.fit(self.X_train, self.y_train)

        self.model = model.best_estimator_
        self.best_params = model.best_params_

        print("trained new model")

    def main_train(self, df, run_name="run", n_runs=100):
        with mlflow.start_run(run_name=run_name):
            self.train_new_model(df, n_runs)
            preds = self.model.predict(self.X_test)
            pred_probas = self.model.predict_proba(self.X_test)
            perf = self.eval_performance(preds, pred_probas)

            mlflow.log_params(self.best_params)
            mlflow.log_metrics(perf)
