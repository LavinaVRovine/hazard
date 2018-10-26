import logging

DATABASE_URI = "postgres://user:password@localhost/"
IMPLEMENTED_BOOKIES = {"LoL": {"IfortunaCz": "https://www.ifortuna.cz/cz/sazeni/progaming", "ChanceCz":"https://www.chance.cz/kurzy/e-sporty-188" }}
DB_MAPPINGS = {"LoL": "lol"}
GOOGLE_PW = "helloworld"
LOG_LVL = logging.WARN
DEBUG = True
GMAIL_USER_MAIL = "user@gmail.com"

logging.basicConfig(filename='run_log.log', filemode='a', format='%(asctime)s %(name)s - %(levelname)s - %(message)s',level=LOG_LVL)


