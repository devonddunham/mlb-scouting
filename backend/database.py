import os
import psycopg2
import psycopg2.extras
from dotenv import load_dotenv

# load env variables from .env file
load_dotenv()

DB_HOST = os.environ.get('DB_HOST', 'localhost')
DB_NAME = os.environ.get('DB_NAME', 'mlb_scouting_db')
DB_USER = os.environ.get('DB_USER')
DB_PASS = os.environ.get('DB_PASS')
DB_PORT = os.environ.get('DB_PORT', '5432')

def get_db_connection():
    return psycopg2.connect(
        host=DB_HOST,
        database=DB_NAME,
        user=DB_USER,
        password=DB_PASS,
        port=DB_PORT
    )

def drop_tables():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # CASCADE makes sure drop dependent tables so no FK issues
    cursor.execute('DROP TABLE IF EXISTS PerformanceMetrics CASCADE')
    cursor.execute('DROP TABLE IF EXISTS ScoutingReport CASCADE')
    cursor.execute('DROP TABLE IF EXISTS Player CASCADE')
    cursor.execute('DROP TABLE IF EXISTS Scout CASCADE')
    cursor.execute('DROP TABLE IF EXISTS Team CASCADE')
    
    print("dropped existing tables")
    conn.commit()
    cursor.close()
    conn.close()

def create_tables():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Team
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS Team (
            team_id VARCHAR(10) PRIMARY KEY,
            name VARCHAR(100) NOT NULL,
            division VARCHAR(50)
        )''')

    # Scout many-to-one with Team
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS Scout (
            scout_id SERIAL PRIMARY KEY,
            name VARCHAR(100) NOT NULL,
            region VARCHAR(50),
            team_id VARCHAR(10) REFERENCES Team(team_id)
        )''')

    # Player many-to-one with Team
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS Player (
            player_id VARCHAR(50) PRIMARY KEY, -- BBRef ID
            mlbam_id INTEGER UNIQUE NOT NULL,  -- Statcast ID
            first_name VARCHAR(50),
            last_name VARCHAR(50),
            primary_position VARCHAR(20),
            team_id VARCHAR(10) REFERENCES Team(team_id)
        )''')

    # ScoutingReport many-to-one with Player and Scout
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS ScoutingReport (
            report_id SERIAL PRIMARY KEY,
            player_id VARCHAR(50) REFERENCES Player(player_id),
            scout_id INTEGER REFERENCES Scout(scout_id),
            report_date DATE DEFAULT CURRENT_DATE,
            overall_grade INTEGER, -- calculated by advanced function
            scout_comments TEXT
        )''')

    # PerformanceMetrics one-to-one with ScoutingReport
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS PerformanceMetrics (
            report_id INTEGER PRIMARY KEY REFERENCES ScoutingReport(report_id) ON DELETE CASCADE,
            exit_velocity REAL,
            launch_angle REAL,
            bat_speed REAL,
            pitch_velocity REAL,
            pfx_x REAL,
            pfx_z REAL,
            pitch_extension REAL,
            xwOBA REAL,
            swing_length REAL
        )''')

    print("intialized database")
    conn.commit()
    cursor.close()
    conn.close()

def start_db():
    if input("Drop existing MLB tables? y/n: ").lower() == 'y':
        drop_tables()
    create_tables()

if __name__ == '__main__':
    start_db()