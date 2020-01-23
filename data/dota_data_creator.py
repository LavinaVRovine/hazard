import pandas as pd
from helpers.custom_exceptions import TeamNotFound
from sqlalchemy import create_engine
from config import DATABASE_URI
from typing import Optional, Union
import re
from.data_creator import MyData


class DOTAData(MyData):
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
