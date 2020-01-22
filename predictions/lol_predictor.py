import pandas as pd
import mlflow.sklearn
from sqlalchemy import create_engine
from config import DATABASE_URI

from predictions.common_predictor import CommonPredictor
from config import ROOT_DIR

pd.set_option("display.width", 1000)
pd.set_option("display.max_columns", 50)


class LoLPredictor(CommonPredictor):
    def __init__(self, debug: bool = False):
        super().__init__(debug=debug)
        self.training_columns = [
            "avg",
            "gold_per_minute",
            "gold_differential_per_minute",
            "gold_differential_at_15",
            "cs_per_minute",
            "cs_differential_at_15",
            "tower_differential_at_15",
            "tower_ratio",
            "first_tower",
            "damage_per_minute",
            "kills_per_game",
            "deaths_per_game",
            "kda",
            "dragon_game",
            "dragons_15",
            "nashors_game",
            "wards_per_minute",
            "c_avg",
            "c_gold_per_minute",
            "c_gold_differential_per_minute",
            "c_gold_differential_at_15",
            "c_cs_differential_at_15",
            "c_tower_differential_at_15",
            "c_tower_ratio",
            "c_first_tower",
            "c_damage_per_minute",
            "c_kills_per_game",
            "c_deaths_per_game",
            "c_kda",
            "c_dragon_game",
            "c_dragons_15",
            "c_nashors_game",
        ]
        self.y_col_name = "main_team_won"


if __name__ == "__main__":

    print()

    mlflow.set_tracking_uri(f"file:///{ROOT_DIR}/mlruns")
    mlflow.set_experiment("hazard_lol")
    lol = LoLPredictor()
    con = create_engine(DATABASE_URI + "lol", echo=False)
    df_all = pd.read_sql("SELECT * FROM averaged_predictions", con=con)
    lol.main_train(df_all, run_name="save run", n_runs=30)
    print()
    # todo musi byt v current run
    # mlflow.sklearn.save_model(lol.model, path=f"{ROOT_DIR}/models/ttt", conda_env=f"{ROOT_DIR}/environment.yaml")
    # mlflow.sklearn.log_model(lol.model, artifact_path=f"{ROOT_DIR}/ttt", conda_env=f"{ROOT_DIR}/environment.yaml")
