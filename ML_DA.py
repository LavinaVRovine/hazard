from config import DATABASE_URI
import pandas as pd
from sklearn import preprocessing
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from sqlalchemy import create_engine
from LOL_formatter import Formatter
from sklearn.externals import joblib
pd.set_option('display.width', 1000)
pd.set_option('display.max_columns', 50)


db_url = f"{DATABASE_URI}lol"

def load_train_df(db_location):
    engine = create_engine(db_location,
                           echo=False)
    return pd.read_sql("SELECT * FROM basic_predictions", engine)


def format_train_df(train_dataset):
    formatter = Formatter(train_dataset)
    df = formatter.main_reformat()
    df = formatter.drop_for_predict(df)
    return df


df = load_train_df(db_url)
df = format_train_df(df)

df.loc[(df["name"] == "100 Thieves") & (df["c_name"] == "Invictus Gaming")]

print()
print()