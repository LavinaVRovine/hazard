import requests
import pandas as pd
import bs4 as bs
import asyncio
import traceback
import csv
import re
from scrape.scrape_helpers import Sess
from scrape.csgo.csgo_match import CSGOMatch
pd.set_option('display.width', 1000)
pd.set_option('display.max_columns', 50)

BASE_URL = "https://www.hltv.org"

# gets urls of all matches
def get_csgo_matches():
    offset = 0
    urls = set()
    with requests.session() as c:

        while offset < 40544 :
            url = f"https://www.hltv.org/results?offset={offset}"
            try:
                response = c.get(url)
                soup = bs.BeautifulSoup(response.text,"html5lib")

                for match in soup.find_all("div",{"class":"result-con"}):
                    match_url = match.find("a").get("href")
                    urls.add(match_url)
                offset += 100

                if offset % 1000 == 0:
                    print(f"successfully run {offset}")
            except:
                pd.Series(list(urls)).to_csv("csgo_matches.csv", index=False)
                print(traceback.print_exc())
                print(f"Failed at offset {offset}")
                exit()
        else:
            pd.Series(list(urls)).to_csv("csgo_matches.csv", index=False)
            print("Done")
# TODO: POZOR UZ NENI V CSV ALE V DB!
#get_csgo_matches()

from dataclasses import dataclass

@dataclass
class Team:
    name: str

d = Team("a")


if __name__ == "__main__":
    c = Sess()
    url = "https://www.hltv.org/matches/2328545/optic-vs-complexity-cs-summit-3"
    #url = "https://www.hltv.org/stats/matches/61686/optic-vs-complexity"
    response = c.get(url)
    soup = bs.BeautifulSoup(response.text, "html5lib")
    cs_match = CSGOMatch(soup, c)
    print()

