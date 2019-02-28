import requests
import re
from bs4 import BeautifulSoup
import pandas as pd
import time
import random
from config import ROOT_DIR, DEBUG
from bookie_monitors.monitor import Monitor


class IfortunaCz(Monitor):

    def __init__(self, *args, **kwargs):

        super().__init__(*args, **kwargs)
        self._interesting_bet_options = ["zápas"]

    def parse_data_from_doc(self, ajax_doc):
        return pd.read_html(ajax_doc.replace("\n", ""))

    def get_stats_doc(self, ajax_url):
        for _ in range(0, 10):
            ajax_doc = super().get_response(ajax_url).text
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

    def use_saved_file(self):
        print(f"Using saved file for {self.web_name}")
        file = open(f"{ROOT_DIR}/data/IfortunaCz.html", encoding="utf-8")
        x = file.read()

        all_stats = pd.read_html(x.replace("\n", ""))
        matches = self.format_bookie_data(all_stats[0])
        matches["timestamp"] = pd.Timestamp.utcnow()
        return matches

    def get_tournament_info(self):
        pass

    # TODO: dunno. should be handeled here or in main?
    # TODO: split into mupltiple methods
    def get_bookie_info(self):
        if DEBUG:
            self.matches = self.use_saved_file()
        else:
            response = super().get_response(self.gaming_page)
            soup = BeautifulSoup(response.content, 'html.parser')

            for title in soup.find_all("h3"):
                ajax_url = self.find_ajax_stats_url(title)
                if ajax_url is None:
                    continue

                ajax_doc = self.get_stats_doc(ajax_url)
                if ajax_doc is False:
                    print(f"Something wen wrong with for {ajax_url}")
                    continue
                all_stats = self.parse_data_from_doc(ajax_doc)
                # zápasy only
                match_stats = all_stats[0]
                formatted = self.format_bookie_data(match_stats)
                super().update_matches(formatted)
                self.stats_updated = True
                print("succesfully updated stats")
            return True

    def find_ajax_stats_url(self, title):
        # ga
        if "| " + self.game_name in title.text and "celkov" not in title.text:
            relevant_div = title.find_next("div")
            link = None
            #assert relevant_div.get("class")[0] == "betTableFilterHolder"
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
            # nevim zda se že to předělali? važně nevim
            if link is None:
                th = relevant_div.find("th")
                link = th.find("a").get("href")

                rrr = re.compile("itemTypeId=(\d+)")
                neco_id = rrr.findall(link)
                if neco_id == []:
                    return
                url_values = [neco_id[0]]

            ajax_url = self.gaming_page + self.parse_tournament_name(
                link) + "?action=filter_by_subgame&itemTypeId=" + ";".join(
                url_values) + ";&_ajax=1"
            return ajax_url

    def is_relevant_bid_type(self, bet_type_title):
        return bet_type_title in self._interesting_bet_options

    def parse_tournament_name(self, tournament_link):
        return tournament_link[tournament_link.rfind("/"):tournament_link.rfind("?")]

    @staticmethod
    def is_special_table(table):
        return "Handicap mapy" in table.columns or "Počet map" in table.columns

    def format_bookie_data(self, pd_table):
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
        df[["team1", "team2"]] = super().split_match_to_teams(df["game_title"])
        df.rename({"1": "team_1_rate", "2": "team_2_rate"}, axis=1,
                  inplace=True)
        return df


if __name__ == "__main__":
    import logging
    #c = IfortunaCz("chance", game_name="LoL", logger=logging,  game_url="https://www.ifortuna.cz/cz/sazeni/progaming")
    DEBUG = False
    c = IfortunaCz("ifortuna", game_name="Dota", logger=logging,
                   game_url="https://www.ifortuna.cz/cz/sazeni/progaming")
    c.get_bookie_info()
    print()
