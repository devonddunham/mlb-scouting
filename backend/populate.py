import pandas as pd
import psycopg2
from database import get_db_connection
import pybaseball
import requests
from bs4 import BeautifulSoup

from calculate_grade import update_all_grades


# web scraping function to get player position
def get_player_position(first_name: str, last_name: str, player_id: int) -> str | None:
    url = f"https://baseballsavant.mlb.com/savant-player/{first_name}-{last_name}-{player_id}"
    
    headers = {'User-Agent': 'Mozilla/5.0'}
    response = requests.get(url, headers=headers)
    
    if response.status_code != 200:
        return None

    soup = BeautifulSoup(response.content, 'html.parser')

    bio_section = soup.find('div', class_='bio')
    if not bio_section:
        return None

    # if player is retired, the position div has a font size of .8 rem instead of 1 rem, so we check for both
    position_div = bio_section.find('div', style=lambda value: value and 'font-size: 1rem' in value)

    if position_div:
        strings = list(position_div.stripped_strings)
        if strings:
            position = strings[0].strip()  # position is usually the first string in that div
            return position
    else:
        retired_div = bio_section.find('div', style=lambda value: value and 'font-size: .8rem' in value)
    if retired_div:
        strings = list(retired_div.stripped_strings)
        if strings:
            position = strings[0].strip() # position is the first string in this
            return position
    

    return None

# web scraping function to get team for player since baseball savant csv files dont have team info, and we need team_id for our database
def get_player_team(first_name: str, last_name: str, player_id: int) -> str | None:
    # dict mapping name to team_id
    TEAM_MAP = {
        "New York Mets": "NYM", "Philadelphia Phillies": "PHI", "Atlanta Braves": "ATL", 
        "Miami Marlins": "MIA", "Washington Nationals": "WSH", "Los Angeles Dodgers": "LAD", 
        "San Francisco Giants": "SF", "San Diego Padres": "SD", "Colorado Rockies": "COL", 
        "Arizona Diamondbacks": "ARI", "Chicago Cubs": "CHC", "St. Louis Cardinals": "STL", 
        "Cincinnati Reds": "CIN", "Pittsburgh Pirates": "PIT", "Milwaukee Brewers": "MIL",
        "New York Yankees": "NYY", "Boston Red Sox": "BOS", "Toronto Blue Jays": "TOR", 
        "Tampa Bay Rays": "TB", "Baltimore Orioles": "BAL", "Houston Astros": "HOU", 
        "Athletics": "ATH", "Seattle Mariners":"SEA", "Los Angeles Angels": "LAA", 
        "Texas Rangers": "TEX", "Cleveland Guardians": "CLE", "Chicago White Sox":"CWS", 
        "Minnesota Twins": "MIN", "Kansas City Royals": "KC", "Detroit Tigers": "DET"
    }
    
    url = f"https://baseballsavant.mlb.com/savant-player/{first_name}-{last_name}-{player_id}"
    
    # headers for possible blocking
    headers = {'User-Agent': 'Mozilla/5.0'}
    response = requests.get(url, headers=headers)
    
    # we need status code 200, meaning it exists
    if response.status_code != 200:
        return None

    # getting the html content of the page and parsing it with BeautifulSoup
    soup = BeautifulSoup(response.content, 'html.parser')

    # in the inspect element the parent div that has the team name is the div with class 'bio'
    bio_section = soup.find('div', class_='bio')
    if not bio_section:
        return None

    # the team name is in the div with style 'font-size: 1rem;' inside the bio section
    team_div = bio_section.find('div', style=lambda value: value and 'font-size: 1rem' in value)

    if team_div:
        # strip the text to get the position, team name
        strings = list(team_div.stripped_strings)

        if not strings:
            return None

        # team name is the last string in that div
        full_team_name = strings[-1].strip()

        # map the full team name to the team_id
        return TEAM_MAP.get(full_team_name)
    else:
        # there are multiple lines with that styles so get them all
        line_8rem = bio_section.find_all(
            "div",
            style=lambda s: s and "font-size: .8rem" in s
        )

    # getting the second line which has the team name
    second_line = line_8rem[1] if len(line_8rem) > 1 else None

    if second_line:
        # turn each piece of text into a string in a list
        second_line_strings = list(second_line.stripped_strings)
        for token in reversed(second_line_strings):
            mapped_team = TEAM_MAP.get(token.strip())
            # if we find a mapped team in any of the tokens
            if mapped_team:
                return mapped_team

    return None
    

