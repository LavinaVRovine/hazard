from decisions.decider import Decider
from data.lol_data_creator import LOLData
from helpers.custom_exceptions import TeamNotFound, NoMatchData


class LoLDecider(Decider):
    def __init__(self, match, db_location, data_handler: LOLData):
        super().__init__(match, db_location)
        self.data_handler = data_handler

    def decide_match_action(self, predictor) -> dict:

        try:
            match_row = self.data_handler.create_match_stats_row(
                self.team_1_name, self.team_2_name
            )
        except (TeamNotFound, NoMatchData) as e:
            print(e)
            return {"team1": self.team_1_name, "team2": self.team_2_name}

        else:
            # no error
            return self.decide(predictor, match_row.fillna(0))
