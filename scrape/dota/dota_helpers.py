import random
import pandas as pd
#which fucking should'nt been necessary :D
def update_team_and_match_db_return_t_id(link, name, cursor, conn):
    if link is None:
        return random.randint(100000, 500000)

    cursor.execute(f"SELECT team_id,team_name FROM teams WHERE team_link = '{link}'")
    try:
        id, team_name = cursor.fetchone()
    except:
        id = random.randint(100000, 500000)

    try:
        if not team_name:
            cursor.execute(
                f"UPDATE teams SET team_name = '{name}' WHERE team_link = '{link}'")

        cursor.execute(
            f"SELECT team_id FROM dota_matches WHERE team_name = '{name}'")


        t_m_id = cursor.fetchone()[0]
        if not t_m_id:
            cursor.execute( f"UPDATE dota_matches SET team_id = {id} WHERE team_name = '{name}'")
    except:
        pass
    #cursor.fetch(all)
    conn.commit()
    return id

def pandify_basic_match_info(basic_dict):
    # flatten nested dicts
    output = {}
    for key, value in basic_dict.items():
        if type(value) == dict:
            trol = {f"{key}_{k}": v for k, v in basic_dict[key].items()}

            output = {**output, **trol}
        else:
            output={**output,**{key:basic_dict[key]}}
    df = pd.DataFrame.from_dict(output, orient="index").T
    df["Match Ended_datetime"] = pd.to_datetime(df["Match Ended_datetime"])
    return df