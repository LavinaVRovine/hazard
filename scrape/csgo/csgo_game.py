import pandas as pd
import bs4 as bs
# from dataclasses import dataclass
from helpers.helpers import parse_number

pd.set_option('display.width', 1000)
pd.set_option('display.max_columns', 50)

BASE_URL = "https://www.hltv.org"


class CSGOGame:
    """
    One game of a match with outcomes and statistics
    """

    def __init__(self, c, link, map_name, site_game_id):
        """
        :param c: requests session
        :param link: url link of the game page
        :param map_name: name of the map
        :param site_game_id: id of the game as presented on the page
        """
        self.c = c
        self.url = BASE_URL + link
        self.response = self.get_response()
        self.soup = self.get_soup_page()
        self.map_name = map_name
        self.site_game_id = site_game_id
        # list of pd.Dataframes containing player stats
        t1_player_stats, t2_player_stats = self.parse_players_stats()
        # Teams participating in a game
        self.t1 = Team(**self.parse_team_basic_info(1))
        self.t2 = Team(**self.parse_team_basic_info(2))
        self.t1.set_player_stats(t1_player_stats)
        self.t2.set_player_stats(t2_player_stats)

    def get_response(self):
        return self.c.get(self.url)

    def get_soup_page(self):
        return bs.BeautifulSoup(self.response.text, "html5lib")

    # def parse_round_history(self, soup):
    #    wtf = soup.find("div", {"class": "standard-box round-history-con"})
    #   return

    @staticmethod
    def format_breakdown(breakdown_info):
        """now gets only totals, dont know what to do with rest"""
        totals = breakdown_info.text[:breakdown_info.text.find("(")]
        return totals.strip()

    @staticmethod
    def is_winner(team_info):
        """
        decides if team won and what was his score
        :param team_info: bs team_info element
        :return:
            True and score if winner
            False and score if loser
            None and score if its a tie
            :exception otherwise
        """
        win = team_info.find("div", {"class": "bold won"})
        # old identifier is not bold...
        if win is None:
            win = team_info.find("div", {"class": "won"})
        if win:
            return True, int(win.text)

        lost = team_info.find("div", {"class": "bold lost"})
        if lost is None:
            lost = team_info.find("div", {"class": "lost"})
        if lost:
            return False, int(lost.text)

        tie = team_info.find("div", {"class": "bold"})
        if tie:
            return None, int(tie.text)
        raise Exception("failed to parse game winner")

    def parse_team_basic_info(self, which_team):
        """
        parses basic information about team participating in a game
        :param which_team: int, which identifies if its main team or competitor
        :return: dict with team info
            :exception if invalid param
        """
        info_box = self.soup.find("div", {"class": "match-info-box"})
        if which_team == 1:
            x = "team-left"
        elif which_team == 2:
            x = "team-right"
        else:
            raise AttributeError
        team_info = info_box.find("div", {"class": x})

        team_id = parse_number(team_info.find("a").get("href"))

        team_name = team_info.find("a").text
        team_is_winner, team_score = self.is_winner(team_info)
        return {"name": team_name, "winner": team_is_winner,
                "score": team_score, "team_id": team_id}

    def parse_game_info(self):
        """
        parses an info box
        :return:
        """
        output = {}
        rows = self.soup.find_all("div", {"class": "match-info-row"})
        for row in rows:
            row_name = row.find("div", {"class": "bold"})
            row_value = row.find("div", {"class": "right"})

            if row_name.text == "Breakdown":
                output["Totals"] = self.format_breakdown(row_value)
            output[row_name.text] = str(row_value)
        return output

    def parse_players_stats(self):
        """
        gets table of player statistics for the game
        :return: list of pd.dataframes
        """
        players_stats = pd.read_html(self.response.text)
        return [t for t in players_stats]


# wanted to try dataclasses:0
#@dataclass()
class Team:
    """
    Represents team participating in a game
    """

    def __init__(self, name ,winner, score, team_id, player_stats=None):
        self.name = name
        self.winner = winner
        self.score = score
        self.team_id = team_id
        self.player_stats = player_stats
    # name: str
    # winner: bool
    # score: int
    # team_id: int
    # player_stats: pd.DataFrame = None

    def set_player_stats(self, df: pd.DataFrame):
        """
        # nota pythonic way to update player stats
        :param df: unformatted dataframe parsed from page
        :return: None -> sets instance var
        """
        df.rename({self.name: "player"}, axis=1, inplace=True)
        self.player_stats = self.reformat_df(df)

    @staticmethod
    def reformat_df(df):
        """
        prepares dataframe to be inserted into database
        :param df: dataframe of player stats
        :return: formatted dataframe
        """
        if "K (hs)" in df.columns:
            df[["K", "HS"]] = df["K (hs)"].str.split("(", expand=True)
            df["HS"] = df["HS"].str.replace(")", "")
            df.drop("K (hs)", axis=1, inplace=True)
        if "A (f)" in df.columns:
            df[["A", "F"]] = df["A (f)"].str.split("(", expand=True)
            df["F"] = df["F"].str.replace(")", "")
            df.drop("A (f)", axis=1, inplace=True)

        df["KAST"] = df["KAST"].str.replace("%", "")
        if "Rating1.0" in df.columns:
            df.rename({"Rating1.0": "rating1"}, axis=1, inplace=True)
        if "Rating2.0" in df.columns:
            df.rename({"Rating2.0": "rating2"}, axis=1, inplace=True)

        for c in ["K", "HS", "A", "F", "KAST"]:
            if c not in df.columns:
                df[c] = None
        df[["K", "HS", "A", "F", "KAST"]] =\
            df[["K", "HS", "A", "F", "KAST"]].apply(
                pd.to_numeric, errors="coerce")
        df["KAST"] = df["KAST"] / 100
        return df
