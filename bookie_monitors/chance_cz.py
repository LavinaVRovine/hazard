from bookie_monitors.monitor import Monitor
import logging
import requests
from bs4 import BeautifulSoup
import re
import json
from config import ROOT_DIR
pattern = re.compile(r'.*?League of Legends')

#WIP
class ChanceCz(Monitor):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.gaming_page = "https://www.chance.cz/kurzy/e-sporty-188"

    # TODO: update fror reasanable inheritance
    def get_bookie_info(self):

        response = self.get_response(self.gaming_page)
        soup = BeautifulSoup(response.content, 'html.parser')
        for title in soup.find_all("h2"):#, text=pattern):
            if "League of Legends" in title.text:
                print("got lol")
                rows = title.find_all_next("div", {"class": "rowMatchWrapper"})

                for row in rows:
                    link = row.find_next("a", {"class": "matchName"})
                    match = link.text
                    odds_div =  link.find_next("div", {"class": "rowMatchOdds"}) # div class="rowMatchOdds"
                    data = odds_div.find("div").get("data-ev")
                    data_dict = json.loads(data)
                    real_data = data_dict["oppRows"][0]["opps"]
                    stats = {}
                    for one_team in real_data:
                        # kolikaty ten team je.. asi
                        location = one_team["optN"]
                        odds = one_team["rt"]
                        stats[location] = odds
                    print()



    def parse_all_stats(self, ajax_doc):

        soup = BeautifulSoup(open(f"{ROOT_DIR}/data/chance.html", encoding="utf-8"), 'html.parser')
        print(soup)
        print("lalala")
        print(soup.find("h2"))
        for title in soup.find_all("h2"):

            print(f"{title} and match {pattern.match(title)}")
        pass


if __name__ == "__main__":

    c = ChanceCz("chance", game_name="LoL", logger=logging, db_location="")
    c.get_bookie_info()
    print()