import pandas as pd
from sqlalchemy import create_engine
from config import DATABASE_URI
from helpers.custom_exceptions import NoMatchData

DB_URL = f"{DATABASE_URI}csgo"
ENGINE = create_engine(DB_URL)


pd.set_option("display.width", 1000)
pd.set_option("display.max_columns", 50)


ug_sql = """select t1_winner, team_1_id, team_2_id
from matches
"""

winrate_against_each_other_sql = """SELECT u.team_1_id, u.team_2_id, sum(t1_winner::int) wins_against_each_other,
 count(team_1_id) games_against_each_other, (sum(t1_winner::int)::float/count(team_1_id)) as winrate_against_each_other
from matches as u
where team_1_id is not null or team_2_id is not null
group by team_1_id, team_2_id

"""

# TODO potrebuji IDcka na dotaz, ale v training byt nemaji + na fejko


def get_teams_stats(team_id: int = None) -> pd.DataFrame:
    base_team_stats_sql = """SELECT 
          ps.team_id,
          Avg(ps."K/D Diff")                          kddiffs,
          Avg(ps."FK Diff")                           fkdiff,
          ( Sum(ps."K") + Sum(ps."A") ) / Sum(ps."D") AS my_rate,
          Sum(ps."HS") / ( Sum(ps."K") )              hs_rate,
          Avg(COALESCE(ps.rating2, ps.rating1))       AS page_rating
   FROM   players_stats ps
   join games g on g.game_id = ps.game_id
   GROUP BY ps.team_id;"""

    if not team_id:
        return pd.read_sql(base_team_stats_sql, con=ENGINE)
    else:
        return pd.read_sql(
            """SELECT 
          ps.team_id,
          Avg(ps."K/D Diff")                          kddiffs,
          Avg(ps."FK Diff")                           fkdiff,
          ( Sum(ps."K") + Sum(ps."A") ) / Sum(ps."D") AS my_rate,
          Sum(ps."HS") / ( Sum(ps."K") )              hs_rate,
          Avg(COALESCE(ps.rating2, ps.rating1))       AS page_rating
   FROM   players_stats ps
   join games g on g.game_id = ps.game_id
   WHERE ps.team_id = %(t_id)s
   GROUP BY ps.team_id;""",
            con=ENGINE,
            params={"t_id": team_id},
        )


def get_teams_winrate(team_id: int = None) -> pd.DataFrame:
    base_winrate_stats_sql = """SELECT u.team_id team_id, sum(u.is_winner::int) wins, count(u.team_id) games,
 (sum(u.is_winner::int)::float/count(u.team_id)) as winrate

from
(select t1_winner is_winner, team_1_id team_id from matches where team_1_id is not null 
union all
select t2_winner is_winner, team_2_id team_id from matches where team_2_id is not null ) as u
group by u.team_id
order by games desc"""

    if not team_id:
        return pd.read_sql(base_winrate_stats_sql, con=ENGINE)
    else:
        return pd.read_sql(
            """SELECT u.team_id team_id, sum(u.is_winner::int) wins, count(u.team_id) games,
 (sum(u.is_winner::int)::float/count(u.team_id)) as winrate

from
(select t1_winner is_winner, team_1_id team_id from matches where team_1_id is not null 
union all
select t2_winner is_winner, team_2_id team_id from matches where team_2_id is not null ) as u
where team_id = %(t_id)s
group by u.team_id
order by games desc""",
            con=ENGINE,
            params={"t_id": team_id},
        )


class ColumnRenamer:
    """
    small helper to rename duplicate columns
    """

    def __init__(self):
        self.d = dict()

    def __call__(self, x):
        if x not in self.d:
            self.d[x] = 0
            return x
        else:
            self.d[x] += 1
            return "%s_%d" % (x, self.d[x])


def get_csgo_data():
    team_stats = get_teams_stats()
    team_winrate = get_teams_winrate()
    matches = pd.read_sql(ug_sql, con=ENGINE)
    against_each_other_df = pd.read_sql(winrate_against_each_other_sql, con=ENGINE)

    df_with_winrates = matches.merge(
        team_winrate, left_on="team_1_id", right_on="team_id"
    ).merge(
        team_winrate, left_on="team_2_id", right_on="team_id", suffixes=("_n", "_c")
    )
    df_with_winrates_stats = df_with_winrates.merge(
        team_stats, left_on="team_1_id", right_on="team_id"
    ).merge(team_stats, left_on="team_2_id", right_on="team_id", suffixes=("_n", "_c"))
    df_with_winrates_stats_aeo_stats = df_with_winrates_stats.merge(
        against_each_other_df,
        left_on=["team_1_id", "team_2_id"],
        right_on=["team_1_id", "team_2_id"],
        suffixes=("", "AEO"),
    )

    df_with_winrates_stats_aeo_stats = df_with_winrates_stats_aeo_stats.rename(
        columns=ColumnRenamer()
    )
    df_with_winrates_stats = df_with_winrates_stats.rename(columns=ColumnRenamer())

    # doing this because in preds teams might not yet have faced each other, therefore ll be missing AEO stats
    return df_with_winrates_stats_aeo_stats.append(
        df_with_winrates_stats, sort=False
    ).sample(frac=0.75)


def data_if_not_played_before(main_team_id, competitor_id) -> pd.Series:
    """

    :param main_team_id:
    :param competitor_id:
    :return:
    :raises if cant find any data. no idea how it happens actually. Raises NoMatchData exc.
    """
    team_stats = get_teams_stats()
    team_winrate = get_teams_winrate()

    df_with_winrates = team_stats.merge(
        team_winrate, left_on="team_id", right_on="team_id"
    )
    t1_r = df_with_winrates.loc[df_with_winrates["team_id"] == main_team_id].add_suffix(
        "_n"
    )
    t2_r = df_with_winrates.loc[
        df_with_winrates["team_id"] == competitor_id
    ].add_suffix("_c")

    if len(t1_r) == 0:
        raise NoMatchData(f"failed to find data for id {main_team_id}")
    if len(t2_r) == 0:
        raise NoMatchData(f"failed to find data for id {competitor_id}")

    whole_row = pd.concat(
        [t1_r.reset_index(drop=True), t2_r.reset_index(drop=True)],
        axis=1,
        ignore_index=False,
    )

    return whole_row.iloc[0]


def remove_id_cols(df: pd.DataFrame) -> pd.DataFrame:
    return df.loc[:, [c for c in df.columns if "_id" not in c]]


if __name__ == "__main__":
    data_if_not_played_before(4411, 4555)
    print()
    df = get_csgo_data()
    print()
