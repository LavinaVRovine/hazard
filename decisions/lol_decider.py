import pandas as pd
from decisions.decider import Decider


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
