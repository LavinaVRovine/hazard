import traceback
import pandas as pd
from sqlalchemy import create_engine
from typing import Union, Optional
pd.set_option("display.width", 1000)
pd.set_option("display.max_columns", 50)


class Decider:
    """
    Decides whether it's worth to bet or not by comparing bookie ods
    against my ML percentage
    """

    def __init__(self, match_row, db_location):
        self.engine = create_engine(db_location, echo=False)
        self.team_1_name = match_row["team1"].strip().lower()
        self.team_2_name = match_row["team2"].strip().lower()
        self.team_1_rate = match_row["team_1_rate"]
        self.team_2_rate = match_row["team_2_rate"]

    @staticmethod
    def calc_ods_percent(decimal_ods) -> float:
        return 1 / decimal_ods

    def validate_teams(self, main_team: Optional[Union[pd.DataFrame, pd.Series]], competitor: Optional[Union[pd.DataFrame, pd.Series]]):
        try:
            if main_team is None or len(main_team) == 0:
                print(f"No team {self.team_1_name} in DB")
                raise ValueError
            elif competitor is None or len(competitor) == 0:
                print(f"No team {self.team_2_name} in DB")
                raise ValueError
        except:
            raise ValueError
        return True

    def create_match_stats_row(self) -> pd.DataFrame:
        main_team = self.lookup_team_stats(self.team_1_name)
        competitor = self.lookup_team_stats(self.team_2_name)
        try:
            self.validate_teams(main_team, competitor)
        except ValueError:
            # todo fix
            return
        competitor = competitor.add_prefix("c_")
        if type(competitor) == pd.Series or type(main_team) == pd.Series:
            whole_row = pd.concat([main_team, competitor])
            return pd.DataFrame(whole_row).T
        else:
            whole_row = pd.concat([main_team, competitor], axis=1)
        return whole_row

    def lookup_team_stats(self, team_name):
        pass

    @staticmethod
    def is_big_difference(pct_diff):
        return abs(pct_diff) > 0.2

    @staticmethod
    def pct_diff(bookie_pct, my_pct):
        return bookie_pct - my_pct

    def compare_ods(self, my_pct_win_change):
        bookie_pct = self.calc_ods_percent(float(self.team_1_rate))
        diff = self.pct_diff(bookie_pct, my_pct_win_change)
        if self.is_big_difference(diff):
            return (
                f"should do stuff: bookie pct = {bookie_pct} "
                f"and mine {my_pct_win_change}"
            )
        else:
            return (
                f"seems like a pass: bookie pct = {bookie_pct} "
                f"and mine {my_pct_win_change}"
            )

    def decide_match_action(self, predictor):
        #match_row = self.create_match_stats_row()
        try:
            match_row = self.create_match_stats_row()
        except ValueError:
            return {"team1": self.team_1_name, "team2": self.team_2_name}

        match_row = match_row[predictor.training_columns]
        return self.decide(predictor, match_row.fillna(0))

    def decide(self, predictor, prediction_row) -> dict:
        try:
            preds = predictor.predict_one_match(prediction_row.fillna(0))
            # now does basically nothing :)
            decision = self.compare_ods(preds[True])

            output = {
                "team1": self.team_1_name,
                "team2": self.team_2_name,
                "preds": preds,
                "decision": decision,
            }

            print(
                f"prediction for {self.team_1_name} againt competitor {self.team_2_name}"
                f" are {preds}   {decision}"
            )
            return output
        except:
            print(
                f"something went wrong for  {self.team_1_name} againt"
                f" competitor {self.team_2_name}"
            )
            traceback.print_exc()
            return {"team1": self.team_1_name, "team2": self.team_2_name}
