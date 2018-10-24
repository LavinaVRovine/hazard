import pandas as pd
from bookie_monitors.ifortuna_cz import IfortunaCz
from decider import Decider
from ml_predictions import My_predictor
from LOL_formatter import Formatter
from helpers.helpers import *
pd.set_option('display.width', 1000)
pd.set_option('display.max_columns', 50)
from config import *


def handle_match(row, predictor, db_location):
    decision_maker = Decider(row, db_location)
    match_row = decision_maker.create_match_stats_row()
    formatter = Formatter(match_row)
    try:
        x = formatter.main_reformat()
        bookie_match_row = formatter.drop_useless_columns(x, type="main")

        preds = predictor.predict_one_match(bookie_match_row)
        # now does basically nothing :)
        decision = decision_maker.compare_ods(preds[True])

        output = {"team1": row['team1'], "team2": row['team2'], "preds":preds, "decision":
            decision}

        print(
            f"prediction for {row['team1']} againt competitor {row['team2']} are {preds}   {decision}")
        return output
    except:

        print(
            f"something went wrong for  {row['team1']} againt competitor {row['team2']}")
        return {"team1": row['team1'], "team2": row['team2']}


def main(game):
    logging.info(f"Started script for game: {game}")
    db_location = DATABASE_URI + DB_MAPPINGS[game]
    if game == "LoL":
        predictor = My_predictor(db_location=db_location)
    else:
        logging.critical(f"Not implemented game: {game}")
        raise NotImplemented

    bookies = IMPLEMENTED_BOOKIES[game]
    for bookie, game_url in bookies.items():
        #monitor = Monitor(bookie, game_name=game, logger=logging, db_location=db_location, game_url=game_url)
        monitor = IfortunaCz(bookie, game_name=game, logger=logging,
                             db_location=db_location, game_url=game_url)
        monitor.get_bookie_info()
        basic_info = monitor.get_biding_info()
        data = list()
        for index, row in basic_info.iterrows():
            data.append(handle_match(row, predictor, db_location))

        if DEBUG:
            print(reformat_output_mail(data), game)
        else:
            send_mail(reformat_output_mail(data), game)


if __name__ == "__main__":
    print("rolling")

    main("LoL")