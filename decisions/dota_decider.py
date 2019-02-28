import pandas as pd
import re
from decisions.decider import Decider


class DotaDecider(Decider):
    def lookup_team_stats(self, team_name):
        team_name = "".join(re.findall("(\w+)", team_name)).lower()
        exact_match = pd.read_sql(
            "SELECT * FROM team_stats_winrate_filtered where lower(regexp_replace(team_name, '[^\w]+','','g')) = '%s'" % (team_name,),
            con=self.engine
        )
        if exact_match is not None:
            return exact_match
        like_match = pd.read_sql(
            "SELECT * FROM team_stats_winrate_filtered where lower(regexp_replace(team_name, '[^\w]+','','g')) like '%%%s%%' LIMIT 1" % (team_name,)   % (team_name,),
            con=self.engine
        )
        # pozor, muze jich tam byt vice. chce to vybrat ten nejrelevantnejsi
        if like_match is not None:
            return like_match

        return