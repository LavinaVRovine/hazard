import pandas as pd
from sqlalchemy import create_engine
from sklearn.model_selection import train_test_split
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.ensemble import RandomForestClassifier
from predictions.common_predictor import CommonPredictor
from config import DATABASE_URI
from mlflow import log_metric, log_param, log_artifact
from csgo_db_loader.get_csgo_data import get_csgo_data
import mlflow

pd.set_option("display.width", 1000)
pd.set_option("display.max_columns", 50)
DB_URL = f"{DATABASE_URI}csgo"
ENGINE = create_engine(DB_URL)


class CSGOPredictor(CommonPredictor):
    def __init__(self, df):
        super().__init__()
        self.df = df
        self.y_col_name = "t1_winner"
        self.training_columns = list(set(df.columns))
        self.training_columns.remove(self.y_col_name)

    def train_new_model(self, df: pd.DataFrame, model=None):
        if model is None:
            model = GradientBoostingClassifier()
        y = df.pop(self.y_col_name)
        self.X_train, self.X_test, self.y_train, self.y_test = train_test_split(
            df, y, test_size=0.2, random_state=7
        )

        model.fit(self.X_train, self.y_train)
        self.new_model = model
        # print(model.score(self.X_test, self.y_test))
        print("trained new model")

    def train_on_whole(self, model=None):
        if not model:
            model = GradientBoostingClassifier()
        model.fit(
            pd.concat([self.X_train, self.X_test]),
            pd.concat([self.y_train, self.y_test]),
        )
        return model


if __name__ == "__main__":
    from sklearn.svm import SVC
    from sklearn.ensemble import (
        RandomForestClassifier,
        VotingClassifier,
        GradientBoostingClassifier,
    )
    from sklearn.model_selection import GridSearchCV, RandomizedSearchCV
    from sklearn.metrics import log_loss, make_scorer

    scorer = make_scorer(log_loss, greater_is_better=False, needs_proba=True)
    params = dict(
        n_estimators=[50, 100, 200, 400],
        max_depth=[5, 10, 15, 25, 50],
        max_leaf_nodes=[None, 5, 10],
        bootstrap=[True, False],
        n_jobs=[100, 150, 200],
        min_samples_leaf=[1, 2, 4],
        min_samples_split=[2, 5, 10],
        max_features=["sqrt", 0.25, 0.5, 0.75, 1.0],
    )

    df = get_csgo_data()
    pred = CSGOPredictor(df)
    with mlflow.start_run():
        model = RandomForestClassifier()
        search_model = RandomizedSearchCV(
            model, params, n_iter=15, scoring=scorer, cv=5
        )
        # search_model = GridSearchCV(model, params, cv=3, scoring=scorer)
        pred.train_new_model(df, search_model)

        m = pred.new_model.best_estimator_
        pred.check_differences(m)
        from sklearn.metrics import roc_auc_score

        preds = m.predict(pred.X_test)
        print(m.score(pred.X_test, pred.y_test))
        print("trained new model")
        print(f"roc {roc_auc_score(pred.y_test, preds)}")
