import pandas as pd
import bs4 as bs

pd.set_option('display.width', 1000)
pd.set_option('display.max_columns', 50)


class DotaMatch:
    """
    Representation of dota page of a Match
    """
    def __init__(self, soup):
        """
        sadly, starts whole logic - parses basic info, stats etc.
        Need to call self.get_teams_stats afterwards
        :param soup: BS4 soup object of match page
        """
        self.soup = soup
        # list of teams with base info
        self.teams =\
            self.get_teams(self.soup.find("div", {"class": "team-results"}))
        self.team_names = [t[0] for t in self.teams]
        # dict with League, Game Mode, Region etc.
        self.basic_match_info = self.parse_match_header()
        self.teams_stats = self.parse_team_results()
        # dunno, weird match, dont want to handle rioght now
        if self.teams_stats is False:
            raise ValueError
        self.t1 = None
        self.t2 = None

    def get_teams_stats(self) -> None:
        """
        sets t1 and t2 to have valid information
        :return: None
        """

        for index, team in enumerate(self.team_names):
            if index == 0:
                self.t1 = {"name": team, "winner": self.teams[index][1],
                           "stats": self.teams_stats[team],
                           "link": self.teams[index][2]}
            else:
                self.t2 = {"name": team, "winner": self.teams[index][1],
                           "stats": self.teams_stats[team],
                           "link": self.teams[index][2]}

    def parse_match_header(self) -> dict:
        """
        parses basic info about match itself like league, duration etc.
        :return: dict with League, Game Mode, Region etc.
        """
        header_div = self.soup.find("div", {"class": "header-content"})
        stats = header_div.find("div", {"class": "header-content-secondary"})
        output = {}
        for dl in stats.find_all("dl"):
            header = dl.find("dt").text
            text_value = dl.find("dd").text

            if header == "League":
                league_link = dl.find("a").get("href")
                output[header] = {"value": text_value, "link": league_link}
            elif header == "Match Ended":
                date_time = dl.find("time").get("datetime")
                output[header] = {"value": text_value, "datetime": date_time}
            else:
                output[header] = text_value
        return output

    @staticmethod
    def parse_table_headers(thead):
        nvm = []
        for th in thead.find_all("th"):
            acr = th.find("acronym")
            if acr:
                name = acr.get("title")
            else:
                name = th.text
            nvm.append(name)
        for blocked_elem in ['Overview', 'Farm', 'Damage', 'Items']:
            nvm.remove(blocked_elem)
        # rename header
        if nvm[4] == "":
            nvm[4] = "Player link"
        return nvm

    @staticmethod
    def parse_player_perf_table(trow):
        row_vals = []
        for td in trow.find_all('td'):

            if td.find('a'):
                smth = (td.a['href'])
            elif td.find("i"):
                if td.i.get("oldtitle"):
                    smth = (td.i["oldtitle"])
                elif td.i.get("title"):
                    smth = td.i.get("title")
                else:
                    print(f"dunno {td}")
            else:
                smth = ''.join(td.stripped_strings)
            row_vals.append(smth)
        return row_vals

    def parse_player_performance(self, table) -> pd.DataFrame:
        """
        creates pd.Dataframe from html table of player stats
        :param table: BS4 element of table containing player stats
        :return: unformatted dataframe
        """
        random_list = []
        headers = self.parse_table_headers(table.find("thead"))
        body = table.find("tbody")
        for row in body.find_all('tr'):
            row_vals = self.parse_player_perf_table(row)
            assert len(row_vals) == len(headers),\
                f"Invalid parsing of headers or body"
            random_list.append(row_vals)
        return pd.DataFrame(random_list, columns=headers)

    @staticmethod
    def get_teams(results_div):
        """
        parse teams participating in a match
        :param results_div: BS4 elem of results - HEADERS above players stats
        :return: list of 2 lists containing name, winstatus, link of team
        """
        output = []
        for s in results_div.find_all("section", recursive=False):
            team_name = s.find("header").text
            try:
                team_url = s.find("header").find("a").get("href")
            except:
                team_url = None
            victory_icon = s.find("span", {"class": "victory-icon"})
            if victory_icon:
                won = True
            else:
                won = False
            output.append([team_name, won, team_url])
        return output

    @staticmethod
    def reformat_team_df(magic_df):
        """
        Reformats dataframe containing player statistics to desired output
        :param magic_df: unformatted players Dataframe
        :return: formatted Dataframe
        """
        team_df = magic_df.copy()
        team_df.drop(
            ["", "Items in inventory at the end of the match", "Player"],
            axis=1, inplace=True
        )
        # remove some stupidly named cols
        for col in team_df.copy().columns:
            if "(" in col:
                no_name = col[:col.find("(")-1]
                team_df.rename({col: no_name}, axis=1, inplace=True)

        # change data format
        for col in list(team_df.columns):
            if col == "Hero":
                continue
            team_df[col] = team_df[col].str.replace("k", "000")
        for col in ["Kills", "Deaths", "Assists", "Net Worth", "Last Hits",
                    "Denies", "Gold earned per minute",
                    "Experience earned per minute",
                    "Damage dealt to enemy Heroes",
                    "Healing provided to friendly Heroes",
                    "Damage dealt to enemy buildings"]:
            team_df[col] = pd.to_numeric(team_df[col], errors="coerce")

        return team_df

    def parse_team_results(self):
        """
        parses table of player statistics
        :return: dict with name: pd.Dataframe statistics
        """
        output = {}
        results_div = self.soup.find("div", {"class": "team-results"})
        team_names = self.get_teams(results_div)
        performance_tables = results_div.find_all("table")
        if len(team_names) != len(performance_tables):
            return False
        assert len(team_names) == len(performance_tables), "invalid team names"
        for index, table in enumerate(performance_tables):
            team_df = self.parse_player_performance(table)
            team_df = self.reformat_team_df(team_df)
            output[self.team_names[index]] = team_df

        return output



if __name__ == "__main__":
    from scrape.scrape_helpers import Sess
    resp = Sess().get("https://www.dotabuff.com/matches/4189901985")

    match = DotaMatch(bs.BeautifulSoup(resp.text, "html5lib"))
    match.get_teams_stats()

    print()
