import pandas as pd

from csgo_db_loader.my_globals import ENGINE

pd.set_option("display.width", 1000)
pd.set_option("display.max_columns", 50)


def get_summarize_player_stats_to_team() -> pd.DataFrame:
    """
    just summarizes players perf into teams
    :return:
    """
    return pd.read_sql(
        """(
         SELECT sum(players_stats."A") AS a,
            sum(players_stats."D") AS d,
            avg(players_stats."KAST") AS kast,
            avg(players_stats."K/D Diff") AS kd_diff,
            sum(players_stats."FK Diff") AS fk_diff,
            sum(players_stats."K") AS k,
            sum(players_stats."HS") AS hs,
            players_stats.game_id,
            players_stats.team_id,
            avg(
                CASE
                    WHEN players_stats.rating2 IS NOT NULL THEN players_stats.rating2
                    WHEN players_stats.rating1 IS NOT NULL THEN players_stats.rating1
                    ELSE NULL::double precision
                END) AS ratings
           FROM players_stats
          GROUP BY players_stats.game_id, players_stats.team_id
        )""",
        con=ENGINE,
    )
