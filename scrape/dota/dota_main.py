import pandas as pd
import bs4 as bs
from sqlalchemy import create_engine
import psycopg2
from scrape.dota.dota_match_scraper import DotaMatch
from scrape.dota.dota_helpers import update_team_and_match_db_return_t_id, pandify_basic_match_info
from scrape.scrape_helpers import Sess
from config import DATABASE_URI
pd.set_option('display.width', 1000)
pd.set_option('display.max_columns', 50)

BASE_URL = "https://www.dotabuff.com"
DB_URL = f"{DATABASE_URI}dota"
conn = psycopg2.connect(DB_URL)
cursor = conn.cursor()
ENGINE = create_engine(DB_URL)


def get_max_match_id():
    cursor.execute(
        f"SELECT max(match_id) FROM matches ")
    return cursor.fetchone()[0]


# loads nonscraped matches from db and scrapes them
def scrape_pending_matches():

    pending_matches = pd.read_sql_table("dota_matches", ENGINE)
    pending_matches =\
        pending_matches.loc[pending_matches["scraped_page"] == False, :]

    max_match_id = get_max_match_id()
    c = Sess()

    for i, (index, row) in enumerate(pending_matches.iterrows()):
        print(i)
        link = row["match_link"]
        row_id = row["row_id"]
        # skip already parsed matches might have been in multiple times
        if link in list(pd.read_sql_table("matches", con=ENGINE)[
                            "match_link"].unique()):
            cursor.execute(
                f"UPDATE dota_matches SET scraped_page ="
                f" {True} WHERE row_id = {row_id}"
            )
            conn.commit()

            continue

        print(BASE_URL + link)
        resp = c.get(BASE_URL + link)
        if resp is False:
            print("Failed scraped")
            cursor.execute(
                f"UPDATE dota_matches SET "
                f"scraped_page = NULL WHERE row_id = {row_id}"
            )
            conn.commit()
            continue
        assert resp.status_code == 200,\
            f"Failed {link} with code {resp.status_code}"

        try:
            match = DotaMatch(bs.BeautifulSoup(resp.text, "html5lib"))
        except ValueError:
            print("failed match init")
            continue

        match_overview = pandify_basic_match_info(match.basic_match_info)
        try:
            # dis is horribuble
            # actually dont know what it does :D
            t1_id =\
                update_team_and_match_db_return_t_id(match.t1["link"],
                                                     match.t1["name"],
                                                     cursor, conn)

            t2_id = \
                update_team_and_match_db_return_t_id(match.t2["link"],
                                                     match.t2["name"],
                                                     cursor, conn)

            match_overview["t1_id"] = t1_id
            match_overview["t2_id"] = t2_id
            match_overview["t1_name"] = match.t1["name"]
            match_overview["t2_name"] = match.t2["name"]
            match_overview["t1_winner"] = match.t1["winner"]
            match_overview["t2_winner"] = match.t2["winner"]
            match_overview["t1_link"] = match.t1["link"]
            match_overview["t2_link"] = match.t2["link"]
            match_overview["match_link"] = link
            match_id = max_match_id + i + 1
            match_overview["match_id"] = match_id

            t1_stats = match.t1["stats"]
            t1_stats["match_id"] = match_id
            t1_stats["team_id"] = t1_id

            t2_stats = match.t2["stats"]
            t2_stats["match_id"] = match_id
            t2_stats["team_id"] = t2_id

            match_overview.to_sql("matches",
                                  con=ENGINE, index=False, if_exists='append')
            t1_stats.to_sql("stats", con=ENGINE, index=False,
                            if_exists='append')
            t2_stats.to_sql("stats", con=ENGINE, index=False,
                            if_exists='append')

            cursor.execute(
                f"UPDATE dota_matches SET scraped_page ="
                f" {True} WHERE row_id = {row_id}"
            )
            conn.commit()
            print("successfull update")
        except Exception:
            cursor.execute(
                f"UPDATE dota_matches SET scraped_page ="
                f" NULL WHERE row_id = {row_id}"
            )
            conn.commit()

            print("failed update")


if __name__ == "__main__":
    scrape_pending_matches()
