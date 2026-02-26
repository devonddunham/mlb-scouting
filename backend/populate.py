import sqlite3
import pandas as pd
from pybaseball import statcast_batter, statcast_pitcher, playerid_lookup, batting_stats, pitching_stats

def get_connection():
    return sqlite3.connect('mlb_scouting.db')

def populate_scouts():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("INSERT OR IGNORE INTO Scout (name, region, teamID) VALUES ('Devon Dunham', 'Southeast', 'TBR')")
    conn.commit()
    conn.close()

def populate_teams():
    conn = get_connection()
    cursor = conn.cursor()

    teams = [
        ('TBR', 'Tampa Bay Rays', 'AL East'),
        ('NYY', 'New York Yankees', 'AL East'),
        ('BOS', 'Boston Red Sox', 'AL East'),
        ('TOR', 'Toronto Blue Jays', 'AL East'),
        ('BAL', 'Baltimore Orioles', 'AL East'),
        ('LAD', 'Los Angeles Dodgers', 'NL West'),
        ('SFG', 'San Francisco Giants', 'NL West'),
        ('SDP', 'San Diego Padres', 'NL West'),
        ('ARI', 'Arizona Diamondbacks', 'NL West'),
        ('COL', 'Colorado Rockies', 'NL West'),
        ('NYM', 'New York Mets', 'NL East'),
        ('PHI', 'Philadelphia Phillies', 'NL East'),
        ('ATL', 'Atlanta Braves', 'NL East'),
        ('MIA', 'Miami Marlins', 'NL East'),
        ('WSN', 'Washington Nationals', 'NL East'),
        ('CHC', 'Chicago Cubs', 'NL Central'),
        ('STL', 'St. Louis Cardinals', 'NL Central'),
        ('CIN', 'Cincinnati Reds', 'NL Central'),
        ('PIT', 'Pittsburgh Pirates', 'NL Central'),
        ('MIL', 'Milwaukee Brewers', 'NL Central'),
        ('CLE', 'Cleveland Guardians', 'AL Central'),
        ('CWS', 'Chicago White Sox', 'AL Central'),
        ('MIN', 'Minnesota Twins', 'AL Central'),
        ('DET', 'Detroit Tigers', 'AL Central'),
        ('KCR', 'Kansas City Royals', 'AL Central'),
        ('HOU', 'Houston Astros', 'AL West'),
        ('OAK', 'Oakland Athletics', 'AL West'),
        ('LAA', 'Los Angeles Angels', 'AL West'),
        ('SEA', 'Seattle Mariners', 'AL West'),
        ('TEX', 'Texas Rangers', 'AL West')
    ]

    cursor.executemany("INSERT OR IGNORE INTO Team (teamID, name, division) VALUES (?, ?, ?)", teams)
    conn.commit()
    conn.close()

def populate_whole_team(team_abbr, season=2025):
    print(f"Populating data for {team_abbr} in season {season}...")
    
    # get lists of hitters and pitchers for the season
    h_list = batting_stats(season)
    p_list = pitching_stats(season)

    # filter for the specific team
    team_hitters = h_list[h_list['Team'] == team_abbr]
    team_pitchers = p_list[p_list['Team'] == team_abbr]

    conn = get_connection()
    cursor = conn.cursor()

    # populate hitters
    for _, row in team_hitters.iterrows():
        name_parts = row['Name'].split()
        first, last = name_parts[0], " ".join(name_parts[1:])
        
        # find the player id
        ids = playerid_lookup(last, first)
        if ids.empty: continue
        
        mlbam_id = int(ids['key_mlbam'].values[0])
        bbref_id = ids['key_bbref'].values[0] # this is from the lahman db, havent added yet

        # get advanced metrics from statcast for the last month
        raw_data = statcast_batter('2025-05-01', '2025-06-01', mlbam_id)
        avg_ev = raw_data['launch_speed'].mean() if not raw_data.empty else 0
        avg_la = raw_data['launch_angle'].mean() if not raw_data.empty else 0

        # insert Player
        cursor.execute('''INSERT OR IGNORE INTO Player (playerID, mlbamID, nameFirst, nameLast, teamID, primaryPosition)
                          VALUES (?, ?, ?, ?, ?, 'Hitter')''', 
                       (bbref_id, mlbam_id, first, last, team_abbr))

        # insert Scouting Report
        # right now all reports are done by same scout (id=1) and have a default overall grade of 50
        # later for advanced function we create our own grade
        cursor.execute('''INSERT INTO ScoutingReport (playerID, scoutID, date, playerType, exit_velocity, launch_angle, overall_grade)
                          VALUES (?, 1, date('now'), 'Hitter', ?, ?, 50)''', 
                       (bbref_id, round(float(avg_ev), 2), round(float(avg_la), 2)))

    # add pitchers
    for _, row in team_pitchers.iterrows():
        name_parts = row['Name'].split()
        first, last = name_parts[0], " ".join(name_parts[1:])
        
        ids = playerid_lookup(last, first)
        if ids.empty: continue
        
        mlbam_id = int(ids['key_mlbam'].values[0])
        bbref_id = ids['key_bbref'].values[0] # this is from the lahman db, havent added yet

        # get advanced metrics from statcast for the last month
        raw_data = statcast_pitcher('2025-05-01', '2025-06-01', mlbam_id)
        avg_velo = raw_data['release_speed'].mean() if not raw_data.empty else 0
        avg_spin = raw_data['release_spin_rate'].mean() if not raw_data.empty else 0

        cursor.execute('''INSERT OR IGNORE INTO Player (playerID, mlbamID, nameFirst, nameLast, teamID, primaryPosition)
                          VALUES (?, ?, ?, ?, ?, 'Pitcher')''', 
                       (bbref_id, mlbam_id, first, last, team_abbr))

        cursor.execute('''INSERT INTO ScoutingReport (playerID, scoutID, date, playerType, pitch_velocity, spin_rate, overall_grade)
                          VALUES (?, 1, date('now'), 'Pitcher', ?, ?, 50)''', 
                       (bbref_id, round(float(avg_velo), 2), round(float(avg_spin), 2)))

    conn.commit()
    conn.close()
    print(f"Added players for {team_abbr}.")

if __name__ == "__main__":
    populate_teams()
    populate_scouts()
    populate_whole_team('LAD')