# populate database with players
def populate_players():
    # load in csv files
    batters_df = pd.read_csv('data/batters.csv')
    pitchers_df = pd.read_csv('data/pitchers.csv')

    # split the string for last name and first name
    # orginally in form "lastname, firstname"
    # expand = true splits into two new columns
    batters_df[['last_name', 'first_name']] = batters_df['last_name, first_name'].str.split(', ', expand=True)
    # remove any whitespace from the names
    batters_df['first_name'] = batters_df['first_name'].str.strip()
    batters_df['last_name'] = batters_df['last_name'].str.strip()

    pitchers_df[['last_name', 'first_name']] = pitchers_df['last_name, first_name'].str.split(', ', expand=True)
    pitchers_df['first_name'] = pitchers_df['first_name'].str.strip()
    pitchers_df['last_name'] = pitchers_df['last_name'].str.strip()

    conn = get_db_connection()
    cur = conn.cursor()

    try:
        # process batters
        print("Populating players from batters.csv...")

        counter = 0
        # first 100 rows to not overload
        for i, row in batters_df[-101:].iterrows():
            print(f"{counter}/100 Processing {row['first_name']} {row['last_name']} with player_id {row['player_id']}...")
            counter += 1
            team_id = get_player_team(row['first_name'], row['last_name'], row['player_id'])
            position = get_player_position(row['first_name'], row['last_name'], row['player_id'])
            cur.execute('''
                INSERT INTO Player (player_id, first_name, last_name, primary_position, team_id)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (player_id) DO NOTHING
            ''', (row['player_id'], row['first_name'], row['last_name'], position, team_id))

        counter = 0
        # process pitchers
        print("Populating players from pitchers.csv...")
        for i, row in pitchers_df[-101:].iterrows():
            print(f"{counter}/100 Processing {row['first_name']} {row['last_name']} with player_id {row['player_id']}...")
            counter += 1

            team_id = get_player_team(row['first_name'], row['last_name'], row['player_id'])
            cur.execute('''
                INSERT INTO Player (player_id, first_name, last_name, primary_position, team_id)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (player_id) DO NOTHING
            ''', (row['player_id'], row['first_name'], row['last_name'], 'P', team_id))

        conn.commit()
        print("Successfully populated players.")
    
    except Exception as e:
        print(e)
        conn.rollback()
        print(f"Error during population: {e}")
    finally:
        cur.close()
        conn.close()

def populate_metrics():
    # load in csv files
    batters_df = pd.read_csv('data/batters.csv')
    pitchers_df = pd.read_csv('data/pitchers.csv')

    conn = get_db_connection()
    cur = conn.cursor()

    try:
        # process batters
        print("Populating batter metrics...")
        for _, row in batters_df[-101:].iterrows():
            # create a scouting report for each player (using a default scout_id of 1 for automated imports)
            
            cur.execute('''
                INSERT INTO ScoutingReport (player_id, scout_id, report_date, overall_grade)
                VALUES (%s, %s, %s, %s) RETURNING report_id
            ''', (row['player_id'], 1, row['year'], 50)) # default overall grade of 50 for now, until we make our advanced grading function

            report_id = cur.fetchone()[0] # get the generated report_id to link with PerformanceMetrics
            
            

            # insert batter-specific metrics into PerformanceMetrics
            cur.execute('''
                INSERT INTO PerformanceMetrics (
                    report_id, exit_velocity, launch_angle, hard_hit_percentage,
                    zone_swing_percentage, zone_swing_miss_percentage,
                    out_zone_swing_percentage, out_zone_swing_miss_percentage, xwoba
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            ''', (
                report_id, row['exit_velocity_avg'], row['launch_angle_avg'], 
                row['hard_hit_percent'], row['z_swing_percent'], 
                row['z_swing_miss_percent'], row['oz_swing_percent'], 
                row['oz_swing_miss_percent'], row['xwoba']
            ))

        # process pitchers
        print("Populating pitcher metrics...")
        for _, row in pitchers_df[-101:].iterrows():
            cur.execute('''
                INSERT INTO ScoutingReport (player_id, scout_id, report_date, overall_grade)
                VALUES (%s, %s, %s, %s) RETURNING report_id
            ''', (row['player_id'], 1, row['year'], 50))
            
            report_id = cur.fetchone()[0]

            # insert Pitcher-specific metrics into PerformanceMetrics
            cur.execute('''
                INSERT INTO PerformanceMetrics (
                    report_id, four_seam_velocity, k_percentage, bb_percentage,
                    hard_hit_percentage, barrel_percentage, whiff_percentage,
                    gb_percentage, four_seam_spin, out_zone_swing_miss_percentage
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ''', (
                report_id, row['ff_avg_speed'], row['k_percent'], 
                row['bb_percent'], row['hard_hit_percent'], 
                row['barrel_batted_rate'], row['whiff_percent'], 
                row['groundballs_percent'], row['ff_avg_spin'], row['oz_swing_miss_percent']
            ))

        conn.commit()
        print("Successfully populated performance metrics.")

    except Exception as e:
        conn.rollback()
        print(f"Error during population: {e}")
    finally:
        cur.close()
        conn.close()

