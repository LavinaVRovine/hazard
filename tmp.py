import pandas as pd
from sqlalchemy import create_engine
from config import DATABASE_URI

con = create_engine(DATABASE_URI + "lol", echo=False)

print(pd.read_sql("""$$select Dianne's horse$$""", con=con))