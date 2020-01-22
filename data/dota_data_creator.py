import pandas as pd
from helpers.custom_exceptions import TeamNotFound
from sqlalchemy import create_engine
from config import DATABASE_URI
from typing import Optional, Union
import re


class DOTAData:
    def __init__(self):
        self.engine = create_engine(DATABASE_URI + "dota", echo=False)

    def lookup_team_stats(self, team_name):
        team_name = "".join(re.findall("(\w+)", team_name)).lower()
        exact_match = pd.read_sql(
            "SELECT * FROM team_stats_winrate_filtered where lower(regexp_replace(team_name, '[^\w]+','','g')) = '%s'"
            % (team_name,),
            con=self.engine,
        )
        if exact_match is not None:
            return exact_match
        like_match = pd.read_sql(
            "SELECT * FROM team_stats_winrate_filtered where lower(regexp_replace(team_name, '[^\w]+','','g')) like '%%%s%%' LIMIT 1"
            % (team_name,)
            % (team_name,),
            con=self.engine,
        )
        # pozor, muze jich tam byt vice. chce to vybrat ten nejrelevantnejsi
        if like_match is not None:
            return like_match

        return

    def validate_teams(
            self,
            main_team: Optional[Union[pd.DataFrame, pd.Series]],
            competitor: Optional[Union[pd.DataFrame, pd.Series]],
    ):
        try:
            # FIXME need to use the team name you know...
            if main_team is None or len(main_team) == 0:
                print(f"No team {main_team} in DB")
                raise TeamNotFound
            elif competitor is None or len(competitor) == 0:
                print(f"No team {competitor} in DB")
                raise TeamNotFound
        except:
            raise ValueError
        return True

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
