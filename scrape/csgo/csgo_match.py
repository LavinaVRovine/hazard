import pandas as pd
import bs4 as bs
from scrape.csgo.csgo_game import CSGOGame
from helpers.helpers import parse_number
import datetime
pd.set_option('display.width', 1000)
pd.set_option('display.max_columns', 50)

BASE_URL = "https://www.hltv.org"


class CSGOMatch:
    """
    Match, ie series of games for one team against other team
    """
    def __init__(self, soup, c):
        """

        :param soup: bs4 soup object of the match page
        :param c: requests session

        """
        self.soup = soup
        self.c = c
        self.details_link = self.get_details_url()
        if self.details_link is None:
            raise ValueError
        self.info = self.parse_base_info()

        details_response = c.get(BASE_URL+self.details_link)
        self.detailed_soup =\
            bs.BeautifulSoup(details_response.text, "html5lib")

    def get_details_url(self):
        """
        Statistics are on details page.
        :return: link to details page or None
        """
        match_stats = self.soup.find("div", {"class": "matchstats"})
        if not match_stats:
            return
        headers = match_stats.find_all("div", {"class": "small-padding"})
        # game stats
        # summary_stats = pd.read_html(str(match_stats))
        # assert len(headers) - 1 == len(
        #    summary_stats) / 2, f"Not same len {len(headers)}
        #  against {len(summary_stats)}"
        detailed_stats = headers[-1]
        detailed_stats_link = detailed_stats.find("a")
        if detailed_stats_link:
            return detailed_stats_link.get("href")
        else:
            return

    def parse_base_info(self):
        """
        Parses basic info about match, like time, tournament etc
        :return: dict with time, unix time and tournament link
        """
        main_banner = self.soup.find("div", {"class": "standard-box teamsBox"})

        team_base_info = self.parse_team_base_info(main_banner)

        base_match_info = main_banner.find("div", {"class": "timeAndEvent"})
        unix_time = base_match_info.find("div", {"class": "date"}).get(
            "data-unix")
        unix_time = datetime.datetime.fromtimestamp(int(unix_time[:-3]))
        formatted_date = base_match_info.find("div", {"class": "date"}).text
        tournament_link = base_match_info.find("a").get("href")
        return {**{"unix_time": unix_time, "formatted_date": formatted_date,
                   "tournament_link": tournament_link},
                **team_base_info}

    @staticmethod
    def parse_team_base_info(main_banner):
        """
        Parses basic informations about teams participating in a match
        :param main_banner: BS tag corresponding to match banner
        :return: dict with name, score and win status of both teams
        """

        stats = {}
        for index, team in enumerate(main_banner.find_all(
                "div", {"class": "team"})):
            t_identifier = f"t{index + 1}_"

            team_name = team.find("div", {"class": "teamName"}).text
            won_n_matches = team.find("div", {"class": "won"})
            won = True
            if not won_n_matches:
                won = False
                won_n_matches = int(team.find("div", {"class": "lost"}).text)
            else:
                won_n_matches = int(won_n_matches.text)
            stats = {**stats,
                     **{f"{t_identifier}name": team_name,
                        f"{t_identifier}winner": won,
                        f"{t_identifier}won_n_matches": won_n_matches}}
        return stats

    @staticmethod
    def get_lineup_team_names(lineup_div):
        """
        Parses team names and link
        :param lineup_div: BS4 div element
        :return: list of dicts
        """
        teams = []
        team_names = lineup_div.find_all("div", {
            "class": "box-headline flex-align-center"})
        for team in team_names:
            team = team.find("a")
            team_url = team.get("href")
            team_name = team.text
            teams.append({team_name: {"team_url": team_url}})
        return teams

    def get_lineup(self):
        """
        Parses team names and players playing in that match
        :return: list of teams containing dict with info
        """
        lineup = self.soup.find("div", {"class": "lineups"})
        teams = self.get_lineup_team_names(lineup)

        lineup_table = lineup.find("table")

        data = [[td.a['href'] if td.find('a') else
                 ''.join(td.stripped_strings)
                 for td in row.find_all('td')]
                for row in lineup_table.find_all('tr')]

        for index, roster in enumerate(data):
            teams[index] = {**teams[index], **{"roster": roster}}
        return teams

    def parse_old_games_layout(self):
        """
        Sometimes page does not have games listed, which can happen with old
        matches. Statistics are present directly in details page. Method
        parses it
        :return: game object
        """

        info_box = self.detailed_soup.find("div", {"class": "match-info-box"})
        info_contents = info_box.contents
        site_game_id = parse_number(self.details_link)
        map_name = ""
        # find map name. not accessible directly from BS
        for index, content in enumerate(info_contents):
            if type(content) != bs.element.Tag:
                continue
            span = content.find("span", {"class": "bold"})
            if span:
                text = span.text
                if text == "Map":
                    # the value after map is name of the map
                    map_name = info_contents[index+1]
        link = self.details_link
        game = CSGOGame(self.c, link, map_name, int(site_game_id))
        return game

    def get_games_info(self):
        """
        Gets statistics about game in match
        :return: list of game objects if any, else empty list
        """
        maps = self.detailed_soup.find("div", {"class": "stats-match-maps"})
        games = []
        for a in maps.find_all("a"):
            link = a.get("href")
            map_div = a.find("div", {
                "class":
                    "stats-match-map-result-mapname dynamic-map-name-full"})
            if "mapstatsid" in link:
                site_game_id = parse_number(link)
                map_name = map_div.text
                game = CSGOGame(self.c, link, map_name, int(site_game_id))
                games.append(game)

        # mabye no games, just one old page
        if len(games) == 0:

            game = self.parse_old_games_layout()
            games.append(game)

        return games
