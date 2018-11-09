import requests
import pandas as pd
import bs4 as bs
import time
import random
import re
from sqlalchemy import create_engine
import psycopg2


pd.set_option('display.width', 1000)
pd.set_option('display.max_columns', 50)

db_url = "postgres://postgres:Darthpic0@localhost/dota"



conn = psycopg2.connect(db_url)
cursor = conn.cursor()
cursor.execute("SELECT distinct oponent_link FROM dota_matches")
links = cursor.fetchall()

for index, tupl in enumerate(links):
    id = index+2
    team_link = tupl[0]

    cursor.execute(f"INSERT INTO public.teams(team_id, team_name, scraped)VALUES ({id}, '{team_link}', false  );")
conn.commit()
print()