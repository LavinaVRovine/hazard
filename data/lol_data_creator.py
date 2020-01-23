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
from .data_creator import MyData


class LOLData(MyData):
    def __init__(self):
        self.engine = create_engine(DATABASE_URI + "lol", echo=False)

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
    #
