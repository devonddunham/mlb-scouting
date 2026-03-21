from flask import Flask, render_template
from database import get_db_connection
import psycopg2.extras

app = Flask(__name__)

def fetch_data(query):
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cur.execute(query)
    data = cur.fetchall()
    cur.close()
    conn.close()
    return data

@app.route('/')
def index():
    return "<h1>MLB Scouting App</h1><ul><li><a href='/players'>Players</a></li><li><a href='/teams'>Teams</a></li><li><a href='/reports'>Scouting Reports</a></li></ul>"

@app.route('/players')
def players():
    data = fetch_data("SELECT * FROM Player")
    return render_template('table.html', title="Players", data=data)

@app.route('/teams')
def teams():
    data = fetch_data("SELECT * FROM Team")
    return render_template('table.html', title="Teams", data=data)

@app.route('/reports')
def reports():
    # join tables to show actual names instead of just ids
    query = """
        SELECT p.first_name, p.last_name, s.name as scout_name, r.overall_grade, r.report_date 
        FROM ScoutingReport r
        JOIN Player p ON r.player_id = p.player_id
        JOIN Scout s ON r.scout_id = s.scout_id
    """
    data = fetch_data(query)
    return render_template('table.html', title="Scouting Reports", data=data)

if __name__ == '__main__':
    app.run(debug=True)