import pandas as pd
from sqlalchemy import create_engine
pd.set_option('display.width', 1000)
pd.set_option('display.max_columns', 50)
from config import DATABASE_URI
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from predictions.common_predictor import CommonPredictor
from sklearn.ensemble import GradientBoostingClassifier
DB_URL = f"{DATABASE_URI}csgo"
ENGINE = create_engine(DB_URL)

class CSGOPredictor(CommonPredictor):

    def __init__(self):
        super().__init__()
        self.training_columns = ['d', 'kd_diff', 'fk_diff', 'k', 'hs',
             'ratings', 'max_winrate', 'c_d', 'c_kd_diff', 'c_fk_diff',
             'c_k', 'c_hs', 'c_ratings', 'c_max_winrate']

        self.y_col_name = "t1_winner"

    def train_new_model(self, df: pd.DataFrame):

        y = df.pop(self.y_col_name)
        self.X_train, self.X_test, self.y_train, self.y_test =\
            train_test_split(df, y, test_size=0.2, random_state=7)



        model = GradientBoostingClassifier()

        model.fit(self.X_train, self.y_train)
        self.new_model = model
        print(model.score(self.X_test, self.y_test))
        print("trained new model")

    def train_on_whole(self):
        model = GradientBoostingClassifier()
        model.fit(pd.concat([self.X_train, self.X_test]),
                  pd.concat([self.y_train, self.y_test]))
        return model




if __name__ == "__main__":

    df = pd.read_sql_table('stats', con=ENGINE)
    df.fillna(0, inplace=True)
    #y = df.pop("t1_winner")
    df.drop(["t1_id", "t2_id", "kast", "c_kast", "a", "c_a"], axis=1, inplace=True)

    pred = CSGOPredictor()
    pred.train_new_model(df)
    print(pred.eval_predict_proba())

    print(pred.check_differences(pred.new_model))
    pred.save_model(pred.train_on_whole())
    model = pred.new_model
    for name, importance in zip(list(df.columns),
                                model.feature_importances_):
        ...
        print(name, "=", importance)
    print()