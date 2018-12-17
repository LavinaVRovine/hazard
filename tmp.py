

from sqlalchemy import create_engine
import pandas as pd

engine = create_engine("postgres://postgres:Darthpic0@localhost/beed_mall",
                           echo=False)


mssql_engine = create_engine("mssql+pyodbc://sa:Darthpic0@PAVEL-DELL\\SQLEXPRESS/beed_mall?driver=SQL Server",
                           echo=False, pool_pre_ping=True)




file_path = "D:/Downloads/mall.cz_heureka.cz_2017-01-01-2017-12-31.csv"

for chunk in pd.read_csv(file_path, chunksize=1000000, low_memory=False):

    df = chunk[['date', 'portal_uniq_id', 'item_id', 'segment', 'category',
       'manufacturer', 'feed_category', 'feed_tag', 'feed_manufacturer',
       'name', 'my_price', 'portal_url', 'popularity', 'median_position',
       'bidding_position', 'organic_position', 'stock', 'delivery_date',
       'condition_id', 'condition_name',
       'stats.sessions',
       'stats.cost', 'stats.portal.transactions', 'stats.portal.revenue',
       'stats.portal.conversion_rate', 'stats.portal.cos',
       'stats.ga.transactions', 'stats.ga.revenue', 'stats.ga.conversion_rate',
       'stats.ga.cos', 'bid', 'biddable', 'shop_count',  'top', 'condition_noop', 'condition_check',
       'feed_bid', 'profit_margin', 'stats.heureka_conversion_report.sessions',
       'stats.heureka_conversion_report.cost',
       'stats.heureka_conversion_report.transactions',
       'stats.heureka_conversion_report.revenue']]
    df = df.loc[df["date"] != "date"]

    df["my_price"] = pd.to_numeric(df["my_price"],errors="coerce")
    df["popularity"] = pd.to_numeric(df["popularity"], errors="coerce")
    df["median_position"] = pd.to_numeric(df["median_position"], errors="coerce")
    df["bidding_position"] = pd.to_numeric(df["bidding_position"],
                                          errors="coerce")
    df["organic_position"] = pd.to_numeric(df["organic_position"],
                                          errors="coerce")
    df["condition_id"] = pd.to_numeric(df["condition_id"],
                                           errors="coerce")

    for col in df.columns:
        if col.startswith("stats") or col.endswith("position"):
            df[col] = pd.to_numeric(col, errors="coerce")
    df["bid"] = pd.to_numeric(df["bid"],
                                       errors="coerce")
    df["popularity"] = pd.to_numeric(df["popularity"],
                                       errors="coerce")
    df["condition_id"] = pd.to_numeric(df["condition_id"],
                                     errors="coerce")
    df["bid"] = pd.to_numeric(df["bid"],
                                       errors="coerce")
    df["shop_count"] = pd.to_numeric(df["shop_count"],
                              errors="coerce")

    df["top"] = pd.to_numeric(df["top"],
                                     errors="coerce")
    df["condition_noop"] = pd.to_numeric(df["condition_noop"],
                              errors="coerce")
    df["condition_check"] = pd.to_numeric(df["condition_check"],
                                         errors="coerce")
    df["feed_bid"] = pd.to_numeric(df["feed_bid"],
                                          errors="coerce")
    df["profit_margin"] = pd.to_numeric(df["profit_margin"],
                                   errors="coerce")
    df["biddable"] = df.biddable.astype('bool')
    df["stock"] = df.biddable.astype('bool')
    df["date"] = pd.to_datetime(df["date"],
                                          errors="coerce")
    df["delivery_date"] = pd.to_numeric(df["delivery_date"],
                                          errors="coerce")
    df.to_sql("data", con=engine, index=False, if_exists="append")
    #df.to_sql("data", con=mssql_engine, index=False, if_exists="append")
    print("And another one")









