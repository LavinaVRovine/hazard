import pandas as pd
from helpers.custom_exceptions import TeamNotFound
from abc import ABC, abstractmethod
from typing import Optional, Union


class MyData(ABC):

    @abstractmethod
    def lookup_team_stats(self):
        pass

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
