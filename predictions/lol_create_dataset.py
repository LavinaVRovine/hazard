import pandas as pd
from sqlalchemy import create_engine
from config import DATABASE_URI

pd.set_option("display.width", 1000)
pd.set_option("display.max_columns", 50)

DB_URL = f"{DATABASE_URI}lol"
ENGINE = create_engine(DB_URL)


def create_lol_dataset():
    dropcols = [
        "match_url",
        "ffs",
        "name",
        "c_match_url",
        "c_ffs",
        "c_name",
    ]
    df = pd.read_sql_table("averaged_predictions", con=ENGINE)

    df["main_team_against_comp_winrate"] = df.apply(
        lambda x: calculate_team_against_comp_winrate(x, df), axis=1
    )
    joined = join_with_old(df)

    float_cols = list(joined.select_dtypes(include=["float64"]).columns)
    return joined.loc[:, float_cols], joined.main_team_won_x, joined


def calculate_team_against_comp_winrate(row, data_df):
    df_slice = data_df.loc[
        ((data_df["name"] == row["name"]) & (data_df["c_name"] == row["c_name"]))
    ]
    return df_slice.main_team_won.mean()


def handle_the_old_way():
    old_df = pd.read_sql_table("basic_predictions", con=ENGINE)

    # old_cols = ["gold_per_minute", "gold_differential_per_minute",
    #             "gold_differential_at_15", "cs_per_minute",
    #             "cs_differential_at_15", "tower_differential_at_15",
    #             "tower_ratio", "damage_per_minute", "first_blood",
    #             "kills_per_game", "deaths_per_game", "kda", "dragons_15",
    #             "wards_per_minute", "wards_cleared_per_minute",
    #             "pct_wards_cleared", "c_gold_per_minute",
    #             "c_gold_differential_per_minute", "c_gold_differential_at_15",
    #             "c_cs_per_minute", "c_cs_differential_at_15",
    #             "c_tower_differential_at_15", "c_tower_ratio",
    #             "c_damage_per_minute", "c_first_blood", "c_kills_per_game",
    #             "c_deaths_per_game", "c_kda", "c_dragons_15",
    #             "c_wards_per_minute", "c_wards_cleared_per_minute",
    #             "c_pct_wards_cleared", "win_rate", "c_win_rate", "n_games",
    #             "c_n_games", "dragon_game_value", "dragon_game_pct",
    #             "herald_game_value", "herald_game_pct", "nashors_game_value",
    #             "nashors_game_pct", "c_dragon_game_value", "c_dragon_game_pct",
    #             "c_herald_game_value", "c_herald_game_pct",
    #             "c_nashors_game_value", "c_nashors_game_pct"]
    # old_cols.append("ffs")
    from formatter import Formatter

    df = old_df
    df["win_rate"] = df["win_to_lose"].apply(Formatter.get_winrate)
    df["c_win_rate"] = df["c_win_to_lose"].apply(Formatter.get_winrate)
    df["n_games"] = df["win_to_lose"].apply(Formatter.get_n_games)
    df["c_n_games"] = df["c_win_to_lose"].apply(Formatter.get_n_games)
    df["dragon_game"] = df["dragon_game"].apply(Formatter.parse_x_slash_game)
    df["dragon_game_value"] = df["dragon_game"].str[0]
    df["dragon_game_pct"] = df["dragon_game"].str[1]

    df["herald_game"] = df["herald_game"].apply(Formatter.parse_x_slash_game)
    df["herald_game_value"] = df["herald_game"].str[0]
    df["herald_game_pct"] = df["herald_game"].str[1]

    df["nashors_game"] = df["nashors_game"].apply(Formatter.parse_x_slash_game)
    df["nashors_game_value"] = df["nashors_game"].str[0]
    df["nashors_game_pct"] = df["nashors_game"].str[1]

    df["c_dragon_game"] = df["c_dragon_game"].apply(Formatter.parse_x_slash_game)
    df["c_dragon_game_value"] = df["c_dragon_game"].str[0]
    df["c_dragon_game_pct"] = df["c_dragon_game"].str[1]

    df["c_herald_game"] = df["c_herald_game"].apply(Formatter.parse_x_slash_game)
    df["c_herald_game_value"] = df["c_herald_game"].str[0]
    df["c_herald_game_pct"] = df["c_herald_game"].str[1]

    df["c_nashors_game"] = df["c_nashors_game"].apply(Formatter.parse_x_slash_game)
    df["c_nashors_game_value"] = df["c_nashors_game"].str[0]
    df["c_nashors_game_pct"] = df["c_nashors_game"].str[1]
    df["main_team_against_comp_winrate"] = df.apply(
        lambda x: calculate_team_against_comp_winrate(x, df), axis=1
    )
    # old_cols.append("main_team_against_comp_winrate")
    return df


def join_with_old(data):
    old_df = handle_the_old_way()
    new_df = data
    lol_df = pd.merge(
        old_df, new_df, left_on=["match_url", "name"], right_on=["match_url", "name"]
    )
    lol_df = lol_df.fillna(0)
    return lol_df


if __name__ == '__main__':
    x = handle_the_old_way()
    print()