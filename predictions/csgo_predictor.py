import pandas as pd
from sqlalchemy import create_engine
from predictions.common_predictor import CommonPredictor
from config import DATABASE_URI
from data.get_csgo_data import get_csgo_data
import mlflow


pd.set_option("display.width", 1000)
pd.set_option("display.max_columns", 50)
DB_URL = f"{DATABASE_URI}csgo"
ENGINE = create_engine(DB_URL)


# TODO: remove df from init
class CSGOPredictor(CommonPredictor):
    def __init__(self, df, debug: bool = False):
        super().__init__(debug=debug)
        self.df = df
        self.y_col_name = "t1_winner"
        self.training_columns = list(set(df.columns))
        self.training_columns.remove(self.y_col_name)


if __name__ == "__main__":

    cs_df = get_csgo_data()
    pred = CSGOPredictor(cs_df)
    from config import ROOT_DIR

    mlflow.set_tracking_uri(f"file:///{ROOT_DIR}/mlruns")
    mlflow.set_experiment("hazard_csgo")
    predictor = CSGOPredictor(debug=True, df=cs_df)
    predictor.main_train(cs_df, run_name="first run")

    print()
