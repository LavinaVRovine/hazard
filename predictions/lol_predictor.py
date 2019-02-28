import pandas as pd
from sqlalchemy import create_engine
from config import DATABASE_URI
from predictions.common_predictor import CommonPredictor
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
pd.set_option('display.width', 1000)
pd.set_option('display.max_columns', 50)


class LoLPredictor(CommonPredictor):

    def __init__(self):
        super().__init__()
        self.training_columns = \
            ['avg', 'gold_per_minute', 'gold_differential_per_minute',
             'gold_differential_at_15', 'cs_per_minute',
             'cs_differential_at_15', 'tower_differential_at_15',
             'tower_ratio', 'first_tower', 'damage_per_minute',
             'kills_per_game', 'deaths_per_game', 'kda', 'dragon_game',
             'dragons_15', 'nashors_game', 'wards_per_minute',
             'c_avg', 'c_gold_per_minute',
             'c_gold_differential_per_minute', 'c_gold_differential_at_15',
             'c_cs_differential_at_15', 'c_tower_differential_at_15',
             'c_tower_ratio', 'c_first_tower', 'c_damage_per_minute',
             'c_kills_per_game', 'c_deaths_per_game', 'c_kda', 'c_dragon_game',
             'c_dragons_15', 'c_nashors_game']
        self.y_col_name = "main_team_won"

    def train_new_model(self, df: pd.DataFrame):

        y = df.pop(self.y_col_name)
        self.X_train, self.X_test, self.y_train, self.y_test =\
            train_test_split(df, y, test_size=0.2, random_state=7)
        #from sklearn.ensemble import GradientBoostingClassifier
        #model = GradientBoostingClassifier()
        model = RandomForestClassifier(n_estimators=200, max_depth=12, max_leaf_nodes=12, n_jobs=100)
        model.fit(self.X_train, self.y_train)
        self.new_model = model
        print("trained new model")

    def train_on_whole(self):
        model = RandomForestClassifier(n_estimators=200, max_depth=12, max_leaf_nodes=12, n_jobs=100)
        model.fit(pd.concat([self.X_train, self.X_test]),
                  pd.concat([self.y_train, self.y_test]))
        return model


if __name__ == "__main__":
    DB_URL = f"{DATABASE_URI}lol"
    ENGINE = create_engine(DB_URL)

    dropcols = ["match_url", "ffs", "name", "c_match_url", "c_ffs", "c_name",
                "first_blood", "herald_game", "wards_cleared_per_minute", "pct_wards_cleared",
                "c_cs_per_minute", "c_first_blood", "c_wards_per_minute", "c_wards_cleared_per_minute",
                "c_average_game_duration", "average_game_duration" ,"c_herald_game", "c_pct_wards_cleared" ]
    df = pd.read_sql_table("averaged_predictions", con=ENGINE)

    df = df.drop(dropcols, axis=1)
    df = df.fillna(0)


    # df = pd.read_sql_table("basic_predictions", con=ENGINE)
    #
    #
    # from LOL_formatter import Formatter
    #
    # def format_train_df( train_dataset):
    #     formatter = Formatter(train_dataset)
    #     df = formatter.main_reformat()
    #     df = formatter.drop_for_predict(df)
    #     # names NEEDED for DA
    #
    #     df.drop(["name", "c_name"], axis=1, inplace=True)
    #     return df
    #
    # df = format_train_df(df)

    pred = LoLPredictor()
    pred.train_new_model(df)
    print(pred.new_model.score(pred.X_test, pred.y_test))

    for name, importance in zip(list(df.columns),
                                pred.new_model.feature_importances_):
        ...
        print(name, "=", importance)

    #pred.save_model(pred.train_on_whole())
    print()
