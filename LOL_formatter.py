import re
from decimal import Decimal


class Formatter:
    def __init__(self, df):
        self.df = df

    @staticmethod
    def parse_numbers(win_to_lose):
        regex = re.compile("(\d+)")
        found_numbers = regex.findall(win_to_lose)

        assert len(found_numbers) == 2
        return found_numbers

    @staticmethod
    def get_winrate(win_to_lose):
        found_numbers = Formatter.parse_numbers(win_to_lose)
        return int(found_numbers[0]) / Formatter.get_n_games(win_to_lose)

    @staticmethod
    def get_n_games(win_to_lose):
        found_numbers = Formatter.parse_numbers(win_to_lose)
        return sum(Decimal(i) for i in found_numbers)

    @staticmethod
    def parse_x_slash_game(x_slash_game):
        if x_slash_game is None or x_slash_game == []:
            return (None, None)
        regex = re.compile("(\d+.?\d*?)\s\((\d+.?\d*?)%\)")
        parsed_values = regex.findall(x_slash_game)

        assert len(parsed_values[0]) == 2, x_slash_game
        parsed_values = parsed_values[0]
        return float(parsed_values[0]), float(parsed_values[1])

    def main_reformat(self):
        df = self.df
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

        return df

    def drop_useless_columns(self, df, type):
        if type == "predict":
            return self.drop_for_predict(df)
        elif type == "main":
            return self.drop_for_main(df)
        else:
            raise Exception

    def drop_for_predict(self, df):
        df = df.copy()
        df.drop(["win_to_lose", "season", "region", "c_match_url", "c_season",
                 "c_region", "match_url", "ffs", "dragon_game", "herald_game",
                 "nashors_game",
                 "c_dragon_game", "c_herald_game", "c_nashors_game",
                 "c_win_to_lose"], axis=1, inplace=True)
        #df.drop(["name", "c_name"], axis=1, inplace=True)
        return df

    def drop_for_main(self, df):
        df = df.copy()
        df.drop(["win_to_lose", "season", "region", "c_season",
                 "c_region",  "dragon_game", "herald_game",
                 "nashors_game",
                 "c_dragon_game", "c_herald_game", "c_nashors_game",
                 "c_win_to_lose"], axis=1, inplace=True)
        df.drop(["name", "c_name", "team_id", "c_team_id"],
                axis=1, inplace=True)
        return df
