import requests
from bs4 import BeautifulSoup
from lol_db_models.lol_models import Team, engine, Player_team, Team_match
import re
import time
import random
import logging
from sqlalchemy.orm import sessionmaker

logging.basicConfig(filename='fails.log', filemode='w', format='%(asctime)s %(name)s - %(levelname)s - %(message)s')


# auto update LOL je asi nereálný, nechce se přepisovat

BASE_URL = "http://gol.gg/"
tournaments_url = "/tournament/list/region-ALL/"


class Team_parser():

    def __init__(self, team_link, req_session, sql_session):
        self.team_url = team_link
        self.c = req_session
        self.team_stats = {}
        self.line_up = {}
        self.games = {}
        self.sql_session = sql_session
        self.parse_page()


    def clear_stats(self):
        self.team_stats.pop("")
        regex = re.compile("(\d{1,3}\.?\d?)\s?%")
        try:
            self.team_stats["First Tower"] = regex.findall(self.team_stats["First Tower"])[0]
        except:
            self.team_stats["First Tower"] = None

        try:
            self.team_stats["First Blood"] = \
            regex.findall(self.team_stats["First Blood"])[0]
        except:
            self.team_stats["First Blood"] = None


        try:
            self.team_stats["% Wards Cleared"] = regex.findall(self.team_stats["% Wards Cleared"])[0]
        except:
            self.team_stats["% Wards Cleared"] = None

        for key, value in self.team_stats.items():
            value = value.strip()
            if value == "-":
                self.team_stats[key] == None


    def get_stats(self):
        self.clear_stats()
        stats = self.team_stats
        x = Team(name=stats["Team Name"], season=stats["Season"],
                 region=stats["Region"], win_to_lose=stats["Win Rate"],
                 average_game_duration=stats["Average game duration"],
                 gold_per_minute=stats["Gold Per Minute"],
                 gold_differential_per_minute=stats[
                     "Gold Differential per Minute"],
                 gold_differential_at_15=stats["Gold Differential at 15 min"],
                 cs_per_minute=stats["CS Per Minute"],
                 cs_differential_at_15=stats["CS Differential at 15 min"],
                 tower_differential_at_15=stats[
                     "Tower Differential at 15 min"],
                 tower_ratio=stats["Tower Ratio"],
                 first_tower=stats["First Tower"],
                 damage_per_minute=stats["Damage Per Minute"],
                 first_blood=stats["First Blood"],
                 kills_per_game=stats["Kills Per Game"],
                 deaths_per_game=stats["Deaths Per Game"],
                 kda=stats["Kill / Death Ratio"],
                 dragon_game=stats["Dragons / game"],
                 dragons_15=stats["Dragons at 15 min"],
                 herald_game=stats["Herald / game"],
                 nashors_game=stats["Nashors / game"],
                 wards_per_minute=stats["Wards Per Minute"],
                 vision_wards_per_minute=stats["Vision Wards Per Minute"],
                 wards_cleared_per_minute=stats["Wards Cleared Per Minute"],
                 pct_wards_cleared=stats["% Wards Cleared"])
        self.sql_session.add(x)


        return x
    def get_line_up(self, team_id):

        for player, player_url in self.line_up.items():
            self.sql_session.add(
                Player_team(team_id=team_id, player_name=player,
                            player_url=player_url))

        return self.line_up
    def get_games(self, team_id):

        for game_title, game_url in self.games.items():
            self.sql_session.add(
                Team_match(team_id=team_id, match_title=game_title,
                           match_url=game_url))
        return self.games

    @staticmethod
    def parse_basic_info(table):
        output = {}
        for i, tr in enumerate(table.find_all("tr")):
            tds = tr.find_all("td")
            if len(tds) > 0:
                col_name = tds[0].text.replace(":", "").strip()
                output[col_name] = tds[1].text
        return output

    @staticmethod
    def parse_lineup(table):
        output = {}
        for i, tr in enumerate(table.find_all("tr")):
            # header
            if i == 0 or i == 1:
                continue
            # 5 players and two headers
            if i > 6:
                assert len(output.keys()) == 5
                return output
            tds = tr.find_all("td")
            if len(tds) > 0:
                player_name = tds[1].text
                player_url = tds[1].find("a").get("href")[2:]
                output[player_name] = player_url
        return output

    @staticmethod
    def parse_games(table):
        output = {}
        for i, tr in enumerate(table.find_all("tr")):
            # header
            if i == 0:
                continue
            tds = tr.find_all("td")
            if len(tds) > 0:
                game_title = tds[2].text
                game_url = tds[2].find("a").get("href")[2:]
                output[game_title] = game_url
        return output

    def parse_page(self):
        response = self.c.get(BASE_URL + "teams" + self.team_url)
        assert response.status_code == 200
        soup = BeautifulSoup(response.content, 'html.parser')
        self.team_stats = {}
        for i, table in enumerate(
                soup.find_all("table", {"class": "table_list"})):
            section_name = table.find("th").text
            if i == 0:
                assert "- S" in section_name, "Check basic stats "

                basic_info = self.parse_basic_info(table)
                team_name = table.find("th").text
                team_name = team_name[: team_name.rfind("-")].strip()
                basic_info["Team Name"] = team_name
                self.team_stats = {**self.team_stats, **basic_info}
            elif i == 3:
                assert section_name == "Economy"
                economy = self.parse_basic_info(table)
                self.team_stats = {**self.team_stats, **economy}
            elif i == 4:
                assert section_name == "Aggression"
                aggression = self.parse_basic_info(table)
                self.team_stats = {**self.team_stats, **aggression}
            elif i == 5:
                assert section_name == "Objectives"
                objectives = self.parse_basic_info(table)
                self.team_stats = {**self.team_stats, **objectives}
            elif i == 6:
                assert section_name == "Vision"
                vision = self.parse_basic_info(table)
                self.team_stats = {**self.team_stats, **vision}
            elif i == 9:
                assert section_name == "Role"
                # assert table.find()
                self.line_up = self.parse_lineup(table)
            elif i == 10:
                assert section_name == "Result"
                self.games = self.parse_games(table)

            else:
                continue

