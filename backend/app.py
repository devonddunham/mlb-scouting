#TODO: Create, update, delete
from flask import Flask, render_template, request,redirect, url_for, flash, session
from database import *
import psycopg2.extras

from calculate_grade import update_single_grade

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
            year = request.form["Year"]

            thing,message = checkScout(name) #puts scout in db, checks as well

            if thing==True:     #name doesn't exist, stops from going further
                flash("Scout not found")
                return render_template('addReport.html',players=players)
            
            session['name'] = name      #store for later redirection
            session['player'] = player  #store for later redirection
            session['year'] = year
            
            
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
        year = session.get('year')

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

        message = insertPitcherInfo(scoutName,player,hh,outzone,barrel,k,bb,whiff,gb,velocity,spin,year)

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
@app.route('/addReport/addPositionInfo/playerStats',methods=['POST']) #does logic for above function
def playerStats():
    try:
        scoutName = session.get('name') #get scout name and player from session (prev passed through)
        player = session.get('player')
        year = session.get('year')
        
        #make everyting floats
        exitV = float(request.form['exit_velocity'])
        launchAng = float(request.form['launch_angle'])
        xwoba = float(request.form['xwoba'])
        xobp = float(request.form['xobp'])
        hh = float(request.form['hh'])
        zoneSwing = float(request.form['zoneSwing'])
        zoneSwingMiss = float(request.form['zoneSwingMiss'])
        outZoneSwing = float(request.form['outzoneSwing'])
        outZoneSwingMiss = float(request.form['outzoneSwingMiss'])

        message = insertPositionInfo(scoutName,player,year,exitV,launchAng,xwoba,xobp,hh,zoneSwing,zoneSwingMiss,outZoneSwing,outZoneSwingMiss)

        flash(message)
        return redirect(url_for('index'))
    except Exception as e:
        flash("Error creating report")
        return render_template('addPositionInfo.html')

@app.route('/updateReport')
def updateReport():
    return render_template('updateReport.html')
@app.route('/changeReport', methods=['POST'])
def changeReport():
    sName = request.form['scoutName']
    pName = request.form['playerName']
    year = request.form['year']
    exists = checkReport(sName,pName,year)
    
    if exists:
        firstName, lastName = getPlayer(pName)
        position = fetch_data("SELECT primary_position FROM Player WHERE first_name = %s AND last_name = %s",(firstName,lastName,))
        if position[0][0] == 'P':
            return redirect(url_for('updatePitcher', scout=sName, player=pName, year=year))
        else:
            return redirect(url_for('updatePosition', scout=sName, player=pName, year=year))
    else:
        flash("Could not find report with given information")
        return redirect(url_for('updateReport'))

@app.route('/updatePitcher/<scout>/<player>/<year>')
def updatePitcher(scout, player, year):
    report_id = getReportId(scout, player, year)
    if report_id:
        metrics = getPitcherMetrics(report_id)
        return render_template('updatePitcher.html', scout=scout, player=player, year=year, metrics=metrics)
    else:
        flash("Report not found")
        return redirect(url_for('updateReport'))

@app.route('/updatePosition/<scout>/<player>/<year>')
def updatePosition(scout, player, year):
    report_id = getReportId(scout, player, year)
    if report_id:
        metrics = getPositionMetrics(report_id)
        return render_template('updatePosition.html', scout=scout, player=player, year=year, metrics=metrics)
    else:
        flash("Report not found")
        return redirect(url_for('updateReport'))

