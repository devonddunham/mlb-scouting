import os
import psycopg2
import psycopg2.extras
from dotenv import load_dotenv
from datetime import datetime   #get rid of later


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
            team_id VARCHAR(10) REFERENCES Team(team_id)
        )''')

    # Player many-to-one with Team
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS Player (
            player_id INTEGER PRIMARY KEY,
            first_name VARCHAR(50),
            last_name VARCHAR(50),
            primary_position VARCHAR(20),
            team_id VARCHAR(10) REFERENCES Team(team_id)
        )''')

    # ScoutingReport many-to-one with Player and Scout
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS ScoutingReport (
            report_id SERIAL PRIMARY KEY,
            player_id INTEGER REFERENCES Player(player_id),
            scout_id INTEGER REFERENCES Scout(scout_id),
            report_date INTEGER, -- YYYY
            overall_grade INTEGER -- calculated by advanced function
        )''')

    # PerformanceMetrics one-to-one with ScoutingReport
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS PerformanceMetrics (
            report_id INTEGER PRIMARY KEY REFERENCES ScoutingReport(report_id) ON DELETE CASCADE,
            exit_velocity REAL, -- AVG speed of the ball off the bat in miles per hour
            launch_angle REAL, -- AVG angle of the ball off the bat in degrees, where 0 is level, positive is upward, and negative is downward.
            xwOBA REAL, -- Expected Weighted On-Base Average, a comprehensive metric that estimates a player's offensive contribution based on the quality of contact and plate discipline.
            xOBP REAL, -- Expected On-Base Percentage, which estimates how often a player reaches base based on the quality of contact and plate discipline.
            hard_hit_percentage REAL, -- percentage of batted balls with an exit velocity of 95 mph or higher, showing the player's ability to make strong contact. for both batters and pitchers. pitchers want it low, batters want it high
            zone_swing_percentage REAL,
            zone_swing_miss_percentage REAL,
            out_zone_swing_percentage REAL,
            out_zone_swing_miss_percentage REAL, -- for both batters and pitchers
            barrel_percentage REAL, -- percentage of batted balls that are 'barrels', balls hit with optimal combo of exit velocity and launch angle. Pitchers want it low
            k_percentage REAL,
            bb_percentage REAL,
            whiff_percentage REAL, -- percentage of swings that miss the ball entirely, pitchers want it high
            gb_percentage REAL, -- percentage of batted balls that are ground balls, pitchers want it high
            four_seam_velocity REAL, -- average velocity of the pitcher's four-seam fastball, key indicator of pitching strength
            four_seam_spin REAL -- average spin rate of the pitcher's four-seam fastball, higher spin can indicate better movement and deception
        )''')

    print("intialized database")
    conn.commit()
    cursor.close()
    conn.close()

def makeScout(name, teamId):    #makes a scout
    thing,message = checkScout(name)
    if(thing==True):    #makes sure name is free
        conn = None
        cur = None
        try:
            conn = get_db_connection()
            cur = conn.cursor()

            cur.execute('INSERT INTO Scout (name, team_id) VALUES (%s, %s)',(name, teamId))

            conn.commit()
            cur.close()
            conn.close()

        except Exception as e:
            if conn:
                conn.rollback()
            raise e #send back

        finally:
            if cur:
                cur.close()
            if conn:
                conn.close()
    
    return thing,message

def checkScout(name):
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("SELECT name FROM Scout WHERE name = %s", (name,))
    findName = cur.fetchone()

    cur.close()
    conn.close()
    
    if findName is None:
        return True,"Success! Scout created!"
    
    return False,"Error. Name exists in database"

def createReport(scout,player):
    player_parts = player.split()   #break apart for sending names along
    firstName = player_parts[0]
    lastName = player_parts[1]
    
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("SELECT player_id FROM Player WHERE first_name = %s AND last_name= %s",(firstName,lastName,)) #get player_id 
    play_id = cur.fetchone()
    
    if play_id:     #get rid of tuple
        play_id = play_id[0]

    cur.execute("SELECT scout_id FROM Scout WHERE name = %s",(scout,))
    scout_id = cur.fetchone()
    
    if scout_id:
        scout_id = scout_id[0]

    year = datetime.now().year   #GET RID OF LATER, TESTING PURPOSES RN
    grade = advancedFunc()      #IMPLEMENTATION AT BOTTOM

    try:
        print("inside try block")
        #check if this already exists(all data matches) or not before adding it!
        cur.execute('''SELECT report_id FROM ScoutingReport WHERE player_id=%s AND
                        scout_id=%s AND overall_grade=%s AND report_date=%s''',
                        (play_id,scout_id,grade,year))
        ans = cur.fetchall()
        
        if ans:         #if answer is true, the report already exists
            return None
        else:   #report doesn't exist, proceeed with making of the report
            cur.execute('''INSERT INTO ScoutingReport (player_id, scout_id, report_date, overall_grade)
                        VALUES (%s, %s, %s, %s)''',
                        (play_id,scout_id,year,grade))
            
            conn.commit()

            cur.execute('''SELECT report_id FROM ScoutingReport WHERE player_id=%s AND
                        scout_id=%s AND overall_grade=%s AND report_date=%s''',
                        (play_id,scout_id,grade,year))
            rep_id = cur.fetchone()
            return rep_id[0]      #return report_id for said ScoutingReport

    except Exception as e:
        if conn:
            conn.rollback()
        raise e #send back

    finally:        #close everything
        if cur:
            cur.close()
        if conn:
            conn.close()



def insertPitcherInfo(scout,player,hh,outzone,barrel,k,bb,whiff,gb,velocity,spin):
    #make scouting report
    id=createReport(scout,player)  #make actual report first, need report_id for performanceMetrics
    
    if id == None:
        return "Error, this report already exists"
    
    #Else add the info in and connect everything
    conn = get_db_connection()
    cur = conn.cursor()
 
    cur.execute('''INSERT INTO PerformanceMetrics
                    (report_id,exit_velocity,launch_angle,xwoba,xobp,hard_hit_percentage,zone_swing_percentage,zone_swing_miss_percentage,
                    out_zone_swing_percentage,out_zone_swing_miss_percentage,barrel_percentage,k_percentage,bb_percentage,whiff_percentage,
                    gb_percentage,four_seam_velocity,four_seam_spin) VALUES
                    (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)''',
                    (id,None,None,None,None,hh,None,None,None,outzone,barrel,k,bb,whiff,gb,velocity,spin)
                )
    
    conn.commit()
    cur.close()
    conn.close()

    return "Report created successfully"

def advancedFunc():
    return 0


def start_db():
    if input("Drop existing MLB tables? y/n: ").lower() == 'y':
        drop_tables()
    create_tables()

if __name__ == '__main__':
    start_db()