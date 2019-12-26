import pandas as pd
from decisions.decider import Decider
from csgo_db_loader.get_team_stats import get_csgo_data
import traceback


class CSGODecider(Decider):

    def __init__(self, match_row, db_location):
        super().__init__(match_row, db_location)
        self.df = get_csgo_data()

    def clear_name(self, team_name):
        team_name = team_name.replace("Team", "")
        team_name = team_name.replace("Clan", "")
        team_name = team_name.replace("Gaming", "")
        team_name = team_name.replace("Esports", "")
        team_name = team_name.replace("eSports", "")

        return team_name.strip().lower()

    def lookup_team_id(self, team_name):

        team_name = self.clear_name(team_name)

        if team_name == "ex-Fragsters" or team_name == "ex-fragsters":
            team_name = "fragsters"
        elif team_name == 'Ninjas in Pyjamas' or team_name == 'ninjas in pyjamas':
            team_name = "nip"
        elif team_name == 'LDLC.com' or team_name == 'ldlc.com':
            team_name = "ldlc"

        df = pd.read_sql("SELECT * FROM team where name = '{}' LIMIT 1".format(team_name,), con=self.engine)
        if len(df) == 0:
            return
        return int(df.iloc[0, 0])

    def lookup_team_stats(self, team_name):
        team_id = self.lookup_team_id(team_name)
        if team_id is None:
            return []
        exact_match = pd.read_sql("SELECT * FROM team_stats_filtered where team_id = %s" % (team_id,),
            con=self.engine
        )
        return exact_match

    def create_match_stats_row(self):
        main_team_id = self.lookup_team_id(self.team_1_name)
        competitor_id = self.lookup_team_id(self.team_2_name)
        self.validate_teams(main_team_id, competitor_id)

        # TODO. ah, tohle je nakonec vlastne nedobre, jelikoz ted muzu mit jen tymy, ktere proti sobe nekdy hraly
        #  mel bych tam pak pridat moznost
        # TODO. zaroven nezkousim t2 vs t1, coz je u me neco jineho... f its a mess
        row = self.df[(self.df["team_1_id"] == main_team_id) & (self.df["team_2_id"] == competitor_id)]
        # TODO REMO|VE TESting
        #if len(row) == 0:

         #   row = self.df.sample(1)
        return row


    def decide_match_action(self, predictor):
        #match_row = self.create_match_stats_row()
        try:
            match_row = self.create_match_stats_row()
        except ValueError:
            return {"team1": self.team_1_name, "team2": self.team_2_name}


        try:
            match_row = match_row[predictor.training_columns]

            preds = predictor.predict_one_match(match_row.fillna(0))
            # now does basically nothing :)
            decision = self.compare_ods(preds[True])

            output = \
                {"team1": self.team_1_name, "team2": self.team_2_name,
                 "preds": preds, "decision": decision}

            print(
                f"prediction for {self.team_1_name} againt competitor {self.team_2_name}"
                f" are {preds}   {decision}")
            return output
        except:
            print(
                f"something went wrong for  {self.team_1_name} againt"
                f" competitor {self.team_2_name}")
            traceback.print_exc()
            return {"team1": self.team_1_name, "team2": self.team_2_name}


