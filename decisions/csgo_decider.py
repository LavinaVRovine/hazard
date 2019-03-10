import pandas as pd
from decisions.decider import Decider


# todo: ehm, proc se nepracuje s self.team1_name?
class CSGODecider(Decider):

    def __init__(self, match_row, db_location):
        super().__init__(match_row, db_location)
        self.teams = \
            pd.read_sql("SELECT games_teams.team_id AS t1_id, games_teams.name FROM games_teams GROUP BY games_teams.team_id, games_teams.name",
                        con=self.engine)
        self.teams["name"] = self.teams["name"].str.lower()

    def clear_name(self, team_name):
        team_name = team_name.replace("Team", "")
        team_name = team_name.replace("Clan", "")
        team_name = team_name.replace("Gaming", "")
        team_name = team_name.replace("Esports", "")

        return team_name.strip().lower()

    def lookup_team_id(self, team_name):

        team_name = self.clear_name(team_name)

        if team_name == "ex-Fragsters":
            team_name = "Fragsters"

        team = self.teams[self.teams["name"] == team_name]
        if len(team) == 0:
            return
        else:
            return int(team.iloc[0, 0])

    def lookup_team_stats(self, team_name):
        team_id = self.lookup_team_id(team_name)
        if team_id is None:
            return []
        exact_match = pd.read_sql("SELECT * FROM team_stats_filtered where team_id = %s" % (team_id,),
            con=self.engine
        )
        return exact_match
