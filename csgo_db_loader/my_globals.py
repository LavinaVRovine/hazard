from sqlalchemy import create_engine
from config import DATABASE_URI
DB_URL = f"{DATABASE_URI}csgo"
ENGINE = create_engine(DB_URL)


tables = dict(
    games="seznam mapa, game id, match id",
    games_teams="game id, team id, team name, winner, score - je tady tedy vlastne jen, zdali je tram GAME winner (+name...)",
    matches="match id, kdo vyhral, teamy, ktere se ucastnily a dalsi info o matchich.",
    players_stats="hracske statistkiku pro game id, with teams"
)