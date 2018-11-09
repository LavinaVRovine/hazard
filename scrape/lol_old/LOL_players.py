"""import requests
odpoved = requests.get('https://github.com')
odpoved.raise_for_status()
print(odpoved.text)"""

# written by Digital Academy's Lenka Skalická&Petra Sučková

import requests
import pandas as pd
from sqlalchemy import create_engine
import time
engine = create_engine('postgresql://postgres:Czechitas@localhost:5432/Projekt data')
#print(engine)
df = pd.read_sql_table("player_teams", engine)
urls = list(df["player_url"])
#print(f"delka urls {len(urls)} delka neunikatni {len(list(df['player_url']))}")


#print(urls)
BASE_URL = "http://gol.gg"
#print(BASE_URL + urls[0])
for index,row in df.iterrows():
	try:
		url = row["player_url"]
		player_id = row["player_id"]
		real_url = BASE_URL + url
		#print(real_url)
		headers = {'user-agent': 'my-app/0.0.2'}
		r = requests.get(real_url, headers=headers)
		# jsem moc vidět, ale teď to nevadí
		assert r.status_code == 200, "chybicka"
		#print(r.status_code)
		nev = pd.read_html(r.text)
		#print(nev[2].T)
		zaklady_statistiky = nev[2].T
		zaklady_statistiky.columns = zaklady_statistiky.iloc[0]
		zaklady_statistiky = zaklady_statistiky.reindex(zaklady_statistiky.index.drop(0))
		#print(zaklady_statistiky)
		try:
			zaklady_statistiky["KDA:"] = pd.to_numeric(zaklady_statistiky["KDA:"])
		except:
			zaklady_statistiky["KDA:"] = 0
		#pro všechny to try udělat
		zaklady_statistiky["CS per Minute:"] = pd.to_numeric(zaklady_statistiky["CS per Minute:"])
		zaklady_statistiky["Gold Per Minute:"] = pd.to_numeric(zaklady_statistiky["Gold Per Minute:"])
		zaklady_statistiky.rename({"Gold%:":"Gold"}, axis=1, inplace=True)
		#smažeme %
		zaklady_statistiky["Gold"] = zaklady_statistiky["Gold"].str.replace("%", "")
		zaklady_statistiky["Gold"] = pd.to_numeric(zaklady_statistiky["Gold"])

		zaklady_statistiky["Win Rate:"] = zaklady_statistiky["Win Rate:"].str.replace("%", "")
		zaklady_statistiky["Win Rate:"] = pd.to_numeric(zaklady_statistiky["Win Rate:"])

		zaklady_statistiky["Kill Participation:"] = zaklady_statistiky["Kill Participation:"].str.replace("%", "")
		zaklady_statistiky["Kill Participation:"] = pd.to_numeric(zaklady_statistiky["Kill Participation:"])

		zaklady_statistiky.fillna("ah", inplace = True)

		zaklady_statistiky["player_id"] = player_id

		#print(zaklady_statistiky.columns)
		#zaklady_statistiky.to_csv("players.csv", mode = "a")
		
		#zaklady_statistiky = zaklady_statistiky.fillna
		zaklady_statistiky.to_sql("players_statistics", engine, if_exists = "append", index = False)
		time.sleep(1)
		if index % 50 == 0:
			print(f"jedeme {index}")

	except:
		print(f"hups {url}")