class S_scraper():

    def __init__(self, a, req_session):
        self.a = a
        self.req_session = req_session


    def start(self,sql_session):

        team_link = self.a.get("href")[1:]

        team = Team_parser(team_link, self.req_session)
        stats = team.get_stats()
        lineup = team.get_line_up()
        games = team.get_games()


        x = Team(name=stats["Team Name"], season=stats["Season"], region=stats["Region"],win_to_lose=stats["Win Rate"],
             average_game_duration=stats["Average game duration"], gold_per_minute=stats["Gold Per Minute"], gold_differential_per_minute=stats["Gold Differential per Minute"],
             gold_differential_at_15=stats["Gold Differential at 15 min"],cs_per_minute=stats["CS Per Minute"], cs_differential_at_15=stats["CS Differential at 15 min"],
             tower_differential_at_15=stats["Tower Differential at 15 min"], tower_ratio=stats["Tower Ratio"],first_tower=stats["First Tower"],damage_per_minute=stats["Damage Per Minute"],
             first_blood=stats["First Blood"], kills_per_game=stats["Kills Per Game"], deaths_per_game=stats["Deaths Per Game"], KDA=stats["Kill / Death Ratio"],
             dragon_game=stats["Dragons / game"], dragons_15=stats["Dragons at 15 min"],herald_game=stats["Herald / game"], nashors_game=stats["Nashors / game"],
             wards_per_minute=stats["Wards Per Minute"], vision_wards_per_minute=stats["Vision Wards Per Minute"],wards_cleared_per_minute=stats["Wards Cleared Per Minute"],
             pct_wards_cleared=stats["% Wards Cleared"])
        sql_session.add(x)
        sql_session.commit()


        for player, player_url in lineup.items():
            sql_session.add(Player_team(team_id=x.team_id, player_name=player, player_url=player_url))

        for game_title, game_url in games.items():
            sql_session.add(Team_match(team_id=x.team_id,match_title=game_title, match_url=game_url))
        #Team, engine, Table, Player_team
        sql_session.commit()




        time.sleep(random.randint(1,3))



    # ed_user = Team(name='ed')
    # session.add(ed_user)
    # session.commit()

from contextlib import contextmanager

@contextmanager
def session_scope():
    sql_Session = sessionmaker(bind=engine)

    """Provide a transactional scope around a series of operations."""
    session = sql_Session()
    try:
        yield session
        session.commit()
    except:
        logging.error(f"failed ")
        session.rollback()
        raise
    finally:
        session.close()

def scrape_season(season="S8"):
    sql_session = sessionmaker(bind=engine)

    """Provide a transactional scope around a series of operations."""
    session = sql_session()

    url = f"http://gol.gg/teams/list/season-{season}/split-ALL/region-ALL/tournament-ALL/week-ALL/"
    with requests.Session() as c:
        response = c.get(url)
        soup = BeautifulSoup(response.content, 'html.parser')
        rel_table = soup.find('table', {
            'class': 'table_list playerslist tablesaw trhover'})
        assert rel_table

        for a in rel_table.find_all("a"):
            time.sleep(0.5)

            try:
                team_link = a.get("href")[1:]

                team = Team_parser(team_link, c, session)
                stats = team.get_stats()
                session.commit()
                lineup = team.get_line_up(stats.team_id)
                games = team.get_games(stats.team_id)

                session.commit()
                print(f"done {a}")



            except:
                session.rollback()
                logging.error(f"failed for {a}")
                print(f"failed {a}")
                # raise
            finally:
                session.close()

scrape_season("S9")
