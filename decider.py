import pandas as pd
from sqlalchemy import create_engine
pd.set_option('display.width', 1000)
pd.set_option('display.max_columns', 50)


class Decider:
    """
    Decides whether it's worth to bet or not by comparing bookie ods
    against my ML percentage
    """

    def __init__(self, match_row, db_location):
        self.engine = create_engine(
            db_location,
            echo=False)
        self.team_1_name = match_row["team1"]
        self.team_2_name = match_row["team2"]
        self.team_1_rate = match_row["team_1_rate"]
        self.team_2_rate = match_row["team_2_rate"]

    def calc_ods_percent(self, decimal_ods):
        return 1/decimal_ods

    def create_match_stats_row(self):
        main_team = self.lookup_team_stats(self.team_1_name)
        competitor = self.lookup_team_stats(self.team_2_name)
        assert main_team is not None, f"No team {self.team_1_name} in DB"
        assert competitor is not None, f"No team {self.team_2_name} in DB"
        competitor = competitor.add_prefix('c_')
        whole_row = pd.concat([main_team, competitor], axis=1)
        return whole_row

    def lookup_team_stats(self, team_name):
        return pd.read_sql(f"SELECT * FROM teams WHERE name = '{team_name}' ORDER BY season DESC LIMIT 1", con=self.engine)

    @staticmethod
    def is_big_difference(pct_diff):
        return abs(pct_diff) > 0.2

    @staticmethod
    def pct_diff(bookie_pct, my_pct):
        return bookie_pct - my_pct

    def compare_ods(self, my_pct_win_change):
        bookie_pct = self.calc_ods_percent(self.team_1_rate)
        diff = self.pct_diff(bookie_pct, my_pct_win_change)
        if self.is_big_difference(diff):
            return f"should do stuff: bookie pct = {bookie_pct} and mine {my_pct_win_change}"
        else:
            return f"seems like a pass: bookie pct = {bookie_pct} and mine {my_pct_win_change}"

