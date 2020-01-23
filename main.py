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
from bookie_monitors.ifortuna_cz import IfortunaCz
from data.csgo_data_creator import CSGOData
from data.lol_data_creator import LOLData
from data.dota_data_creator import DOTAData

pd.set_option("display.width", 1000)
pd.set_option("display.max_columns", 50)


def create_predictor(game):
    if game == "lol":
        return LoLPredictor()
    elif game == "dota":
        return DotaPredictor()
    elif game == "csgo":
        return CSGOPredictor()
    else:
        logging.critical(f"Not implemented game: {game}")
        raise NotImplementedError


def create_decider(game, bookie_match_row, db_location):
    if game == "lol":
        data_handler = LOLData()
        return LoLDecider(bookie_match_row, db_location, data_handler)
    elif game == "dota":
        data_handler = DOTAData()
        return DotaDecider(bookie_match_row, db_location, data_handler)
    elif game == "csgo":
        data_handler = CSGOData()
        return CSGODecider(bookie_match_row, db_location, data_handler)
    else:
        raise NotImplementedError


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

    bookies = [
        IfortunaCz(game_name=game, logger=logging, game_url=IMPLEMENTED_BOOKIES[game]["IfortunaCz"])
    ]
    for bookie in bookies:
        bookie.get_bookie_info()
        if bookie.matches is None:
            print(f"No games are being played for {game} on {bookie}")
            continue
        # if monitor.stats_updated:
        #     monitor.store_matches()
        bookie_stats = bookie.get_biding_info()

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
        main("lol")
        main("dota")
        main("csgo")
    else:
        for game in games:

            for key, value in DB_MAPPINGS.items():
                if value == game:
                    main(key)


if __name__ == "__main__":
    compare_odds()
