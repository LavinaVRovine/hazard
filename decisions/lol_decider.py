import pandas as pd
from decisions.decider import Decider
from typing import Optional


class LoLDecider(Decider):
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

    def decide_match_action(self, predictor):

        match_row = super().create_match_stats_row()
        try:
            preds = predictor.predict_one_match(match_row.fillna(0))
        except:
            return {}
        # now does basically nothing :)
        decision = self.compare_ods(preds[True])

        output = {
            "team1": self.team_1_name,
            "team2": self.team_2_name,
            "preds": preds,
            "decision": decision,
        }

        print(
            f"prediction for {self.team_1_name} againt competitor {self.team_2_name}"
            f" are {preds}   {decision}"
        )
        return output
