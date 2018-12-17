import pandas as pd
from sqlalchemy import create_engine
from config import DATABASE_URI
from predictions.common_predictor import CommonPredictor
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression

pd.set_option('display.width', 1000)
pd.set_option('display.max_columns', 50)


class DotaPredictor(CommonPredictor):

    def __init__(self):
        super().__init__()
        self.training_columns = ['kills', 'deaths', 'assists', 'worth',
                                 'last_hits', 'denies', 'gold_min', 'xp_min',
                                 'dmg_heroes', 'healing', 'dmg_buildings',
                                 'c_kills', 'c_deaths', 'c_assists', 'c_worth',
                                 'c_last_hits', 'c_denies', 'c_gold_min',
                                 'c_xp_min', 'c_dmg_heroes', 'c_healing',
                                 'c_dmg_buildings']
        self.y_col_name = 't1_winner',

    def train_new_model(self, _df: pd.DataFrame):

        y = _df.pop("t1_winner")


        self.X_train, self.X_test, self.y_train, self.y_test =\
            train_test_split(_df, y, test_size=0.2)

        from sklearn.svm import SVC
        from sklearn.ensemble import RandomForestClassifier, VotingClassifier
        from sklearn.tree import DecisionTreeClassifier
        # lr =  LogisticRegression()
        # rf = RandomForestClassifier()
        # svc = SVC()
        #
        # model = VotingClassifier(estimators=[("lr", lr), ("rf", rf), ("svc", svc)],voting='soft', probability=True)
        #
        from sklearn.ensemble import AdaBoostClassifier

        model = AdaBoostClassifier(

            DecisionTreeClassifier(max_depth=1), n_estimators=200,

            algorithm="SAMME", learning_rate=0.5, random_state=42)



        model.fit(self.X_train, self.y_train)
        self.new_model = model
        print("trained new model")

    def train_on_whole(self):
        model = LogisticRegression()
        model.fit(pd.concat([self.X_train, self.X_test]),
                  pd.concat(self.y_train, self.y_test))


if __name__ == "__main__":

    DB_URL = f"{DATABASE_URI}dota"
    ENGINE = create_engine(DB_URL)

    # df = pd.read_sql_table("game_stats_reduced_to_matches", con=ENGINE)
    # df.drop(["year_of_game", "team_id",'League_value',
    #  'League_link', 'Game Mode', 'Region', 'Duration', 'Match Ended_value',
    #  'Match Ended_datetime',
    #         't1_id', 't2_id', 't1_name', 't2_name', 't2_winner', 't1_link',
    #  't2_link', 'match_link', 'match_id','c_year_of_game', 'c_team_id',
    #  'game_year',
    #         "series_link", "min_series_match", "win_pct",
    #  "t1_winner", "redundant_team_id"], axis=1, inplace=True)

    df = pd.read_sql_table("game_stats", con=ENGINE)
    df.drop(["year_of_game", "team_id", 'League_value', 'League_link',
             'Game Mode', 'Region', 'Duration', 'Match Ended_value',
             'Match Ended_datetime',
             't1_id', 't2_id', 't1_name', 't2_name', 't2_winner',
             't1_link', 't2_link', 'match_link', 'match_id', 'c_year_of_game',
             'c_team_id', 'game_year'], axis=1, inplace=True
            )

    # df.drop_duplicates()
    # y = df.pop("t1_winner")
    df.fillna(0, inplace=True)

    pred = DotaPredictor()
    pred.train_new_model(df)
    pred.compare_models()

    print()
