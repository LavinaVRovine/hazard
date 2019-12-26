import pandas as pd
from sqlalchemy import create_engine
from config import DATABASE_URI
from predictions.common_predictor import CommonPredictor
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.ensemble import RandomForestClassifier
from predictions.lol_create_dataset import create_lol_dataset

pd.set_option("display.width", 1000)
pd.set_option("display.max_columns", 50)
from sklearn.feature_selection import SelectKBest
from sklearn.metrics import (
    accuracy_score,
    roc_auc_score,
    classification_report,
    confusion_matrix,
    f1_score,
    median_absolute_error,
    mean_squared_error,
)
from sklearn.model_selection import RandomizedSearchCV
import numpy as np
from config import ROOT_DIR

from sklearn.externals import joblib
from datetime import datetime

# import git


class LoLPredictor:
    def __init__(self):
        self.name = type(self).__name__
        self.X, self.y, self.df = create_lol_dataset()
        try:
            self.model = self.load_saved_model()
        except:
            pass

    @staticmethod
    def get_model_param_grid():
        # Number of trees in random forest
        n_estimators = [int(x) for x in np.linspace(start=200, stop=2000, num=10)]
        # Number of features to consider at every split
        max_features = ["auto", "sqrt"]
        # Maximum number of levels in tree
        max_depth = [int(x) for x in np.linspace(10, 110, num=11)]
        max_depth.append(None)
        # Minimum number of samples required to split a node
        min_samples_split = [2, 5, 10]
        # Minimum number of samples required at each leaf node
        min_samples_leaf = [1, 2, 4]
        # Method of selecting samples for training each tree
        bootstrap = [True, False]
        # Create the random grid
        return {
            "n_estimators": n_estimators,
            "max_features": max_features,
            "max_depth": max_depth,
            "min_samples_split": min_samples_split,
            "min_samples_leaf": min_samples_leaf,
            "bootstrap": bootstrap,
        }

    @staticmethod
    def evaluate(model, x_test, y_t):
        predictions = model.predict(x_test)
        probabilities = model.predict_proba(x_test)

        true_probabilities = probabilities[:, 1]
        mse = mean_squared_error(y_t, true_probabilities)
        mae = median_absolute_error(y_t, true_probabilities)

        acc_score = accuracy_score(y_t, predictions)
        auc_score = roc_auc_score(y_t, predictions)
        classification_score = classification_report(y_t, predictions)
        confusion_score = confusion_matrix(y_t, predictions)
        f_score = f1_score(y_t, predictions)

        print(
            f"Evalutation stats are:\naccuracy score: {acc_score} \n auc_score: {auc_score} \n "
            f"classification_report{classification_score}\n"
            f"conf_score: {confusion_score}\n f_score: {f_score}\n"
            f"mse: {mse}  and mae {mae}"
        )

    def train_model(self):
        reducer = SelectKBest(k=10)

        forrest_params = {
            "forrest__" + key: value
            for key, value in self.get_model_param_grid().items()
        }

        model = RandomForestClassifier()
        params = forrest_params

        # from sklearn.ensemble import GradientBoostingClassifier
        #
        # model = GradientBoostingClassifier()
        # params = {}

        pipe = Pipeline([("reduce_dim", reducer), ("forrest", model)])

        randomized_pipe = RandomizedSearchCV(
            pipe, params, n_iter=100, cv=3, verbose=2, n_jobs=2
        )

        # randomized_pipe = GridSearchCV(pipe, param_grid)
        randomized_pipe.fit(self.X, self.y)
        self.model = randomized_pipe
        return randomized_pipe

    def load_saved_model(self):
        return joblib.load(f"{ROOT_DIR}/data/{self.name}.joblib")["model"]

    def save_model(self, classifier):

        if (
            input("U are going to rewrite model. Are you sure?" " Spec 'yes' if so")
            == "yes"
        ):
            repo = git.Repo(search_parent_directories=True)
            sha = repo.head.object.hexsha
            toBePersisted = dict(
                {
                    "model": classifier,
                    "metadata": {
                        "name": "Lol Pipepiline Model",
                        "author": "Pavel Klammert",
                        "date": datetime.now(),
                        "source_code_version": sha,
                        "metrics": {"acc": classifier.best_score_},
                    },
                }
            )

            joblib.dump(toBePersisted, f"{ROOT_DIR}/data/{self.name}.joblib")
            return True
        else:
            print("New model not set")
            return False

    def predict_one_match(self, row):
        clf = self.model
        labels = clf.classes_
        probabilities = clf.predict_proba(row)
        return {labels[0]: probabilities[0][0], labels[1]: probabilities[0][1]}


if __name__ == "__main__":
    lol = LoLPredictor()
    trained_model = lol.train_model()
    lol.save_model(trained_model)
    print()
