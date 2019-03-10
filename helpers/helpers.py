from tabulate import tabulate
from config import GMAIL_USER_MAIL, GOOGLE_PW
import re


def parse_number(string:str)->int:
    return int(re.compile("/(\d+)/").findall(string)[0])


def send_mail(message, game, bookie):
    import smtplib
    from email.mime.multipart import MIMEMultipart
    from email.mime.text import MIMEText
    # SMTP_SSL Example
    server_ssl = smtplib.SMTP_SSL("smtp.gmail.com", 465)
    server_ssl.ehlo()  # optional, called by login()
    server_ssl.login(GMAIL_USER_MAIL, GOOGLE_PW)

    msg = MIMEMultipart('alternative')
    msg['subject'] = f"Update on hazard for game: {game} - {bookie}"
    msg['To'] = GMAIL_USER_MAIL + ", jan.kudelka91@gmail.com"
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
    message = html.format(table=tabulate(
        message, headers="firstrow", tablefmt="html"
    ))
    msg.attach(MIMEText(message, 'html'))

    server_ssl.sendmail(GMAIL_USER_MAIL, GMAIL_USER_MAIL,  msg.as_string())
    server_ssl.close()
    print('successfully sent the mail')
    return True


def reformat_output_mail(results):
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
