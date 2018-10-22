import logging

DATABASE_URI = "postgres://user:password@localhost/"
IMPLEMENTED_BOOKIES = {"LoL": ["ifortuna"]}
DB_MAPPINGS = {"LoL": "lol"}
GOOGLE_PW = "helloworld"
LOG_LVL = logging.WARN
DEBUG = True
GMAIL_USER_MAIL = "user@gmail.com"

logging.basicConfig(filename='run_log.log', filemode='a', format='%(asctime)s %(name)s - %(levelname)s - %(message)s',level=LOG_LVL)


