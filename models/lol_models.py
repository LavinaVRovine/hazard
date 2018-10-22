
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, Float, ForeignKey, Table, MetaData, Boolean
from sqlalchemy import create_engine
from sqlalchemy_utils import database_exists, create_database
from sqlalchemy.orm import relationship
from config import DB_MAPPINGS, DATABASE_URI
engine = create_engine(DATABASE_URI + DB_MAPPINGS["LoL"],
                           echo=False)
if not database_exists(engine.url):
    create_database(engine.url)
Base = declarative_base()
class Team(Base):

    __tablename__ = "teams"
    # nutno tedy vytvorit dalsi tabulku se seasnama?

    ['Region', 'Season', 'Win Rate', 'Average game duration', 'Team Name',
     'Gold Per Minute', 'Gold Differential per Minute',
     'Gold Differential at 15 min', 'CS Per Minute',
     'CS Differential at 15 min', 'Tower Differential at 15 min',
     'Tower Ratio', 'First Tower', 'Damage Per Minute', 'First Blood',
     'Kills Per Game', 'Deaths Per Game', 'Kill / Death Ratio',
     'Average Assists / Kill', 'Dragons / game', 'Dragons at 15 min',
     'Herald / game', 'Nashors / game', 'Wards Per Minute',
     'Vision Wards Per Minute', 'Wards Cleared Per Minute', '% Wards Cleared']


    team_id = Column(Integer,primary_key=True)
    name = Column(String)
    season = Column(String)
    region = Column(String)
    win_to_lose = Column(String)
    average_game_duration = Column(String)
    gold_per_minute = Column(Float)
    gold_differential_per_minute = Column(Float)
    gold_differential_at_15 = Column(Float)
    cs_per_minute = Column(Float)
    cs_differential_at_15 = Column(Float)
    tower_differential_at_15 = Column(Float)
    tower_ratio = Column(Float)
    first_tower = Column(Float)
    damage_per_minute = Column(Float)
    first_blood = Column(Float)
    kills_per_game = Column(Float)
    deaths_per_game = Column(Float)
    kda = Column(Float)
    dragon_game = Column(String)
    dragons_15= Column(Float)
    herald_game = Column(String)
    nashors_game = Column(String)
    wards_per_minute = Column(Float)
    vision_wards_per_minute = Column(Float)
    wards_cleared_per_minute = Column(Float)
    pct_wards_cleared = Column(Float)

    player_teams = relationship("Player_team")#, back_populates="parent")
    matches = relationship("Team_match")#, back_populates="parent")

class Player_team(Base):
    __tablename__ = "player_teams"
    player_id = Column(Integer, primary_key=True)
    team_id = Column(Integer, ForeignKey("teams.team_id"))
    player_name = Column(String)
    player_url = Column(String)

    teams = relationship("Team")

class Team_match(Base):

    __tablename__ = "team_matches"
    match_id = Column(Integer, primary_key=True)
    team_id = Column(Integer, ForeignKey("teams.team_id"))
    match_title = Column(String)
    match_url = Column(String)
    teams = relationship("Team")

class Game_result(Base):

    __tablename__ = "game_results"

    real_match_id =  Column(Integer, primary_key=True)
    match_id = Column(Integer, ForeignKey("team_matches.match_id"))
    main_team_id = Column(Integer)
    competitor_team_id = Column(Integer)
    score = Column(String)
    main_team_won = Column(Boolean)

def upgrade(migrate_engine):
    meta = MetaData(bind=migrate_engine)
    teams = Table('teams', meta, autoload=True)
    teams.c.id.alter(name='team_id')


#upgrade(engine)
Base.metadata.create_all(engine)