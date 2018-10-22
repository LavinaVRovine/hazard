import pandas as pd
from monitor import Monitor
import logging
from decider import Decider
from ml_predictions import My_predictor
from LOL_formatter import Formatter
from helpers.custom_exceptions import *
from tabulate import tabulate
pd.set_option('display.width', 1000)
pd.set_option('display.max_columns', 50)
from config import *

def send_mail(message, game):
    import smtplib
    from email.mime.multipart import MIMEMultipart
    from email.mime.text import MIMEText
    # SMTP_SSL Example
    server_ssl = smtplib.SMTP_SSL("smtp.gmail.com", 465)
    server_ssl.ehlo()  # optional, called by login()
    server_ssl.login(GMAIL_USER_MAIL, GOOGLE_PW)

    msg = MIMEMultipart('alternative')
    msg['subject'] = f"Update on hazard for game: {game}"
    msg['To'] = GMAIL_USER_MAIL
    msg['From'] = GMAIL_USER_MAIL
    msg.preamble = """
    Your mail reader does not support the report format.
    Please visit us <a href="http://www.mysite.com">online</a>!"""
    html = """
        <html>
        <head>
        <style> 
          table, th, td {{ border: 1px solid black; border-collapse: collapse; }}
          th, td {{ padding: 5px; }}
        </style>
        </head>
        <body><p>Hello, Friend.</p>
        <p>Here is your data:</p>
        {table}
        <p>Regards,</p>
        <p>Me</p>
        </body></html>
        """
    message = html.format(table=tabulate(message, headers="firstrow", tablefmt="html"))
    msg.attach(MIMEText(message, 'html'))

    server_ssl.sendmail(GMAIL_USER_MAIL, GMAIL_USER_MAIL,  msg.as_string())
    server_ssl.close()
    print('successfully sent the mail')
    return True

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

def reformat_output_mail(results):
    #TODO: use tabulate instead
    output = []
    headers = []
    for match in results:
        for key in match.keys():
            if key not in headers:
                headers.append(key)
    output.append(headers)
    for match in results:
        lala = []
        for header in headers:
            if header in match:
                lala.append(match[header])
            else:
                lala.append(" ")
        output.append(lala)
    return output


def main(game):
    logging.info(f"Started script for game: {game}")
    db_location = DATABASE_URI + DB_MAPPINGS[game]
    if game == "LoL":
        predictor = My_predictor(db_location=db_location)
    else:
        logging.critical(f"Not implemented game: {game}")
        raise NotImplemented

    bookies = IMPLEMENTED_BOOKIES[game]
    for bookie in bookies:
        monitor = Monitor(bookie, game_name=game, logger=logging, db_location=db_location)
        if DEBUG == False:
            monitor.get_actual_bookie_info()
        basic_info = monitor.get_biding_info()
        data = list()
        for index, row in basic_info.iterrows():
            data.append(handle_match(row, predictor, db_location))


        send_mail(reformat_output_mail(data), game)




if __name__ == "__main__":
    print("rolling")

    main("LoL")