import re
from bs4 import BeautifulSoup
import pandas as pd
import time
import random
from config import ROOT_DIR
from bookie_monitors.monitor import Monitor


class IfortunaCz(Monitor):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._interesting_bet_options = ["zápas"]

    # FIXME. uses old website layout
    def use_saved_file(self):
        print(f"Using saved file for {self.__name__}")
        file = open(f"{ROOT_DIR}/data/IfortunaCz.html", encoding="utf-8")
        x = file.read()

        all_stats = pd.read_html(x.replace("\n", ""))
        matches = self.format_bookie_data(all_stats[0])
        matches["timestamp"] = pd.Timestamp.utcnow()
        return matches

    def get_parse_page(self):
        response = super().get_response(self.gaming_page)
        return BeautifulSoup(response.content, "html5lib")

    @staticmethod
    def is_invalid_tournament(t_title: str):
        return (
            "ukončení podpory starých" in t_title
            or "Živá hra online" in t_title
            or "celkový vítěz" in t_title
            or "celkovy" in t_title
            or "elkový ví" in t_title
        )

    def process_tournament_table(self, table):
        tournament_title = table.find("h2").text
        if self.is_invalid_tournament(tournament_title) or not self.is_game_tournament(tournament_title):
            return

        try:

            match_stats = pd.read_html(table.find("table").prettify())[0]
        except:
            import traceback
            traceback.print_exc()
            return
        formatted = self.format_bookie_data(match_stats)
        return formatted

    def get_bookie_info(self):
        soup = self.get_parse_page()
        for table in soup.find_all("section", {"class": "competition-box"}):
            formatted = self.process_tournament_table(table=table)
            if formatted is None:
                continue
            super().update_matches(formatted)
            self.stats_updated = True
            print("succesfully updated stats")
        return True

    def is_game_tournament(self, title: str):
        """Kinda stupidly made...if searching for dota, consider only dota"""
        return self.game_name.lower() in title.lower()

    def is_relevant_bid_type(self, bet_type_title):
        return bet_type_title in self._interesting_bet_options

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
        try:
            df[["game_title", "game_id"]] = df.iloc[:, 0].str.rsplit(" ", 1, expand=True)
            df[["team1", "team2"]] = super().split_match_to_teams(df["game_title"])
            df.rename({"1": "team_1_rate", "2": "team_2_rate"}, axis=1, inplace=True)
        except ValueError:
            # most likely velkovy vitez
            return
        return df


if __name__ == "__main__":
    import logging

    c = IfortunaCz(
        game_name="CS:GO",
        logger=logging,
        game_url="https://www.ifortuna.cz/sazeni/e-sporty",
    )
    c.get_bookie_info()
    print()
