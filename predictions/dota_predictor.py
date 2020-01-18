import pandas as pd
from sqlalchemy import create_engine
from config import DATABASE_URI
from predictions.common_predictor import CommonPredictor

pd.set_option("display.width", 1000)
pd.set_option("display.max_columns", 50)


class DotaPredictor(CommonPredictor):
    def __init__(self, debug: bool = False):
        super().__init__(debug=debug)
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
    import mlflow
    from config import ROOT_DIR

    mlflow.set_tracking_uri(f"file:///{ROOT_DIR}/mlruns")
    mlflow.set_experiment("hazard_dota")

    pred = DotaPredictor(debug=True)
    pred.main_train(df, run_name="first run")
    print()
