import pandas as pd
from csgo_db_loader.get_one_game_team_stats import get_summarize_player_stats_to_team


df = pd.read_sql("SELECT match_id, t1_winner from csgo.public.matches join games_teams on matches.match_id = games_teams.m")

exit()
team_game_stats = get_summarize_player_stats_to_team()

"""
 WITH something AS (
         SELECT games.index,
            games.map_name,
            games.game_id,
            games.match_id,
            games.nth_match,
            matches.index,
            matches.unix_time,
            matches.formatted_date,
            matches.tournament_link,
            matches.t1_name,
            matches.t1_winner,
            matches.t1_won_n_matches,
            matches.t2_name,
            matches.t2_winner,
            matches.t2_won_n_matches,
            matches.match_id,
            games_teams.index,
            games_teams.game_id,
            games_teams.team_id,
            games_teams.name,
            games_teams.winner,
            games_teams.score,
            games_teams.game_team_id,
            games_teams.nth_game,
            games.match_id AS something_match_id,
            date_part('year'::text, matches.unix_time) AS winrate_year
           FROM games
             JOIN matches ON matches.match_id = games.match_id
             JOIN games_teams ON games.game_id = games_teams.game_id
        ), something_else AS (
         SELECT games.index,
            games.map_name,
            games.game_id,
            games.match_id,
            games.nth_match,
            matches.index,
            matches.unix_time,
            matches.formatted_date,
            matches.tournament_link,
            matches.t1_name,
            matches.t1_winner,
            matches.t1_won_n_matches,
            matches.t2_name,
            matches.t2_winner,
            matches.t2_won_n_matches,
            matches.match_id,
            games_teams.index,
            games_teams.game_id,
            games_teams.team_id,
            games_teams.name,
            games_teams.winner,
            games_teams.score,
            games_teams.game_team_id,
            games_teams.nth_game,
            games.match_id AS something_else_match_id,
            date_part('year'::text, matches.unix_time) AS winrate_year
           FROM games
             JOIN matches ON matches.match_id = games.match_id
             JOIN games_teams ON games.game_id = games_teams.game_id
        )
 SELECT something.team_id,
    something_else.team_id AS c_team_id,
    something.winrate_year,
    something.t1_winner,
    something.something_match_id
   FROM something something(index, map_name, game_id, match_id, nth_match, index_1, unix_time, formatted_date, tournament_link, t1_name, t1_winner, t1_won_n_matches, t2_name, t2_winner, t2_won_n_matches, match_id_1, index_2, game_id_1, team_id, name, winner, score, game_team_id, nth_game, something_match_id, winrate_year)
     JOIN something_else something_else(index, map_name, game_id, match_id, nth_match, index_1, unix_time, formatted_date, tournament_link, t1_name, t1_winner, t1_won_n_matches, t2_name, t2_winner, t2_won_n_matches, match_id_1, index_2, game_id_1, team_id, name, winner, score, game_team_id, nth_game, something_else_match_id, winrate_year) ON something.something_match_id = something_else.something_else_match_id AND something.game_team_id <> something_else.game_team_id;"""