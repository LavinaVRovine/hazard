import pandas as pd
import click
from decisions.csgo_decider import CSGODecider
from decisions.dota_decider import DotaDecider
from decisions.lol_decider import LoLDecider
from helpers.helpers import *
from config import logging, DATABASE_URI, DB_MAPPINGS, IMPLEMENTED_BOOKIES, DEBUG
from predictions.lol_predictor import LoLPredictor
from predictions.dota_predictor import DotaPredictor
from predictions.csgo_predictor import CSGOPredictor
from csgo_db_loader.get_csgo_data import get_csgo_data
from bookie_monitors.ifortuna_cz import IfortunaCz  # needed, dont remove

pd.set_option("display.width", 1000)
pd.set_option("display.max_columns", 50)

# script's purpose is to predict who ll win e-sport game and
# suggest action and amount to bet
# WIP currently


def create_predictor(game):
    if game == "LoL":
        return LoLPredictor()
    elif game == "Dota":
        return DotaPredictor()
    elif game == "CS:GO":

        return CSGOPredictor(get_csgo_data())
    else:
        logging.critical(f"Not implemented game: {game}")
        raise NotImplementedError


def create_decider(game, row, db_location):
    if game == "LoL":
        return LoLDecider(row, db_location)
    elif game == "Dota":
        return DotaDecider(row, db_location)
    elif game == "CS:GO":
        return CSGODecider(row, db_location)
    else:
        raise NotImplementedError


def get_bookie_stats(bookie, game, game_url):
    global_vars = globals()
    assert bookie in global_vars, f"Cant instantialize " f"class for bookie {bookie}"
    monitor = global_vars[bookie](
        bookie, game_name=game, logger=logging, game_url=game_url
    )
    # goes to bookie page and downloads new stats etc.
    monitor.get_bookie_info()
    if monitor.matches is None:
        print(f"No games are being played for {game} on {bookie}")
        return
    # if monitor.stats_updated:
    #     monitor.store_matches()
    return monitor.get_biding_info()


def process_matches(bookie_stats, game: str, db_location, predictor) -> list:
    output_data = list()
    for index, row in bookie_stats.iterrows():
        decision_maker = create_decider(game, row, db_location)
        output_data.append(
            dict(
                decision_maker.decide_match_action(predictor),
                **{"date": row["datum"]},
            )
        )
    return output_data


def main(game):
    logging.info(f"Started script for game: {game}")
    print(f"Started script for game: {game}")
    db_location = DATABASE_URI + DB_MAPPINGS[game]
    predictor = create_predictor(game)
    bookies = IMPLEMENTED_BOOKIES[game]
    for bookie, game_url in bookies.items():
        bookie_stats = get_bookie_stats(bookie, game, game_url)
        if bookie_stats is None:
            continue
        output_data = process_matches(bookie_stats, game, db_location, predictor)

        if DEBUG:
            print(reformat_output_mail(output_data), game)
        else:
            send_mail(reformat_output_mail(output_data), game, bookie)


@click.command()
@click.option(
    "--compare_odds",
    "-co",
    default=["all"],
    help="Which game(s) to compare",
    type=click.Choice(["all", "lol", "dota", "csgo"]),
    multiple=True,
    show_default=True,
)
def compare_odds(**kwargs):

    if "game_name" in kwargs:
        games = kwargs["game_name"]
    else:
        games = ["all"]

    if "all" in games:
        main("LoL")
        main("Dota")
        main("CS:GO")
    else:
        for game in games:

            for key, value in DB_MAPPINGS.items():
                if value == game:
                    main(key)


if __name__ == "__main__":
    compare_odds()
