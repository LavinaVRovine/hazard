import requests
import pandas as pd
import bs4 as bs
import time
import random
import re
import traceback
import psycopg2
from sqlalchemy import create_engine
pd.set_option('display.width', 1000)
pd.set_option('display.max_columns', 50)


# scrapovalo se tak, ze se vzaly zapasy, z nich teamy,
# hitnul se team a oscrapovaly se vsechny jeho zapasy.
# to proto, ze team obsahuje vsechny zapasy. seznam zapasu jako takovych neni


# zatim funguje tak, ze mam vsechny teamy, pro ty loopuji a meru vsechny jejich matche
# pokud je oponent nekdo, koho nemam v db jako team, tak je pridan -> je nutno potom neyet jeste nekolikrat...

# musim pote nejak vyresit to, ze takhle nemam moznost updatovat, aneb scrapovalo by se vse znovu :D

team_link = "esports/teams/3-complexity-gaming"


agent = "User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/64.0.3282.140 Safari/537.36 Edge/18.17763"
BASE_URL = "https://www.dotabuff.com"

db_url = "postgres://postgres:Darthpic0@localhost/dota"
engine = create_engine((db_url))
url = f"https://www.dotabuff.com/{team_link}/matches?date=all"


class TeamScraper:
    def __init__(self, team_row, all_teams, forced_url = None):

        team_link = team_row["team_name"]

        self.team_url = f"https://www.dotabuff.com/{team_link}/matches?date=all"
        if "6074306" in team_link:
            self.team_url = "https://www.dotabuff.com/esports/teams/6074306/matches?date=all&original_slug=6074306-vbet&page=3"
        self.team_id = team_row["team_id"]
        self.session = requests.session()
        self.team_name = None
        if forced_url is not None:
            self.team_url = forced_url

        #response = requests.get("https://free-proxy-list.net/")
        #df = pd.read_html(response.text)[0]
        #proxy = df["IP Address"].sample().iat[0]
        #self.proxies = {'http': proxy,'https': proxy}

    def parse_matches_webpage(self, web_page, soup):
        visible_data = pd.read_html(web_page)[0]

        parsed_table = soup.find_all('table')[0]
        # copypasted from SO...
        data = [[td.a['href'] if td.find('a') else
                 ''.join(td.stripped_strings)
                 for td in row.find_all('td')]
                for row in parsed_table.find_all('tr')]
        link_data = pd.DataFrame(data[1:])
        link_data.drop([3, 4], axis=1, inplace=True)
        link_data.rename(
            {0: "tournament_link", 1: "match_link", 2: "series_link",
             5: "oponent_link"}, axis=1, inplace=True)
        return pd.concat([visible_data, link_data], axis=1)

    def get_team_name(self, soup):
        self.team_name = soup.find("h1").contents[0]

    def handle_new_teams(self, unique_teamlinks):
        current_db_teams = pd.read_sql_table("teams", engine)

        max_id = max(current_db_teams["team_id"])
        teams_in_db = set(current_db_teams["team_name"])
        non_processed_teams = unique_teamlinks - teams_in_db
        lal = {}
        for index,team in enumerate(non_processed_teams):
            lal[team] = max_id + index + 1

        df = pd.DataFrame.from_dict(lal, orient="index").reset_index()
        df.rename({"index":"team_name", 0:"team_id"}, axis=1, inplace=True)
        df["scraped"] = False
        df.to_sql("teams", engine, if_exists="append",
                 index=False)
    def mark_success(self):

        conn = psycopg2.connect(db_url)
        cursor = conn.cursor()
        cursor.execute(f"UPDATE public.teams SET scraped='true' WHERE team_id = '{self.team_id}';")
        conn.commit()

    def go(self):
        url = self.team_url

        while True:
            time.sleep(random.randint(2, 7))

            response = self.session.get(url, headers={"User-Agent": agent})#, proxies=self.proxies)
            print(f"processing url {url}")


            try:
                assert response.status_code == 200, response
                soup = bs.BeautifulSoup(response.text, 'html5lib')
                df = self.parse_matches_webpage(response.text, soup)
                if self.team_name is None:
                    self.get_team_name(soup=soup)
                df["team_name"] = self.team_name
                #drops column with teamname as header and no data
                df.drop(df.columns[4], axis=1, inplace=True)
                df.to_sql("dota_matches", engine, if_exists="append",
                          index=False)
                next = soup.find("span", {"class": "next"})

                if not next:
                    break
                next_url =next.find("a")
                url = BASE_URL + next_url.get("href")
                unique_teams_to_scrape = set(df["oponent_link"].unique())
                self.handle_new_teams(unique_teams_to_scrape)
            except Exception as e:
                print(f"Last  url failed: {url} time: {time.strftime('%Y-%m-%d %H:%M')}" )
                traceback.print_exc()
                exit()
        self.mark_success()



if __name__ == "__main__":
    import bs4 as bs
    # old scrape
    def get_matches():
        all_teams = pd.read_sql_table("teams", engine)
        all_matches = pd.read_sql_table("dota_matches", engine)

        #vole mas to spatne. muzu skrapovat klidne neco vickrat :D protoze mam set tady, ne nad celym datasetem
        queued_teams = all_teams.loc[all_teams["scraped"] == False, :]
        #force_url =  "https://www.dotabuff.com/esports/teams/46/matches?date=all&original_slug=46-team-empire&page=52 "
        for i,(index, row) in enumerate(queued_teams.iterrows()):
            if row["team_name"] == "Unknown":
                continue
            # asi jsem skipnul Team Empire -->set false
            ts = TeamScraper(row, all_teams)
            ts.go()


    def parse_matches_webpage(web_page, soup):
        visible_data = pd.read_html(web_page)[0]

        parsed_table = soup.find_all('table')[0]
        # copypasted from SO...
        data = [[td.a['href'] if td.find('a') else
                 ''.join(td.stripped_strings)
                 for td in row.find_all('td')]
                for row in parsed_table.find_all('tr')]
        link_data = pd.DataFrame(data[1:])
        link_data.drop([3, 4], axis=1, inplace=True)
        link_data.rename(
            {0: "tournament_link", 1: "match_link", 2: "series_link",
             5: "oponent_link"}, axis=1, inplace=True)
        return pd.concat([visible_data, link_data], axis=1)

    # vezme pouze nove esport matche
    def update_matches():
        page_num = 1
        from scrape.scrape_helpers import Sess

        while True:

            time.sleep(random.randint(2, 7))
            url = f"https://www.dotabuff.com/esports/matches?page={page_num}"
            print(url)
            resp = Sess().get(url)

            soup = bs.BeautifulSoup(resp.text, 'html5lib')
            df = parse_matches_webpage(resp.text, soup)
            df.drop(df.columns[4], axis=1, inplace=True)
            df = df[['tournament_link', 'match_link', 'series_link', 'oponent_link',  'Duration', 'Series']]
            df.to_sql("dota_matches", engine, if_exists="append",
                      index=False)

            page_num += 1
            if page_num >= 50:
                break





    update_matches()
















