import requests
import pandas as pd
import bs4 as bs
import traceback
from sqlalchemy import create_engine
import psycopg2
from helpers.helpers import parse_number
from scrape.scrape_helpers import Sess
from scrape.csgo.csgo_match import CSGOMatch
from config import DATABASE_URI

pd.set_option('display.width', 1000)
pd.set_option('display.max_columns', 50)

BASE_URL = "https://www.hltv.org"
DB_URL = f"{DATABASE_URI}csgo"
ENGINE = create_engine(DB_URL)
# TODO map name je s nejakym shit znakem


def get_current_scrape_pages():
    return pd.read_sql_table("scrape_urls", con=ENGINE)


class Found(Exception):
    pass


class Blocked(Exception):
    """Uve been blocked!"""
    pass


def get_new_matches_since_last_run():
    """
    Loops until it finds url, which is already scraped.
    Results on page are sorted by date.
    Appends new result urls for scraping into Database.
    :return: True
    """
    current_links = set(get_current_scrape_pages()["link"].unique())
    offset = 0
    urls = set()
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:65.0) Gecko/20100101 Firefox/65.0',
    }
    with requests.session() as session:
        print("Started looking for new CSGO results")
        while True:
            try:
                results_url = f"{BASE_URL}/results?offset={offset}"
                results_soup =\
                    bs.BeautifulSoup(session.get(results_url, headers=headers).text, "html5lib")

                if results_soup.find("h1", {"data-translate": "block_headline"}) is not None:
                    raise Blocked

                for match in results_soup.find_all("div",
                                                   {"class": "result-con"}):
                    match_url = match.find("a").get("href")
                    if match_url in current_links:
                        raise Found("found")
                    urls.add(match_url)

                offset += 100
                if offset % 1000 == 0:
                    print(f"successfully run {offset}")
            except Found:
                pd.DataFrame(list(urls), columns=["link"]).to_sql(
                    "scrape_urls", con=ENGINE, index=False, if_exists='append')
                print(f"Updated urls for CS:GO scraping by {len(urls)}.")
                return True
    return False


if __name__ == "__main__":
    get_new_matches_since_last_run()

    conn = psycopg2.connect(DB_URL)
    cursor = conn.cursor()
    scrape_urls = get_current_scrape_pages()
    pending_urls = scrape_urls[(scrape_urls["scraped"] != False) &
                               (scrape_urls["scraped"] != True)]
    c = Sess()

    for index, row in pending_urls.iterrows():
        link = row["link"]
        url = BASE_URL + link
        site_match_id = int(parse_number(url))
        print(f"Processing: {url}")
        soup = bs.BeautifulSoup(c.get(url).text, "html5lib")
        if url == "https://www.hltv.org/matches/2297915/night-raid-vs-kappakappa-dreamhack-open-cluj-napoca-2015-eu-pre-qualifier-2" or url == "https://www.hltv.org/matches/2330407/ut-austin-vs-kennesaw-state-university-java-collegiate-2":
            continue
        try:
            cs_match = CSGOMatch(soup, c)
        except Exception:
            print("failed init -> no stats")
            cursor.execute(
               f"UPDATE scrape_urls SET scraped = FALSE WHERE link='{link}'")
            conn.commit()
            continue

        games = cs_match.get_games_info()
        if len(games) == 0:
            print("found no games on the page, skipping for now")
            continue

        match_info = pd.Series(cs_match.parse_base_info())
        match_info["match_id"] = site_match_id
        # this is gay
        match_info = pd.DataFrame(match_info).T
        games_df = pd.DataFrame(
            columns=["map_name", "game_id", "match_id", "nth_match"]
        )
        game_teams_df = pd.DataFrame(
            columns=["game_id", "team_id", "name", "winner", "score"]
        )
        players_stats_df = None

        for game_index, game in enumerate(games):
            game_n_in_match = game_index + 1
            games_df = games_df.append({
                "map_name": game.map_name, "game_id": game.site_game_id,
                "match_id": site_match_id, "nth_match": game_n_in_match},
                ignore_index=True
            )

            for t in[game.t1, game.t2]:
                team_repr = t.__dict__

                player_stats = team_repr.pop("player_stats")
                team_id = team_repr["team_id"]

                team_repr["game_id"] = game.site_game_id
                team_repr["team_id"] = team_id
                team_repr["nth_game"] = game_n_in_match
                team_repr["game_team_id"] =\
                    f"{game.site_game_id}:{team_id}:{game_n_in_match}"
                game_teams_df =\
                    game_teams_df.append(team_repr, ignore_index=True)

                player_stats["game_id"] = game.site_game_id
                player_stats["team_id"] = team_id
                player_stats["nth_game"] = game_n_in_match
                player_stats["game_team_id"] = \
                    f"{game.site_game_id}:{team_id}:{game_n_in_match}"
                player_stats = player_stats.rename(columns={"K-D Diff": "K/D Diff"})
                if players_stats_df is None:
                    players_stats_df = player_stats
                else:
                    players_stats_df = players_stats_df.append(player_stats)

        try:
            players_stats_df.to_sql("players_stats", con=ENGINE, index=False,
                                    if_exists="append")
            match_info.to_sql("matches", con=ENGINE, index=False,
                              if_exists="append")
            games_df.to_sql("games", con=ENGINE, index=False,
                            if_exists="append")
            game_teams_df.to_sql("games_teams", con=ENGINE, index=False,
                                 if_exists="append")

            cursor.execute(
                f"UPDATE scrape_urls SET scraped = TRUE WHERE link='{link}'")
            conn.commit()
        except Exception:
            traceback.print_exc()
            #exit()
