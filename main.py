import pandas as pd
import traceback
from bookie_monitors.ifortuna_cz import IfortunaCz
from bookie_monitors.chance_cz import ChanceCz
from decider import Decider, DotaDecider
from LOL_formatter import Formatter
from helpers.helpers import *
from config import *
from predictions.lol_predictor import LoLPredictor
from predictions.dota_predictor import DotaPredictor

pd.set_option('display.width', 1000)
pd.set_option('display.max_columns', 50)

# script's purpose is to predict who ll win e-sport game and
# suggest action and amount to bet
# WIP currently

# TODO: refatoring, chance - static file, and find out, why i dont get same chances for fnatic against cloud9 :D

def decide_match_action(row, predictor, db_location):
    decision_maker = Decider(row, db_location)
    try:
        match_row = decision_maker.create_match_stats_row()
    except ValueError:
        return {"team1": row['team1'], "team2": row['team2']}
    formatter = Formatter(match_row)
    try:
        formatted_row = formatter.main_reformat()
        bookie_match_row =\
            formatter.drop_useless_columns(formatted_row, type="main")

        preds = predictor.predict_one_match(bookie_match_row)
        # now does basically nothing :)
        decision = decision_maker.compare_ods(preds[True])

        output =\
            {"team1": row['team1'], "team2": row['team2'],
             "preds":preds, "decision": decision}

        print(
            f"prediction for {row['team1']} againt competitor {row['team2']}"
            f" are {preds}   {decision}")
        return output
    except:
        print(
            f"something went wrong for  {row['team1']} againt"
            f" competitor {row['team2']}")
        traceback.print_exc()
        return {"team1": row['team1'], "team2": row['team2']}


def main(game):
    logging.info(f"Started script for game: {game}")
    db_location = DATABASE_URI + DB_MAPPINGS[game]
    if game == "LoL":
        predictor = LoLPredictor()
    elif game == "Dota":
        predictor = DotaPredictor()
    else:
        logging.critical(f"Not implemented game: {game}")
        raise NotImplemented
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
                data.append(decide_match_action(row, predictor, db_location))
            elif game == "Dota":

                decision_maker = DotaDecider(row, db_location)

                try:
                    match_row = decision_maker.create_match_stats_row()
                    match_row = match_row[predictor.training_columns]
                    preds = predictor.predict_one_match(match_row)
                    decision = decision_maker.compare_ods(preds[True])

                    output = \
                        {"team1": row['team1'], "team2": row['team2'],
                         "preds": preds, "decision": decision}

                    print(
                        f"prediction for {row['team1']} againt competitor {row['team2']}"
                        f" are {preds}   {decision}")
                    data.append(output)
                except:
                    print(
                        f"something went wrong for  {row['team1']} againt"
                        f" competitor {row['team2']}")
                    traceback.print_exc()
                    data.append( {"team1": row['team1'], "team2": row['team2']})
                print()

        if DEBUG:
            print(reformat_output_mail(data), game)
        else:
            send_mail(reformat_output_mail(data), game, bookie)


if __name__ == "__main__":
    print("rolling lol")
    main("LoL")
    print("rolling dota")
    main("Dota")