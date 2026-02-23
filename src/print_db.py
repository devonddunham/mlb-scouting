# gemini wrote this so rather than using sqlite in the terminal
import sqlite3

def verify_data():
    conn = sqlite3.connect('mlb_scouting.db')
    cursor = conn.cursor()

    print("--- Players in Database ---")
    print ("PlayerID, First Name, Last Name, Position")
    cursor.execute("SELECT playerID, nameFirst, nameLast, primaryPosition FROM Player")
    for row in cursor.fetchall():
        print(row)


    # print teams
    print("\n--- Teams in Database ---")
    print ("TeamID, Name, Division")
    cursor.execute("SELECT teamID, name, division FROM Team")
    for row in cursor.fetchall():
        print(row)

    # print scouts
    print("\n--- Scouts in Database ---")
    print ("ScoutID, Name, Region, TeamID")
    cursor.execute("SELECT scoutID, name, region, teamID FROM Scout")
    for row in cursor.fetchall():
        print(row)

    print("\n--- Scouting Reports in Database ---")
    print ("Date, Last Name, Player Type, Exit Velocity, Pitch Velocity, Overall Grade")
    
    cursor.execute('''
        SELECT r.date, p.nameLast, r.playerType, r.exit_velocity, r.pitch_velocity, r.overall_grade
        FROM ScoutingReport r
        JOIN Player p ON r.playerID = p.playerID
    ''')
    for row in cursor.fetchall():
        print(row)

    conn.close()

if __name__ == "__main__":
    verify_data()