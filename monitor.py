import requests
from bs4 import BeautifulSoup
import pandas as pd
from sqlalchemy import create_engine
from sqlalchemy_utils import database_exists, create_database
import time
import random


class Monitor:
    """
    Class represents scraper of a single bookie web page
    Written for ifortuna.cz
    """

    def __init__(self, web_name, game_name, logger, db_location):
        self.logger = logger
        self.game_name = game_name
        self.game_identifier = "| " + game_name
        self.web_name = web_name
        gaming_page_mapping =\
            {"ifortuna": "https://www.ifortuna.cz/cz/sazeni/progaming"}
        self.gaming_page = gaming_page_mapping[web_name]
        self.db_url = db_location
        self.engine = self.check_db(self.db_url)
        self._interesting_bet_options = ["zápas"]
        self.ted_jen_toto_no = "zápas"

        file = open("data/ajax_page.html", encoding="utf-8")
        x = file.read()

        all_stats = pd.read_html(x.replace("\n", ""))
        self.matches = self.format_table_result(all_stats[0])
        self.matches["timestamp"] = pd.Timestamp.utcnow()

        self.stats_updated = False

    def clear_test_df(self):
        self.matches = None

    def parse_all_stats(self, ajax_doc):
        return pd.read_html(ajax_doc.replace("\n", ""))

    def update_matches(self, df):
        df["timestamp"] = pd.Timestamp.utcnow()
        if self.matches is None:

            self.matches = df
        else:
            self.matches.concat(df, axis=0, inplace=True)

    def get_stats_doc(self, c, ajax_url):
        for _ in range(0, 10):
            ajax_doc = c.get(ajax_url).text
            if "sázka na výsledek zápas" in ajax_doc or "betTable" in ajax_doc:
                return ajax_doc
            else:
                wait_time = random.randint(20, 60)
                time.sleep(wait_time)
                print(
                    f"Waiting {wait_time} because ajax "
                    f"doc seems corrupted: {ajax_doc}")
        print("Failed to parse ajax DOC!!")
        return False

    def get_actual_bookie_info(self):
        self.clear_test_df()
        with requests.Session() as c:
            response = c.get(self.gaming_page)
            soup = BeautifulSoup(response.content, 'html.parser')

            for title in soup.find_all("h3"):
                ajax_url = self.find_ajax_stats_url(title)
                if ajax_url is None:
                    continue

                ajax_doc= self.get_stats_doc(c, ajax_url)
                if ajax_doc == False:
                    print("fuck")
                all_stats = self.parse_all_stats(ajax_doc)
                formatted = self.format_table_result(all_stats[0])
                # 0 index == zapasy only
                self.update_matches(formatted)
                self.stats_updated = True
                print("succesfully updated stats")


    def find_ajax_stats_url(self, title):
        if self.game_identifier in title.text:
            relevant_div = title.find_next("div")
            assert relevant_div.get("class")[0] == "betTableFilterHolder"
            url_values = []
            for span in relevant_div.find_all("span", {"class": "checkbox"}):
                bet_type_title = span.find("input").get("title")
                # not interested in pocet map and so on
                if self.is_relevant_bid_type(bet_type_title):
                    value = span.find("input").get("value")
                    url_values.append(value)
                    parent = span.parent
                    assert parent.name == "span"
                    link = parent.find("a").get("href")

            ajax_url = self.gaming_page + self.parse_tournament_name(
                link) + "?action=filter_by_subgame&itemTypeId=" + ";".join(
                url_values) + ";&_ajax=1"
            return ajax_url

    def is_relevant_bid_type(self, bet_type_title):
        return bet_type_title in self._interesting_bet_options

    def parse_tournament_name(self, tournament_link):
        return tournament_link[tournament_link.rfind("/"):tournament_link.rfind("?")]

    def get_biding_info(self):
        return self.matches[["team1", "team2", "team_1_rate", "team_2_rate"]]

    @staticmethod
    def check_db(db_url):
        engine = create_engine(db_url, echo=False)
        if not database_exists(engine.url):
            create_database(engine.url)
        return engine

    @staticmethod
    def is_special_table(table):
        return "Handicap mapy" in table.columns or "Počet map" in table.columns

    def format_table_result(self, pd_table):
        """
        :param pd_table: df from webpage
        :return: formatted df
        """
        df = pd_table.copy()
        if self.is_special_table(df):
            print("who cares")
            return {"table_name": df.columns[0], "result": df}
        df[["game_title", "game_id"]] = df.iloc[:, 0].str.rsplit(" ", 1,
                                                                 expand=True)
        df[["team1", "team2"]] = df["game_title"].str.split(" - ", 1,
                                                            expand=True)
        df.rename({"1": "team_1_rate", "2": "team_2_rate"}, axis=1,
                  inplace=True)
        return df

    def store_matches(self):
        assert self.stats_updated is True, "No updated stats, dont put into DB"

        df = self.matches.copy()
        df["web_page"] = self.web_name
        df["type"] = self.ted_jen_toto_no
        df["game"] = self.game_name
        df["my_bid_status"] = None
        df.to_sql("bookie_stats", con=self.engine, if_exists="append", index=False)


if __name__ == "__main__":
    monitor = Monitor("ifortuna", "LoL")
    monitor.get_actual_bookie_info()
    lal = monitor.get_biding_info()
    monitor.store_matches()
    print("Finished")
