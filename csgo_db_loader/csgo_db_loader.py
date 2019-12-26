import pandas as pd
from sqlalchemy import create_engine
from config import DATABASE_URI

pd.set_option('display.width', 1000)
pd.set_option('display.max_columns', 50)
DB_URL = f"{DATABASE_URI}csgo"
ENGINE = create_engine(DB_URL)


print()
print()
team_stats_filtered_sql = """ WITH stats AS (
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
        ), winrate AS (
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
        )
 SELECT avg(stats.a) AS a,
    avg(stats.d) AS d,
    avg(stats.kast) AS kast,
    avg(stats.kd_diff) AS kd_diff,
    avg(stats.fk_diff) AS fk_diff,
    avg(stats.k) AS k,
    avg(stats.hs) AS hs,
    avg(stats.ratings) AS ratings,
    max(winrate.win_pct) AS max_winrate,
    stats.team_id,
    max(winrate.games_count) AS game_count
   FROM games_teams
     JOIN stats ON stats.game_id = games_teams.game_id AND stats.team_id = games_teams.team_id
     JOIN games ON games.game_id = games_teams.game_id
     JOIN matches ON games.match_id = matches.match_id
     JOIN winrate ON winrate.team_id = stats.team_id
  GROUP BY stats.team_id;"""




stats_sql = """
 SELECT matches_winner.t1_id,
    matches_winner.t2_id,
    matches_winner.t1_winner,
    tsf.a,
    tsf.d,
    tsf.kast,
    tsf.kd_diff,
    tsf.fk_diff,
    tsf.k,
    tsf.hs,
    tsf.ratings,
    tsf.max_winrate,
    tsf2.a AS c_a,
    tsf2.d AS c_d,
    tsf2.kast AS c_kast,
    tsf2.kd_diff AS c_kd_diff,
    tsf2.fk_diff AS c_fk_diff,
    tsf2.k AS c_k,
    tsf2.hs AS c_hs,
    tsf2.ratings AS c_ratings,
    tsf2.max_winrate AS c_max_winrate
   FROM matches_winner
     JOIN team_stats_filtered tsf ON matches_winner.t1_id = tsf.team_id
     JOIN team_stats_filtered tsf2 ON matches_winner.t2_id = tsf2.team_id;"""

df = pd.read_sql_table('stats', con=ENGINE)
df = df.dropna()
