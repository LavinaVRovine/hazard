import pandas as pd
from sqlalchemy import create_engine
from config import DATABASE_URI
from predictions.common_predictor import CommonPredictor
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import RandomizedSearchCV


pd.set_option("display.width", 1000)
pd.set_option("display.max_columns", 50)

RANDOM_STATE = 7
DEBUG = True

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

    def set_data(self, df: pd.DataFrame) -> bool:
        y = df.pop(self.y_col_name)
        df = df.loc[:, self.training_columns].fillna(0)
        self.X_train, self.X_test, self.y_train, self.y_test = \
            train_test_split(df, y, test_size=0.2, random_state=RANDOM_STATE if DEBUG else None)

    def train_new_model(self, df: pd.DataFrame):

        self.set_data(df)
        #from sklearn.ensemble import GradientBoostingClassifier
        #model = GradientBoostingClassifier()

        import numpy as np
        # Number of trees in random forest
        n_estimators = [int(x) for x in np.linspace(start=200, stop=2000, num=10)]
        # Number of features to consider at every split
        max_features = ['auto', 'sqrt']
        # Maximum number of levels in tree
        max_depth = [int(x) for x in np.linspace(10, 110, num=11)]
        max_depth.append(None)
        # Minimum number of samples required to split a node
        min_samples_split = [2, 5, 10]
        # Minimum number of samples required at each leaf node
        min_samples_leaf = [1, 2, 4]
        # Method of selecting samples for training each tree
        bootstrap = [True, False]  # Create the random grid
        random_grid = {'n_estimators': n_estimators,
                       'max_features': max_features,
                       'max_depth': max_depth,
                       'min_samples_split': min_samples_split,
                       'min_samples_leaf': min_samples_leaf,
                       'bootstrap': bootstrap}
        rf_model = RandomForestClassifier()
        model = RandomizedSearchCV(rf_model, param_distributions=random_grid, n_iter=25, cv=3, random_state=RANDOM_STATE if DEBUG else None, )

        model.fit(self.X_train, self.y_train)

        self.model = model.best_estimator_
        self.best_params = model.best_params_
        print("trained new model")

    def train_on_whole(self, best_params: dict):
        model = RandomForestClassifier(**best_params)
        model.fit(pd.concat([self.X_train, self.X_test]),
                  pd.concat([self.y_train, self.y_test]))
        return model


if __name__ == "__main__":
    lol = LoLPredictor()
    con = create_engine(DATABASE_URI+"lol", echo=False)
    df = pd.read_sql("SELECT * FROM averaged_predictions", con=con)
    #lol.train_new_model(df)
    print()
