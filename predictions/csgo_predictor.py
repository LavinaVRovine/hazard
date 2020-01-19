import pandas as pd
from sqlalchemy import create_engine
from predictions.common_predictor import CommonPredictor
from config import DATABASE_URI, ROOT_DIR
from data.get_csgo_data import get_csgo_data, remove_id_cols
import mlflow


pd.set_option("display.width", 1000)
pd.set_option("display.max_columns", 50)
DB_URL = f"{DATABASE_URI}csgo"
ENGINE = create_engine(DB_URL)


class CSGOPredictor(CommonPredictor):
    def __init__(self, debug: bool = False):
        super().__init__(debug=debug)
        self.y_col_name = "t1_winner"
        self.training_columns = [
            "wins_n",
            "games_n",
            "winrate_n",
            "wins_c",
            "games_c",
            "winrate_c",
            "kddiffs_n",
            "fkdiff_n",
            "my_rate_n",
            "hs_rate_n",
            "page_rating_n",
            "kddiffs_c",
            "fkdiff_c",
            "my_rate_c",
            "hs_rate_c",
            "page_rating_c",
            "wins_against_each_other",
            "games_against_each_other",
            "winrate_against_each_other",
        ]


if __name__ == "__main__":
    mlflow.set_tracking_uri(f"file:///{ROOT_DIR}/mlruns")
    mlflow.set_experiment("hazard_csgo")

    cs_df = remove_id_cols(get_csgo_data())

    predictor = CSGOPredictor(debug=False)
    predictor.main_train(cs_df, run_name="first run", n_runs=100)

    # predictor.save_model(predictor.train_on_whole(predictor.best_params))
    print()
