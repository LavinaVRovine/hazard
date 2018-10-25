from bookie_monitors.monitor import Monitor
import logging
import requests
from bs4 import BeautifulSoup
import re
import json
import pandas as pd
from config import ROOT_DIR
pattern = re.compile(r'.*?League of Legends')

# WIP
class ChanceCz(Monitor):

    def process_row(self, match_row):
        link = match_row.find_next("a", {"class": "matchName"})
        match = link.text.strip()
        odds_div = link.find_next("div", {
            "class": "rowMatchOdds"})  # div class="rowMatchOdds"
        data = odds_div.find("div").get("data-ev")
        data_dict = json.loads(data)
        real_data = data_dict["oppRows"][0]["opps"]
        stats = {}
        for one_team in real_data:
            # kolikaty ten team je.. asi
            location = one_team["optN"]
            odds = one_team["rt"]
            stats[location] = odds

        return {match: stats}

    def format_bookie_data(self, dict_data):
        df = pd.DataFrame(dict_data).T.reset_index()
        df.rename({"1":"team_1_rate","2":"team_2_rate", "index": "game_title"}, axis=1, inplace=True)
        df[["team1", "team2"]] = super().split_match_to_teams(df["game_title"])
        df["team_1_rate"] = pd.to_numeric(df["team_1_rate"],errors="coerce")
        df["team_2_rate"] = pd.to_numeric(df["team_2_rate"], errors="coerce")
        if "null" in df.columns:
            df.drop("null", axis=1, inplace=True)
        return df

    # TODO: update fror reasanable inheritance
    def get_bookie_info(self):

        response = super().get_response(self.gaming_page)
        soup = BeautifulSoup(response.content, 'html.parser')
        for title in soup.find_all("h2"):#, text=pattern):
            if "League of Legends" in title.text:
                rows = title.find_all_next("div", {"class": "rowMatchWrapper"})
                data = {}

                # TODO: WARNING, CANT IDENTIFY LOL MATCHES ONLY, GOT ALL MATCHES BELLOW THE HEADER
                # does not matter now, since teams are not in team database
                for row in rows:
                    data = {**data, **self.process_row(row)}

                self.update_matches(self.format_bookie_data(dict_data=data))
                self.stats_updated = True
                print("succesfully updated stats")


if __name__ == "__main__":

    monitor = ChanceCz("chance", game_name="LoL", logger=logging,  game_url="https://www.chance.cz/kurzy/e-sporty-188")
    monitor.get_bookie_info()
    lal = monitor.get_biding_info()
    monitor.store_matches()
    print("Finished")