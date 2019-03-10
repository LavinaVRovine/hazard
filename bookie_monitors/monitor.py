import requests
import pandas as pd
from sqlalchemy import create_engine
from sqlalchemy_utils import database_exists, create_database
from config import DATABASE_URI


# TODO: make it a generic class and ifortuna subclass
# TODO: WIP - sane subclassing
class Monitor:
    """
    Class represents scraper of a single bookie web page
    Written for ifortuna.cz
    """

    def __init__(self, web_name, game_name, logger, game_url):
        self.logger = logger
        self.game_name = game_name
        self.web_name = web_name
        self.gaming_page = game_url
        self.db_url = DATABASE_URI + "monitor"
        self.engine = self.check_db(self.db_url)
        self.matches = None
        self.stats_updated = False
        # dont need nor want anything but win-lose betting
        self.game_type = "zápas"
        self.session = requests.Session()

    def get_response(self, url):

        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:65.0) Gecko/20100101 Firefox/65.0',
        }

        response = self.session.get(url, headers=headers)
        assert response.status_code == 200
        return response

    def update_matches(self, df):
        df["timestamp"] = pd.Timestamp.utcnow()
        if self.matches is None:

            self.matches = df
        else:
            self.matches = pd.concat([self.matches, df], axis=0)

    # TODO: find out if this even makes sense
    # to be overriden per subclass
    def get_bookie_info(self):
        return

    # to be overriden per subclass
    def format_bookie_data(self):
        return

    @staticmethod
    def split_match_to_teams(match_title_series):
        return match_title_series.str.split(" - ", 1, expand=True)

    def get_biding_info(self):
        return self.matches[
            ["team1", "team2", "team_1_rate", "team_2_rate", "datum"]
        ]

    @staticmethod
    def check_db(db_url):
        engine = create_engine(db_url, echo=False)
        if not database_exists(engine.url):
            create_database(engine.url)
        return engine

    def store_matches(self):
        assert self.stats_updated is True, "No updated stats, dont put into DB"

        df = self.matches.copy()
        df["web_page"] = self.web_name
        df["type"] = self.game_type
        df["game"] = self.game_name
        df["my_bid_status"] = None
        df.to_sql("bookie_stats", con=self.engine, if_exists="append",
                  index=False)


if __name__ == "__main__":
    monitor = Monitor("ifortuna", "LoL")
    monitor.get_bookie_info()
    lal = monitor.get_biding_info()
    monitor.store_matches()
    print("Finished")
