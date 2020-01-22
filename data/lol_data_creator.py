import pandas as pd
from data.get_csgo_data import get_csgo_data
import traceback
from data.get_csgo_data import data_if_not_played_before
from helpers.custom_exceptions import TeamNotFound, NoMatchData
from itertools import cycle
from copy import copy
from sqlalchemy import create_engine
from config import DATABASE_URI
from typing import Optional, Union


class LOLData:
    def __init__(self):
        self.engine = create_engine(DATABASE_URI + "lol", echo=False)
    @staticmethod
    def validate_teams(
            main_team: Optional[Union[pd.DataFrame, pd.Series]],
            competitor: Optional[Union[pd.DataFrame, pd.Series]],
    ):

        if main_team is None or len(main_team) == 0:
            print(f"No team {main_team} in DB")
            raise TeamNotFound
        elif competitor is None or len(competitor) == 0:
            print(f"No team {competitor} in DB")
            raise TeamNotFound

    def lookup_team_stats(self, team_name) -> Optional[pd.Series]:
        ehm = pd.read_sql(
            f"SELECT * FROM avged_preds "
            f"WHERE lower(name) like '%%{team_name.lower()}%%' LIMIT 1",
            con=self.engine,
        )
        if len(ehm) == 0:
            return
        output = {}
        for col in ehm.columns:
            if col == "name":
                output[col] = ehm.loc[0, col]
            else:
                output[col] = ehm[col].mean()
        return pd.Series(output)

    def create_match_stats_row(self, team_1_name, team_2_name) -> pd.DataFrame:
        main_team = self.lookup_team_stats(team_1_name)
        competitor = self.lookup_team_stats(team_2_name)
        try:
            self.validate_teams(main_team, competitor)
        except TeamNotFound:
            # todo fix
            raise
        competitor = competitor.add_prefix("c_")
        if type(competitor) == pd.Series or type(main_team) == pd.Series:
            whole_row = pd.concat([main_team, competitor])
            return pd.DataFrame(whole_row).T
        else:
            whole_row = pd.concat([main_team, competitor], axis=1)
        return whole_row