@app.route('/updatePitcherStats', methods=['POST'])
def updatePitcherStats():
    try:
        scout = request.form['scout']
        player = request.form['player']
        year = int(request.form['year'])
        
        report_id = getReportId(scout, player, year)
        if not report_id:
            flash("Report not found")
            return redirect(url_for('updateReport'))
        
        # Get form data
        hh = float(request.form['hh_perc'])
        outzone = float(request.form['outzone_perc'])
        barrel = float(request.form['barrel_perc'])
        k = float(request.form['k_perc'])
        bb = float(request.form['bb_perc'])
        whiff = float(request.form['whiff_perc'])
        gb = float(request.form['gb_perc'])
        velocity = float(request.form['fourSeamVel_perc'])
        spin = float(request.form['fourSeamSpin_perc'])
        
        message = updatePitcherMetrics(report_id, hh, outzone, barrel, k, bb, whiff, gb, velocity, spin)

        # recalculate grade for this report
        update_single_grade(report_id)

        flash(message)
        return redirect(url_for('index'))
    except Exception as e:
        flash("Error updating report")
        return redirect(url_for('updateReport'))

@app.route('/updatePositionStats', methods=['POST'])
def updatePositionStats():
    try:
        scout = request.form['scout']
        player = request.form['player']
        year = int(request.form['year'])
        
        report_id = getReportId(scout, player, year)
        if not report_id:
            flash("Report not found")
            return redirect(url_for('updateReport'))
        
        # Get form data
        exitV = float(request.form['exit_velocity'])
        launchAng = float(request.form['launch_angle'])
        xwoba = float(request.form['xwoba'])
        xobp = float(request.form['xobp'])
        hh = float(request.form['hh'])
        zoneSwing = float(request.form['zoneSwing'])
        zoneSwingMiss = float(request.form['zoneSwingMiss'])
        outZoneSwing = float(request.form['outzoneSwing'])
        outZoneSwingMiss = float(request.form['outzoneSwingMiss'])
        
        message = updatePositionMetrics(report_id, exitV, launchAng, xwoba, xobp, hh, zoneSwing, zoneSwingMiss, outZoneSwing, outZoneSwingMiss)

        # recalculate grade for this report
        update_single_grade(report_id)

        flash(message)
        return redirect(url_for('index'))
    except Exception as e:
        flash("Error updating report")
        return redirect(url_for('updateReport'))

@app.route('/deleteReport')
def deleteReport():
    return render_template('deleteReport.html')
@app.route('/removeReport', methods=['POST'])
def removeRep():
    try:
        scout = request.form['scoutName']
        player = request.form['playerName']
        year = int(request.form['year'])
        
        message = removeReport(scout, player, year)
        flash(message)
        return redirect(url_for('index'))
    except Exception as e:
        flash(f"Error deleting report: {str(e)}")
        return redirect(url_for('deleteReport'))

# search function: devon
@app.route('/search', methods=['GET', 'POST'])
def search():
    results = []
    search_query = ""
    search_type = "player" # default

    if request.method == 'POST':
        search_query = request.form.get('search_query', '')
        search_type = request.form.get('search_type', 'player')

        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

        if search_type == 'player':
            # search by player's first or last name
            # ilike is a case-insensitive search
            query = """
                SELECT p.first_name, p.last_name, s.name as scout_name, 
                       r.report_date as report_year, r.overall_grade
                FROM ScoutingReport r
                JOIN Player p ON r.player_id = p.player_id
                JOIN Scout s ON r.scout_id = s.scout_id
                WHERE p.first_name ILIKE %s OR p.last_name ILIKE %s
            """
            cur.execute(query, (f'%{search_query}%', f'%{search_query}%'))
            
        elif search_type == 'scout':
            # search by scout's name
            query = """
                SELECT p.first_name, p.last_name, s.name as scout_name, 
                       r.report_date as report_year, r.overall_grade
                FROM ScoutingReport r
                JOIN Player p ON r.player_id = p.player_id
                JOIN Scout s ON r.scout_id = s.scout_id
                WHERE s.name ILIKE %s
            """
            cur.execute(query, (f'%{search_query}%',))

        results = cur.fetchall()
        cur.close()
        conn.close()

    return render_template('search.html', results=results, search_query=search_query, search_type=search_type)

if __name__ == '__main__':
    app.run(debug=True)