import pandas as pd
# from sqlalchemy import create_engine
# from config import DATABASE_URI
from predictions.common_predictor import CommonPredictor
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression

pd.set_option('display.width', 1000)
pd.set_option('display.max_columns', 50)


class LoLPredictor(CommonPredictor):

    def __init__(self):
        super().__init__()
        self.training_columns = \
            ["gold_per_minute", "gold_differential_per_minute",
             "gold_differential_at_15", "cs_per_minute",
             "cs_differential_at_15", "tower_differential_at_15",
             "tower_ratio", "damage_per_minute", "first_blood",
             "kills_per_game", "deaths_per_game", "kda", "dragons_15", 
             "wards_per_minute", "wards_cleared_per_minute",
             "pct_wards_cleared", "c_gold_per_minute",
             "c_gold_differential_per_minute", "c_gold_differential_at_15",
             "c_cs_per_minute", "c_cs_differential_at_15",
             "c_tower_differential_at_15", "c_tower_ratio",
             "c_damage_per_minute", "c_first_blood", "c_kills_per_game",
             "c_deaths_per_game", "c_kda", "c_dragons_15",
             "c_wards_per_minute", "c_wards_cleared_per_minute",
             "c_pct_wards_cleared", "win_rate", "c_win_rate", "n_games",
             "c_n_games", "dragon_game_value", "dragon_game_pct",
             "herald_game_value", "herald_game_pct", "nashors_game_value",
             "nashors_game_pct", "c_dragon_game_value", "c_dragon_game_pct",
             "c_herald_game_value", "c_herald_game_pct",
             "c_nashors_game_value", "c_nashors_game_pct"]
        self.y_col_name = "main_team_won"

    def train_new_model(self, df: pd.DataFrame):

        y = df.pop("t1_winner")
        self.X_train, self.X_test, self.y_train, self.y_test =\
            train_test_split(df, y, test_size=0.2)
        model = LogisticRegression()
        model.fit(self.X_train, self.y_train)
        self.new_model = model
        print("trained new model")

    def train_on_whole(self):
        model = LogisticRegression()
        model.fit(pd.concat([self.X_train, self.X_test]),
                  pd.concat(self.y_train, self.y_test))


if __name__ == "__main__":

    pred = LoLPredictor()
    print()
