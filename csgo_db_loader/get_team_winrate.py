import pandas as pd

from csgo_db_loader.my_globals import ENGINE

pd.set_option('display.width', 1000)
pd.set_option('display.max_columns', 50)


def get_team_winrate() -> pd.DataFrame:
    """
    :return:
    """
    return pd.read_sql("""(
         SELECT round(100.0 * (sum(
                CASE
                    WHEN games_teams_1.winner = true THEN 1
                    ELSE 0
                END)::numeric / count(games_1.game_id)::numeric), 1) AS win_pct,
            count(games_1.game_id) AS games_count,
            games_teams_1.team_id
           FROM games games_1
             JOIN matches matches_1 ON matches_1.match_id = games_1.match_id
             JOIN games_teams games_teams_1 ON games_1.game_id = games_teams_1.game_id
          GROUP BY games_teams_1.team_id
          ORDER BY (count(games_1.game_id)) DESC
        )""", con=ENGINE)