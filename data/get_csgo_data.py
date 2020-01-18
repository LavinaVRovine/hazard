import pandas as pd
from sqlalchemy import create_engine
from config import DATABASE_URI

DB_URL = f"{DATABASE_URI}csgo"
ENGINE = create_engine(DB_URL)


pd.set_option("display.width", 1000)
pd.set_option("display.max_columns", 50)


team_stats_sql = """SELECT 
       ps.team_id,
       Avg(ps."K/D Diff")                          kddiffs,
       Avg(ps."FK Diff")                           fkdiff,
       ( Sum(ps."K") + Sum(ps."A") ) / Sum(ps."D") AS my_rate,
       Sum(ps."HS") / ( Sum(ps."K") )              hs_rate,
       Avg(COALESCE(ps.rating2, ps.rating1))       AS page_rating
FROM   players_stats ps
join games g on g.game_id = ps.game_id
GROUP BY ps.team_id;"""

team_winrate_sql = """SELECT u.team_id team_id, sum(u.is_winner::int) wins, count(u.team_id) games,
 (sum(u.is_winner::int)::float/count(u.team_id)) as winrate

from
(select t1_winner is_winner, team_1_id team_id from matches where team_1_id is not null 
union all
select t2_winner is_winner, team_2_id team_id from matches where team_2_id is not null ) as u
group by u.team_id
order by games desc"""


ug_sql = """select t1_winner, team_1_id, team_2_id
from matches
"""

winrate_against_each_other_sql = """SELECT u.team_1_id, u.team_2_id, sum(t1_winner::int) wins_against_each_other,
 count(team_1_id) games_against_each_other, (sum(t1_winner::int)::float/count(team_1_id)) as winrate_against_each_other
from matches as u
where team_1_id is not null or team_2_id is not null
group by team_1_id, team_2_id

"""


def get_csgo_data():
    team_stats = pd.read_sql(team_stats_sql, con=ENGINE)
    team_winrate = pd.read_sql(team_winrate_sql, con=ENGINE)
    matches = pd.read_sql(ug_sql, con=ENGINE)
    against_each_other_df = pd.read_sql(winrate_against_each_other_sql, con=ENGINE)

    df = matches.merge(team_winrate, left_on="team_1_id", right_on="team_id").merge(
        team_winrate, left_on="team_2_id", right_on="team_id", suffixes=("_n", "_c")
    )
    df = df.merge(team_stats, left_on="team_1_id", right_on="team_id").merge(
        team_stats, left_on="team_2_id", right_on="team_id", suffixes=("_n", "_c")
    )
    df = df.merge(
        against_each_other_df,
        left_on=["team_1_id", "team_2_id"],
        right_on=["team_1_id", "team_2_id"],
        suffixes=("", "AEO"),
    )
    return df


def get_csgo_data_no_ids():
    df = get_csgo_data()
    return df.copy().drop([c for c in df.columns if "_id" in c], axis=1).dropna()


if __name__ == "__main__":
    get_csgo_data()
