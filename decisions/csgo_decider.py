from decisions.decider import Decider
from data.get_csgo_data import get_csgo_data
from helpers.custom_exceptions import TeamNotFound, NoMatchData
from data.csgo_data_creator import CSGOData


class CSGODecider(Decider):
    def __init__(self, match_row, db_location, data_handler: CSGOData):
        super().__init__(match_row, db_location)
        self.df = get_csgo_data()
        self.data_handler = data_handler

    def decide_match_action(self, predictor) -> dict:
        try:
            match_row = self.data_handler.create_match_stats_row(self.team_1_name, self.team_2_name)
        except (TeamNotFound, NoMatchData) as e:
            print(e)
            return {"team1": self.team_1_name, "team2": self.team_2_name}

        else:
            # no error
            match_row_df = match_row.to_frame().T.reindex(
                columns=predictor.training_columns
            )

            return super().decide(predictor, match_row_df.fillna(0))