def populate_teams():
    conn = get_db_connection()
    cursor = conn.cursor()

    # all mlb teams with team_id, team_name, and division
    teams = [
        ('NYM', 'New York Mets', 'NL East'),
        ('PHI', 'Philadelphia Phillies', 'NL East'),
        ('ATL', 'Atlanta Braves', 'NL East'),
        ('MIA', 'Miami Marlins', 'NL East'),
        ('WSH', 'Washington Nationals', 'NL East'),

        ('LAD', 'Los Angeles Dodgers', 'NL West'),
        ('SF', 'San Francisco Giants', 'NL West'),
        ('SD', 'San Diego Padres', 'NL West'),
        ('COL', 'Colorado Rockies', 'NL West'),
        ('ARI', 'Arizona Diamondbacks', 'NL West'),

        ('CHC', 'Chicago Cubs', 'NL Central'),
        ('STL', 'St. Louis Cardinals', 'NL Central'),
        ('CIN', 'Cincinnati Reds', 'NL Central'),
        ('PIT', 'Pittsburgh Pirates', 'NL Central'),
        ('MIL', 'Milwaukee Brewers', 'NL Central'),

        ('NYY', 'New York Yankees', 'AL East'),
        ('BOS', 'Boston Red Sox', 'AL East'),
        ('TOR', 'Toronto Blue Jays', 'AL East'),
        ('TB', 'Tampa Bay Rays', 'AL East'),
        ('BAL', 'Baltimore Orioles', 'AL East'),

        ('HOU', 'Houston Astros', 'AL West'),
        ('ATH', 'Athletics', 'AL West'),
        ('SEA', 'Seattle Mariners', 'AL West'),
        ('LAA', 'Los Angeles Angels', 'AL West'),
        ('TEX', 'Texas Rangers', 'AL West'),

        ('CLE', 'Cleveland Guardians', 'AL Central'),
        ('CWS', 'Chicago White Sox', 'AL Central'),
        ('MIN', 'Minnesota Twins', 'AL Central'),
        ('KC', 'Kansas City Royals', 'AL Central'),
        ('DET', 'Detroit Tigers', 'AL Central')
    ]

    print("Populating teams...")
    try:
        for team_id, name, division in teams:
            cursor.execute('''
                INSERT INTO Team (team_id, name, division)
                VALUES (%s, %s, %s)
                ON CONFLICT (team_id) DO NOTHING
            ''', (team_id, name, division))
        
        conn.commit()
        print("Successfully populated teams.")

    except Exception as e:
        conn.rollback()
        print(f"Error during population: {e}")
    finally:
        cursor.close()
        conn.close()

def populate_scouts():
    conn = get_db_connection()
    cur = conn.cursor()

    try:
        # make sample scout with fixed id = 1
        cur.execute('''
            INSERT INTO Scout (scout_id, name, team_id)
            VALUES (%s, %s, %s)
            ON CONFLICT (scout_id) DO NOTHING
        ''', (1, 'John Doe', 'TB'))

        # Keep SERIAL sequence in sync after manual insert
        cur.execute('''
            SELECT setval(
                pg_get_serial_sequence('scout', 'scout_id'),
                (SELECT COALESCE(MAX(scout_id), 1) FROM Scout),
                true
            )
        ''')

        conn.commit()
        print("Successfully populated scouts.")
    except Exception as e:
        conn.rollback()
        print(f"Error populating scouts: {e}")
    finally:
        cur.close()
        conn.close()

if __name__ == "__main__":
    populate_teams()
    populate_players()
    populate_scouts()
    populate_metrics()
    update_all_grades()