import pandas as pd
from data.get_csgo_data import get_csgo_data
import traceback
from data.get_csgo_data import data_if_not_played_before
from helpers.custom_exceptions import TeamNotFound, NoMatchData
from itertools import cycle
from copy import copy
from sqlalchemy import create_engine
from config import DATABASE_URI


class CSGOData:
    def __init__(self):
        self.engine = create_engine(DATABASE_URI + "csgo", echo=False)
        self.df = get_csgo_data()

    @staticmethod
    def clear_name(team_name):
        # TODO, tady pouziji ten yield
        team_name = team_name.replace("Team", "")
        team_name = team_name.replace("Clan", "")
        team_name = team_name.replace("Gaming", "")
        team_name = team_name.replace("Esports", "")
        team_name = team_name.replace("eSports", "")

        team_name = team_name.replace("team", "")
        team_name = team_name.replace("clan", "")
        team_name = team_name.replace("gaming", "")
        team_name = team_name.replace("esports", "")
        team_name = team_name.replace("esports", "")

        return team_name.strip().lower()

    # todo better lookup - withou clearing, with some, full etc
    def lookup_team_ids(self, team_name) -> list:
        """
        find team ids if by team name. Used as bookies have only names...
        :param team_name:
        :return:list of possible ids, most comonnly only single value
        :raises not found exception, if teamname is not in db
        """
        orig_name = copy(team_name)
        team_name = self.clear_name(team_name)

        if team_name == "ex-Fragsters" or team_name == "ex-fragsters":
            team_name = "fragsters"
        elif team_name == "Ninjas in Pyjamas" or team_name == "ninjas in pyjamas":
            team_name = "nip"
        elif team_name == "LDLC.com" or team_name == "ldlc.com":
            team_name = "ldlc"

        df = pd.read_sql(
            "SELECT * FROM team where name = %(t_name)s".format(team_name,),
            con=self.engine,
            params={"t_name": team_name},
        )
        if len(df) == 0:
            raise TeamNotFound(f"Team name {orig_name} -> {team_name}: not found")

        return df.drop_duplicates()["id"].to_list()

    def build_row(self, t1_id, t2_id) -> pd.Series:
        row = self.df[(self.df["team_1_id"] == t1_id) & (self.df["team_2_id"] == t2_id)]

        if len(row) == 0:
            return data_if_not_played_before(t1_id, t2_id)
        return row.iloc[0, :]

    def create_match_stats_row(self, t1_name, t2_name) -> pd.Series:
        try:
            main_team_id = self.lookup_team_ids(t1_name)
            competitor_id = self.lookup_team_ids(t2_name)
        except TeamNotFound:
            traceback.print_exc()
            raise
        id_combinations = (
            zip(main_team_id, cycle(competitor_id))
            if len(main_team_id) > len(competitor_id)
            else zip(cycle(main_team_id), competitor_id)
        )
        for a, b in id_combinations:
            try:
                r = self.build_row(a, b)
            except NoMatchData:
                continue
            else:
                # no error
                return r
        raise NoMatchData
