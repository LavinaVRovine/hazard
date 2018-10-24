import requests
from bs4 import BeautifulSoup
import pandas as pd
from sqlalchemy import create_engine
from sqlalchemy_utils import database_exists, create_database


# TODO: make it a generic class and ifortuna subclass
# TODO: WIP - sane subclassing
class Monitor:
    """
    Class represents scraper of a single bookie web page
    Written for ifortuna.cz
    """

    def __init__(self, web_name, game_name, logger, db_location, game_url):
        self.logger = logger
        self.game_name = game_name
        self.game_identifier = "| " + game_name
        self.web_name = web_name
        self.gaming_page = game_url
        self.db_url = db_location
        self.engine = self.check_db(self.db_url)
        self.matches = None
        self.stats_updated = False
        # dont need nor want anything but win-lose betting
        self.game_type = "zápas"
        self.session = requests.Session()

    def get_response(self, url):
        response = self.session.get(url)
        print(f"resp code {response.status_code}")
        return response

    def parse_all_stats(self, ajax_doc):
        return pd.read_html(ajax_doc.replace("\n", ""))

    def update_matches(self, df):
        df["timestamp"] = pd.Timestamp.utcnow()
        if self.matches is None:

            self.matches = df
        else:
            self.matches.concat(df, axis=0, inplace=True)

    # to be overriden per subclass
    def get_bookie_info(self):
        return

    def get_biding_info(self):
        return self.matches[["team1", "team2", "team_1_rate", "team_2_rate"]]

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