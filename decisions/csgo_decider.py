import pandas as pd
from decisions.decider import Decider


class CSGODecider(Decider):


    def lookup_team_id(self, team_name):



        if team_name == "FaZe Clan":
            team_name = "FaZe"
        elif team_name == "Team Liquid":
            team_name = "Liquid"

        teams =\
            pd.read_sql("SELECT games_teams.team_id AS t1_id, games_teams.name FROM games_teams GROUP BY games_teams.team_id, games_teams.name", con=self.engine)
        team = teams[teams["name"] == team_name]
        if len(team) == 0:
            return
        else:
            return int(team.iloc[0,0])

    def lookup_team_stats(self, team_name):
        team_id = self.lookup_team_id(team_name)
        if team_id is None:
            return []
        exact_match = pd.read_sql("SELECT * FROM team_stats_filtered where team_id = %s" % (team_id,),
            con=self.engine
        )
        return exact_match