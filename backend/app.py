#TODO: Create, update, delete
from flask import Flask, render_template, request,redirect, url_for, flash, session
from database import *
import psycopg2.extras


app = Flask(__name__)
app.secret_key ="23adkfn23rfnjfa98" 

def fetch_data(query,params=None):
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cur.execute(query,params)
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
@app.route('/addScout', methods=['GET','POST']) #creates scout logic, pairs with /new scout
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




@app.route('/addReport')    #renders page
def addReport():
    players = fetch_data("SELECT first_name, last_name FROM Player")
    return render_template('addReport.html',players=players)
@app.route('/createReport', methods = ['GET','POST']) #logic with addReport
def createReport():
    players = fetch_data("SELECT first_name, last_name FROM Player")
    
    if request.method == 'POST':
        try:
            name = request.form["Name"]
            player = request.form["player"]

            thing,message = checkScout(name) #puts scout in db, checks as well

            if thing==True:     #name doesn't exist, stops from going further
                flash("Scout not found")
                return render_template('addReport.html',players=players)
            
            session['name'] = name      #store for later redirection
            session['player'] = player  #store for later redirection
            
            
            player_parts = player.split()   #break apart for sending names along
            firstName = player_parts[0]
            lastName = player_parts[1]
    
            position = fetch_data("SELECT primary_position FROM Player WHERE first_name = %s AND last_name = %s",(firstName,lastName,))
            
            if position[0][0] == ('P'):   #IF player is a pitcher:
                return redirect(url_for('addPitcherInfo',firstName=firstName,lastName =lastName,player=player)) #above goes with this
            
            #else a normal player
            return redirect(url_for('addPositionInfo')) #above goes with this

        except Exception as e:
            print("ERROR")
            return render_template('addReport.html',error=str(e),players=players)



@app.route('/addReport/addPitcherInfo')    #renders page for PITCHERS ONLY
def addPitcherInfo():
    scoutName = session.get('name') #get scout name and player from session (prev passed through)
    player = session.get('player')
    return render_template('addPitcherInfo.html',name=scoutName,player=player)
@app.route('/addReport/addPitcherInfo/pitcherStats',methods=['POST']) #does logic for above function
def pitcherStats():
    try:
        scoutName = session.get('name') #get scout name and player from session (prev passed through)
        player = session.get('player')

        #make everyting floats
        hh = float(request.form['hh_perc'])
        outzone=float(request.form['outzone_perc'])
        barrel = float(request.form['barrel_perc'])
        k = float(request.form['k_perc'])
        bb = float(request.form['bb_perc'])
        whiff = float(request.form['whiff_perc'])
        gb = float(request.form['gb_perc'])
        velocity = float(request.form['fourSeamVel_perc'])
        spin = float(request.form['fourSeamSpin_perc'])

        message = insertPitcherInfo(scoutName,player,hh,outzone,barrel,k,bb,whiff,gb,velocity,spin)

        flash(message)
        return redirect(url_for('index'))

    except Exception as e:
        flash("Error creating report")
        return render_template('addPitcherInfo.html')





@app.route('/addReport/addPositionInfo') #renders page for POSITION PLAYERS ONLY
def addPositionInfo():
    name = session.get('name')
    player = session.get('player')
    return render_template('addPositionInfo.html', name=name, player=player)

if __name__ == '__main__':
    app.run(debug=True)