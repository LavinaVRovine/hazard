import pandas as pd
from sqlalchemy import create_engine
from config import DATABASE_URI
from predictions.common_predictor import CommonPredictor
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier

pd.set_option("display.width", 1000)
pd.set_option("display.max_columns", 50)
from sklearn.metrics import *
import warnings

warnings.filterwarnings("ignore")


class DotaPredictor(CommonPredictor):
    def __init__(self):
        super().__init__()
        self.training_columns = [
            "kills",
            "deaths",
            "assists",
            "worth",
            "last_hits",
            "denies",
            "gold_min",
            "xp_min",
            "dmg_heroes",
            "healing",
            "dmg_buildings",
            "total_win_pct",
            "c_kills",
            "c_deaths",
            "c_assists",
            "c_worth",
            "c_last_hits",
            "c_denies",
            "c_gold_min",
            "c_xp_min",
            "c_dmg_heroes",
            "c_healing",
            "c_dmg_buildings",
            "c_total_win_pct",
        ]
        self.y_col_name = "win"  #'t1_winner'

    def train_new_model(self, _df: pd.DataFrame):

        _df = _df.drop_duplicates()

        y = _df.pop(self.y_col_name)

        self.X_train, self.X_test, self.y_train, self.y_test = train_test_split(
            _df, y, test_size=0.2, random_state=7
        )

        from sklearn.svm import SVC
        from sklearn.ensemble import RandomForestClassifier, VotingClassifier
        from sklearn.model_selection import GridSearchCV

        params = dict(
            n_estimators=[50, 100, 200],
            max_depth=[5, 10, 15],
            max_leaf_nodes=[None, 5, 10],
            bootstrap=[True, False],
            oob_score=[True, False],
            n_jobs=[100, 150, 200],
        )

        model = RandomForestClassifier(
            n_estimators=100, max_depth=10, max_leaf_nodes=10, n_jobs=100
        )
        model = RandomForestClassifier()
        search_model = GridSearchCV(model, params)

        search_model.fit(self.X_train, self.y_train)
        best_model = search_model.best_estimator_
        self.new_model = best_model
        preds = best_model.predict(self.X_test)
        print(best_model.score(self.X_test, self.y_test))
        print("trained new model")
        print(f"roc {roc_auc_score(self.y_test,preds)}")

    def train_on_whole(self):
        model = RandomForestClassifier(
            n_estimators=100, max_depth=10, max_leaf_nodes=10, n_jobs=100
        )
        model.fit(
            pd.concat([self.X_train, self.X_test]),
            pd.concat([self.y_train, self.y_test]),
        )
        return model


if __name__ == "__main__":

    DB_URL = f"{DATABASE_URI}dota"
    ENGINE = create_engine(DB_URL)

    df = pd.read_sql_table("match_stats_all", con=ENGINE)

    # spocitam jaky je winrate mezi teamy.
    totals = df.groupby(["t1_id", "t2_id"])["t1_id"].count()
    wins = df[df["t1_winner"] == True].groupby(["t1_id", "t2_id"])["t1_id"].count()
    win_pcts = wins.divide(totals).reset_index(name="winrate").fillna(0)
    win_pcts["win"] = win_pcts["winrate"] >= 0.5
    df = df.drop("t1_winner", axis=1).drop_duplicates()
    df["joinon"] = df[["t1_id", "t2_id"]].astype(str).apply("-".join, 1)

    win_pcts["joinon"] = win_pcts[["t1_id", "t2_id"]].astype(str).apply("-".join, 1)

    df = pd.merge(df, win_pcts, on="joinon")
    df.drop(
        ["t1_id_x", "t2_id_x", "t1_id_y", "t2_id_y", "joinon", "winrate"],
        axis=1,
        inplace=True,
    )

    # df.drop_duplicates()
    # y = df.pop("t1_winner")
    df.fillna(0, inplace=True)

    pred = DotaPredictor()
    pred.train_new_model(df)
    # pred.compare_models()
    # print(pred.new_model.predict_proba(pred.X_test))
    lala = pred.new_model.predict_proba(pred.X_test)
    import numpy as np

    print(f"a {len(lala[lala > 0.6])}")
    print({len(lala[lala < 0.4])})

    pred.save_model(pred.train_on_whole())

    print()
