import pandas as pd

from bookie_monitors.ifortuna_cz import IfortunaCz
from bookie_monitors.chance_cz import ChanceCz
from decider import Decider
from ml_predictions import My_predictor
from LOL_formatter import Formatter
from helpers.helpers import *
from config import *

pd.set_option('display.width', 1000)
pd.set_option('display.max_columns', 50)

# script's purpose is to predict who ll win e-sport game and
# suggest action and amount to bet
# WIP currently

# TODO: refatoring, chance - static file, and find out, why i dont get same chances for fnatic against cloud9 :D

def decide_match_action(row, predictor, db_location):
    decision_maker = Decider(row, db_location)
    match_row = decision_maker.create_match_stats_row()
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
        return {"team1": row['team1'], "team2": row['team2']}


def main(game):
    logging.info(f"Started script for game: {game}")
    db_location = DATABASE_URI + DB_MAPPINGS[game]
    if game == "LoL":
        predictor = My_predictor(db_location=db_location)
    else:
        logging.critical(f"Not implemented game: {game}")
        raise NotImplemented
    global_vars = globals()
    bookies = IMPLEMENTED_BOOKIES[game]
    for bookie, game_url in bookies.items():

        assert bookie in global_vars, f"Cant instantialize class for bookie {bookie}"
        monitor = global_vars[bookie](bookie, game_name=game, logger=logging,
                                 game_url=game_url)

        monitor.get_bookie_info()
        # if monitor.stats_updated:
        #     monitor.store_matches()
        basic_info = monitor.get_biding_info()
        data = list()
        for index, row in basic_info.iterrows():
            data.append(decide_match_action(row, predictor, db_location))

        if DEBUG:
            print(reformat_output_mail(data), game)
        else:
            send_mail(reformat_output_mail(data), game)


if __name__ == "__main__":
    print("rolling")
    main("LoL")