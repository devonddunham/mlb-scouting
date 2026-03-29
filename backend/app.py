#TODO: Create, update, delete
from flask import Flask, render_template, request,redirect, url_for, flash
from database import *
import psycopg2.extras

app = Flask(__name__)
app.secret_key ="23adkfn23rfnjfa98" 

def fetch_data(query):
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cur.execute(query)
    data = cur.fetchall()
    cur.close()
    conn.close()
    return data

@app.route('/') #home
def index():
    return render_template('home.html')

@app.route('/players') #shows all the players
def players():
    data = fetch_data("SELECT * FROM Player")
    return render_template('table.html', title="Players", data=data)

@app.route('/teams')    #shows all the teams
def teams():
    data = fetch_data("SELECT * FROM Team")
    return render_template('table.html', title="Teams", data=data)

@app.route('/reports')  #shows all information on reports
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

@app.route('/newScout') #goes with /add scout logic
def newScout():
    teams = fetch_data("SELECT * FROM Team")
    return render_template('addScout.html',teams=teams)

#creates scout logic
@app.route('/addScout', methods=['GET','POST'])
def addScout():
    teams = fetch_data("SELECT * FROM Team")

    if request.method == 'POST':
        try:
            name = request.form["Name"]
            teamId = request.form["team_id"]

            thing,message = makeScout(name, teamId) #puts scout in db, checks as well
            
            if thing==False:
                flash(message)
                return render_template('addScout.html',teams=teams)
            
            flash(message)
            return redirect(url_for('index'))

        except Exception as e:
            return render_template('addScout.html',error=str(e),teams=teams)

    return render_template('addScout.html', teams=teams)

if __name__ == '__main__':
    app.run(debug=True)