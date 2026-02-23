import sqlite3

def deploy():
    conn = sqlite3.connect('mlb_scouting.db')
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS Team (
            teamID TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            division TEXT
        )
    ''')

    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS Scout (
            scoutID INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            region TEXT,
            teamID TEXT,
            FOREIGN KEY (teamID) REFERENCES Team(teamID)
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS Player (
            playerID TEXT PRIMARY KEY, -- Lahman/BBRef ID
            mlbamID INTEGER UNIQUE,    -- Statcast ID
            nameFirst TEXT,
            nameLast TEXT,
            primaryPosition TEXT,
            teamID TEXT,
            FOREIGN KEY (teamID) REFERENCES Team(teamID)
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS ScoutingReport (
            reportID INTEGER PRIMARY KEY AUTOINCREMENT,
            playerID TEXT NOT NULL,
            scoutID INTEGER NOT NULL,
            date TEXT NOT NULL,
            playerType TEXT CHECK(playerType IN ('Hitter', 'Pitcher')), -- will only allow 'Hitter' or 'Pitcher'
            -- hitter data (Statcast)
            exit_velocity REAL,
            launch_angle REAL,
            -- pitcher data (Statcast)
            pitch_velocity REAL,
            spin_rate REAL,
            -- 20-80 scale metrics
            overall_grade INTEGER,
            FOREIGN KEY (playerID) REFERENCES Player(playerID),
            FOREIGN KEY (scoutID) REFERENCES Scout(scoutID)
        )
    ''')

    conn.commit()
    conn.close()
    print("Database schema deployed successfully.")

def drop_tables():
    conn = sqlite3.connect('mlb_scouting.db')
    cursor = conn.cursor()

    cursor.execute('DROP TABLE IF EXISTS ScoutingReport')
    cursor.execute('DROP TABLE IF EXISTS Player')
    cursor.execute('DROP TABLE IF EXISTS Scout')
    cursor.execute('DROP TABLE IF EXISTS Team')

    conn.commit()
    conn.close()
    print("All tables dropped successfully.")

if __name__ == "__main__":
    if input("Drop tables? y/n: ").lower() == 'y':
        drop_tables()
    deploy()