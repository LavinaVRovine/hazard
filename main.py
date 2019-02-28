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
from bookie_monitors.ifortuna_cz import IfortunaCz # needed, dont remove
pd.set_option('display.width', 1000)
pd.set_option('display.max_columns', 50)

# script's purpose is to predict who ll win e-sport game and
# suggest action and amount to bet
# WIP currently

# TODO: refatoring, chance - static file, and find out, why i dont get same chances for fnatic against cloud9 :D
def main(game):
    logging.info(f"Started script for game: {game}")
    print(f"Started script for game: {game}")
    db_location = DATABASE_URI + DB_MAPPINGS[game]
    if game == "LoL":
        predictor = LoLPredictor()
    elif game == "Dota":
        predictor = DotaPredictor()
    elif game == "CS:GO":
        predictor = CSGOPredictor()
    else:
        logging.critical(f"Not implemented game: {game}")
        raise NotImplementedError
    global_vars = globals()
    bookies = IMPLEMENTED_BOOKIES[game]
    for bookie, game_url in bookies.items():

        assert bookie in global_vars, f"Cant instantialize class for bookie {bookie}"
        # inits bookie class
        monitor = global_vars[bookie](bookie, game_name=game, logger=logging,
                                 game_url=game_url)
        # goes to bookie page and downloads new stats etc.
        monitor.get_bookie_info()
        if monitor.matches is None:
            print(f"No games are being played for {game} on {bookie}")
            continue
        # if monitor.stats_updated:
        #     monitor.store_matches()
        basic_info = monitor.get_biding_info()
        data = list()
        # for each match basically decide what to do
        for index, row in basic_info.iterrows():
            if game == "LoL":
                decision_maker = LoLDecider(row, db_location)
            elif game == "Dota" :
                decision_maker = DotaDecider(row, db_location)
            elif game == "CS:GO":
                decision_maker = CSGODecider(row, db_location)
            else:
                raise NotImplementedError
            data.append(decision_maker.decide_match_action(row, predictor))
        if DEBUG:
            print(reformat_output_mail(data), game)
        else:
            send_mail(reformat_output_mail(data), game, bookie)


@click.command()

@click.option('--compare_odds','-co', default=['all'],
              help='Which game(s) to compare',
              type=click.Choice(["all", "lol", "dota", "csgo"]),
              multiple=True, show_default=True)
def compare_odds(**kwargs):

    if 'game_name' in kwargs:
        games = kwargs['game_name']
    else:
        games = ["all"]

    # if "csgo" in games:
    #     raise Exception ("csgo currently turned off, because it sucks")
    if "all" in games:
        main("LoL")
        main("Dota")
        main("CS:GO")
    else:
        for game in games:

            for key, value in DB_MAPPINGS.items():
                if value == game:
                    main(key)


if __name__ == '__main__':
    compare_odds()
