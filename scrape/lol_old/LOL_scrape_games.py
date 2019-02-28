import requests
import pandas as pd
from bs4 import BeautifulSoup
from lol_db_models.lol_models import  engine,  Game_result, Team_match
import time
import json
import logging

from sqlalchemy.orm import sessionmaker

logging.basicConfig(filename='fails.log', filemode='w', format='%(asctime)s %(name)s - %(levelname)s - %(message)s')

BASE_URL = "http://gol.gg"


class Games_parser():
    def __init__(self, session):
        self.c = session

    def get_results(self, soup, teams):
        # winner is identifierd by img in first column. team 1 is header, ie
        # name of the team, who is listed in col 1. If img present --> won
        team_1 = teams[1]
        team_2 = teams[2]
        results = {team_1:0, team_2:0}
        result_tables = soup.find_all("table", {"class":"summary_table"})
        for table in result_tables:
            first_td = table.find("td")
            if first_td.find("img") is None:
                results[team_2] +=1
            else:
                results[team_1] += 1
        return results



    def get_teams(self, soup):
        table = soup.find("table", {"class": "score_table2"})
        all_tds = table.find_all("td")

        return {1:all_tds[0].text, 2:all_tds[-1].text}
    def parse_page(self, summary_url, df, sql_session):
        url = summary_url
        if "-game" in summary_url:
            summary_url = summary_url.replace("-game", "-summary")


        response = self.c.get(BASE_URL + summary_url)

        assert response.status_code == 200
        soup = BeautifulSoup(response.content, 'html.parser')
        results = self.get_results(soup, self.get_teams(soup))

        only_the_match = df[df["match_url"] == url]
        #assert len(only_the_match) == 2
        if len(only_the_match) != 2:
            logging.error(f"failed game url = {url}")
            return
        winner = max(results, key=results.get)

        winner_row = only_the_match[only_the_match["name"] == winner]
        loser_row = only_the_match[only_the_match["name"] != winner]
        sql_session.add(
            Game_result(match_id=int(winner_row.iloc[0, 0]),
                        main_team_id=int(winner_row.iloc[0, 1]),
                        competitor_team_id=int(loser_row.iloc[0, 1]), score=json.dumps(results),
                        main_team_won=True)
        )
        sql_session.add(
            Game_result(match_id=int(loser_row.iloc[0, 0]),
                    main_team_id=int(loser_row.iloc[0, 1]),
                    competitor_team_id=(int(winner_row.iloc[0, 1])), score=json.dumps(results),
                    main_team_won=False))


        sql_session.query(Team_match).filter(Team_match.match_url == url).update({"scraped": True})


        return


#with requests.Session() as s:

 #   Games_parser(s).parse_page("/game/stats/2476/page-summary/")


# TODO: je naprd, jelikoz bere proste vsechno, ne jen nenascrapovane!

def scrape_pending_games():
    sql_Session = sessionmaker(bind=engine)

    """Provide a transactional scope around a series of operations."""
    session = sql_Session()

    df = pd.read_sql("SELECT team_matches.match_id, team_matches.team_id, team_matches.match_url, teams.name FROM team_matches JOIN teams ON teams.team_id = team_matches.team_id WHERE team_matches.scraped isnull", engine)

    unique_urls = df["match_url"].unique()

    for url in unique_urls:
        time.sleep(0.5)
        with requests.Session() as s:
            Games_parser(s).parse_page(url, df, session)
        try:

            session.commit()




            print(f"url {url}")

        except:
            session.rollback()
            print(f"failed {url}")
            #raise
        finally:
            session.close()

scrape_pending_games()