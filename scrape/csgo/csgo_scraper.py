import requests
import pandas as pd
import bs4 as bs
import asyncio
import traceback
import csv
from scrape.scrape_helpers import Sess
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

class CSGOGame:

    def __init__(self, c):
        self.c = c

    def parse_round_history(self, soup):
        wtf = soup.find("div", {"class": "standard-box round-history-con"})
        return

    def format_breakdown(self, breakdown_info):
        """now gets only totals, dont know what to do with rest"""
        totals = breakdown_info.text[:breakdown_info.text.find("(")]
        return totals.strip()

    def parse_game_info(self, soup):
        output = {}
        rows = soup.find_all("div", {"class": "match-info-row"})
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

    def parse_game_details(self,link: str):

        response = self.c.get(BASE_URL + link)
        soup = bs.BeautifulSoup(response.text, "html5lib")

        game_info = self.parse_game_info(soup)

        self.parse_round_history(soup)

        players_stats = pd.read_html(response.text)
        formatted = False

        for team_player_stats in players_stats:
            if not formatted:
                players_stats = self.format_players_game_stats(team_player_stats)
                formatted = True
            else:
                players_stats = pd.concat([players_stats,
                                           self.format_players_game_stats(
                                               team_player_stats)]).reset_index(
                    drop=True)
        print()
        return game_info, players_stats

class CSGOMatch:
    """
    dostanu url na serii teamu proti teamu. najdu detailni statistiky,
    tedy kazdou hru=mapu. to pak parsuji
    """
    def __init__(self, soup, c):
        self.soup = soup
        self.c = c
        self.details_link = self.parse_main_page()
        # can not exist :=]
        details_response = c.get(BASE_URL+self.details_link)
        self.detailed_soup = bs.BeautifulSoup(details_response.text,"html5lib")
        self.parse_detailed()

    def parse_main_page(self):

        "//div[@class='small-padding']"
        match_stats = self.soup.find("div", {"class": "matchstats"})
        headers = match_stats.find_all("div", {"class": "small-padding"})

        # if headers:
        #   headers = headers.text
        summary_stats = pd.read_html(str(match_stats))
        assert len(headers) - 1 == len(
            summary_stats) / 2, f"Not same len {len(headers)} against {len(summary_stats)}"

        base_info = self.parse_base_info(soup)

        detailed_stats = headers[-1]
        detailed_stats_link = detailed_stats.find("a").get("href")
        lineup = self.get_lineup(soup)
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


    def parse_detailed(self):
        maps = self.detailed_soup.find("div", {"class": "stats-match-maps"})
        # maps = maps.find_all("div", {"class":"columns"})
        for a in maps.find_all("a"):
            link = a.get("href")
            map = a.find("div", {
                "class": "stats-match-map-result-mapname dynamic-map-name-full"})
            if "mapstatsid" in link:
                map_name = map.text
                print(link)

                lal = CSGOGame(self.c)
                game_info, players_stats = lal.parse_game_details(link)



if __name__ == "__main__":
    c = Sess()
    url = "https://www.hltv.org/matches/2328545/optic-vs-complexity-cs-summit-3"
    #url = "https://www.hltv.org/stats/matches/61686/optic-vs-complexity"
    response = c.get(url)
    soup = bs.BeautifulSoup(response.text, "html5lib")
    cs_match = CSGOMatch(soup, c)
    cs_match.parse_detailed()

