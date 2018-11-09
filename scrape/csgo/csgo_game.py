import requests
import pandas as pd
import bs4 as bs
import asyncio
import traceback
import csv
import re
from scrape.scrape_helpers import Sess


pd.set_option('display.width', 1000)
pd.set_option('display.max_columns', 50)

BASE_URL = "https://www.hltv.org"


class CSGOGame:

    def __init__(self, c, link):
        self.c = c
        self.url = BASE_URL + link
        self.response = self.get_response()
        self.soup = self.get_soup_page()
        t1, t2 = self.parse_players_stats()
        self.parse_winners()

    def get_response(self):
        return self.c.get(self.url)

    def get_soup_page(self):
        return bs.BeautifulSoup(self.response.text,"html5lib")


    def parse_round_history(self, soup):
        wtf = soup.find("div", {"class": "standard-box round-history-con"})
        return

    def format_breakdown(self, breakdown_info):
        """now gets only totals, dont know what to do with rest"""
        totals = breakdown_info.text[:breakdown_info.text.find("(")]
        return totals.strip()

    # TODO: add who won :)

    def parse_winners(self):
        info_box = self.soup.find("div", {"class": "match-info-box"})
        t1_info = info_box.find("div", {"class": "team-left"})
        t2_info = info_box.find("div", {"class": "team-right"})
        t1_name = t1_info.find("a").text
        t2_name = t1_info.find("a").text

        print()

    def parse_game_info(self):
        output = {}
        rows = self.soup.find_all("div", {"class": "match-info-row"})
        for row in rows:
            row_name = row.find("div", {"class": "bold"})
            row_value = row.find("div", {"class": "right"})

            if row_name.text == "Breakdown":
                output["Totals"] = self.format_breakdown(row_value)
            output[row_name.text] = str(row_value)
        return output

    def format_players_game_stats(self, df: pd.DataFrame) -> pd.DataFrame:
        team_name = df.columns[0]
        df.rename({team_name: "players"}, axis=1, inplace=True)
        df["team_name"] = team_name
        return df

    def parse_players_stats(self):
        players_stats = pd.read_html(self.response.text)
        return [TeamPlayerStats(t) for t in players_stats]


        players_stats = pd.read_html(self.response.text)
        formatted = False

        for t in players_stats:
            team = TeamPlayerStats(t)

        for team_player_stats in players_stats:
            if not formatted:
                players_stats = self.format_players_game_stats(
                    team_player_stats)
                formatted = True
            else:
                players_stats = pd.concat([players_stats,
                                           self.format_players_game_stats(
                                               team_player_stats)]).reset_index(
                    drop=True)
        return  players_stats

class TeamPlayerStats:
    def __init__(self, df:pd.DataFrame):
        self.team_name = df.columns[0]
        df.rename({self.team_name: "players"}, axis=1, inplace=True)
        self.stats = df