import requests
import pandas as pd
import bs4 as bs
import asyncio
import traceback
import csv
import re
from scrape.scrape_helpers import Sess

from scrape.csgo.csgo_game import CSGOGame

pd.set_option('display.width', 1000)
pd.set_option('display.max_columns', 50)

BASE_URL = "https://www.hltv.org"

class CSGOMatch:
    """
    dostanu url na serii teamu proti teamu. najdu detailni statistiky,
    tedy kazdou hru=mapu. to pak parsuji
    """
    def __init__(self, soup, c):
        self.soup = soup
        self.c = c
        self.details_link = self.parse_main_page()
        # TODO: can not exist :=]
        details_response = c.get(BASE_URL+self.details_link)
        self.detailed_soup = bs.BeautifulSoup(details_response.text,"html5lib")
        self.parse_detailed_stats()

    def parse_main_page(self):

        "//div[@class='small-padding']"
        match_stats = self.soup.find("div", {"class": "matchstats"})
        headers = match_stats.find_all("div", {"class": "small-padding"})

        # if headers:
        #   headers = headers.text
        summary_stats = pd.read_html(str(match_stats))
        assert len(headers) - 1 == len(
            summary_stats) / 2, f"Not same len {len(headers)} against {len(summary_stats)}"

        base_info = self.parse_base_info(self.soup)

        detailed_stats = headers[-1]
        detailed_stats_link = detailed_stats.find("a").get("href")
        lineup = self.get_lineup(self.soup)
        return detailed_stats_link

    def parse_base_info(self, soup):
        main_banner = soup.find("div", {"class": "standard-box teamsBox"})

        team_base_info = self.parse_team_base_info(main_banner)

        base_match_info = main_banner.find("div", {"class": "timeAndEvent"})
        unix_time = base_match_info.find("div", {"class": "date"}).get(
            "data-unix")
        formatted_date = base_match_info.find("div", {"class": "date"}).text
        tournament_link = base_match_info.find("a").get("href")
        return {**{"unix_time": unix_time, "formatted_date": formatted_date,
                   "tournament_link": tournament_link},
                **team_base_info}

    def parse_team_base_info(self,main_banner):
        stats = []
        for team in main_banner.find_all("div", {"class": "team"}):
            team_name = team.find("div", {"class": "teamName"}).text
            won_n_matches = team.find("div", {"class": "won"})
            won = True
            if not won_n_matches:
                won = False
                won_n_matches = team.find("div", {"class": "lost"}).text
            else:
                won_n_matches = won_n_matches.text

            stats.append(
                {team_name: {"won": won, "won_n_matches": won_n_matches}})

        return {"teams": stats}

    def get_lineup_team_names(self, lineup_div):
        teams = []
        team_names = lineup_div.find_all("div",
                                         {
                                             "class": "box-headline flex-align-center"})
        for team in team_names:
            team = team.find("a")
            team_url = team.get("href")
            team_name = team.text
            teams.append({team_name: {"team_url": team_url}})
        return teams

    def get_lineup(self, soup):
        lineup = soup.find("div", {"class": "lineups"})
        teams = self.get_lineup_team_names(lineup)

        lineup_table = lineup.find("table")

        data = [[td.a['href'] if td.find('a') else
                 ''.join(td.stripped_strings)
                 for td in row.find_all('td')]
                for row in lineup_table.find_all('tr')]

        for index, roster in enumerate(data):
            teams[index] = {**teams[index], **{"roster": roster}}

        return teams


    def parse_detailed_stats(self):
        maps = self.detailed_soup.find("div", {"class": "stats-match-maps"})
        # maps = maps.find_all("div", {"class":"columns"})
        for a in maps.find_all("a"):
            link = a.get("href")
            map = a.find("div", {
                "class": "stats-match-map-result-mapname dynamic-map-name-full"})
            if "mapstatsid" in link:

                game_id =re.compile("/(\d+)/").findall(link)[0]
                map_name = map.text
                print(link)

                lal = CSGOGame(self.c, link)
                game_info = lal.parse_game_info()
                players_stats = lal.parse_players_stats()
                game_info["game_id"] = game_id
                players_stats["game_id"] = game_id
                players_stats["map_name"] = map_name
                print()