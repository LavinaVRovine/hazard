import pandas as pd
from decisions.decider import Decider
import traceback

class LoLDecider(Decider):

    def lookup_team_stats(self, team_name):
        ehm = pd.read_sql(
            f"SELECT * FROM avged_preds "
            f"WHERE lower(name) like '%%{team_name.lower()}%%' LIMIT 1",
            con=self.engine)
        if len(ehm) == 0:
            return []
        output = {}
        for col in ehm.columns:
            if col == "name":
                output[col] = ehm.loc[0, col]
            else:
                output[col] = ehm[col].mean()
        return pd.Series(output)

    def decide_match_action(self, predictor):
        df = predictor.df
        # filter t1 against t2
        row = df.loc[(df["name"] == self.team_1_name) & (df["c_name_x"] == self.team_2_name), :]
        # might be multiple seasons
        if len(row) == 0:
            print(
                f"something went wrong for  {self.team_1_name} againt"
                f" competitor {self.team_2_name}")
            traceback.print_exc()
            return {"team1": self.team_1_name, "team2": self.team_2_name}

        elif len(row) > 1:
            row = row[row["season"] == row["season"].max()]
        # possible error. data should? be similar anyway....
        if len(row) > 1:
            row = row.sample(1)
        row = row.loc[:, list(df.select_dtypes(include=['float64']).columns)]
        preds = predictor.predict_one_match(row.fillna(0))
        # now does basically nothing :)
        decision = self.compare_ods(preds[True])

        output = \
            {"team1": self.team_1_name, "team2": self.team_2_name,
             "preds": preds, "decision": decision}

        print(
            f"prediction for {self.team_1_name} againt competitor {self.team_2_name}"
            f" are {preds}   {decision}")
        return output


