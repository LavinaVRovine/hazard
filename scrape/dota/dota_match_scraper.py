import requests
import pandas as pd
import bs4 as bs
from sqlalchemy import create_engine
import numpy as np
import traceback
import psycopg2
import random
pd.set_option('display.width', 1000)
pd.set_option('display.max_columns', 50)


class DotaMatch:
    def __init__(self, soup):
        self.soup = soup
        self.teams =\
            self.get_teams(self.soup.find("div", {"class": "team-results"}))
        self.team_names = [t[0] for t in self.teams]
        self.basic_match_info = self.parse_match_header()
        self.teams_stats  = self.parse_team_results()
        # dunno, weird match, dont want to handle rioght now
        if self.teams_stats is False:
            return
        self.t1 = None
        self.t2 = None
        self.get_pandified_stats()

    def get_pandified_stats(self) -> None:

        for index,team in enumerate(self.team_names):
            if index == 0:
                self.t1 = {"name":team,"winner": self.teams[index][1], "stats": self.teams_stats[team], "link":self.teams[index][2]}
            else:
                self.t2 = {"name": team, "winner": self.teams[index][1],
                      "stats": self.teams_stats[team],"link":self.teams[index][2]}



    def parse_match_header(self):
        header_div = self.soup.find("div", {"class": "header-content"})
        stats = header_div.find("div", {"class": "header-content-secondary"})
        output = {}
        for dl in stats.find_all("dl"):
            header = dl.find("dt").text
            text_value = dl.find("dd").text

            if header == "League":
                league_link = dl.find("a").get("href")
                output[header] = {"value":text_value, "link":league_link}
            elif header == "Match Ended":
                date_time = dl.find("time").get("datetime")
                output[header] = {"value": text_value, "datetime": date_time}
            else:
                output[header] = text_value
        return output

    def parse_table_headers(self, thead):
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

    def parse_player_perf_table(self, trow):
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
        random_list = []
        headers = self.parse_table_headers(table.find("thead"))

        body = table.find("tbody")
        for row in body.find_all('tr'):
            row_vals = self.parse_player_perf_table(row)
            assert len(row_vals) == len(headers), f"Invalid parsing of headers or body"
            random_list.append(row_vals)

        return pd.DataFrame(random_list,columns=headers)

    def get_teams(self, results_div):
        output = []
        for s in results_div.find_all("section", recursive=False):
            team_name = s.find("header").text
            try:
                team_url = s.find("header").find("a").get("href")
            except:
                team_url = None
            victory_icon = s.find("span",{"class":"victory-icon"})
            if victory_icon:
                won = True
            else:
                won = False
            output.append([team_name, won, team_url])
        return output
        #return [a.find("header").text for a in results_div.find_all("section", recursive=False)]


    def reformat_team_df(self, magic_df):
        team_df = magic_df.copy()
        team_df.drop(["", "Items in inventory at the end of the match", "Player"], axis=1, inplace=True)
        # remove some stupidly named cols
        for col in team_df.copy().columns:
            if "(" in col:
                no_name = col[:col.find("(")-1]
                team_df.rename({col:no_name}, axis=1, inplace=True)

        for col in list(team_df.columns):
            if col == "Hero":
                continue
            team_df[col] = team_df[col].str.replace("k", "000")

        for col in ["Kills", "Deaths", "Assists", "Net Worth", "Last Hits",
                    "Denies", "Gold earned per minute", "Experience earned per minute",
                    "Damage dealt to enemy Heroes", "Healing provided to friendly Heroes",
                    "Damage dealt to enemy buildings"]:
            team_df[col] = pd.to_numeric(team_df[col], errors="coerce")

        return team_df


    def parse_team_results(self):
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





