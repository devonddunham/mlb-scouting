#TODO: Create, update, delete
from flask import Flask, jsonify, render_template, request,redirect, url_for, flash, session
from database import *
import psycopg2.extras

from calculate_grade import update_single_grade

app = Flask(__name__)
app.secret_key ="23adkfn23rfnjfa98" 

# fields for pitchers
PITCHER_METRIC_FIELDS = [
    "hard_hit_percentage",
    "out_zone_swing_miss_percentage",
    "barrel_percentage",
    "k_percentage",
    "bb_percentage",
    "whiff_percentage",
    "gb_percentage",
    "four_seam_velocity",
    "four_seam_spin",
]

# fields for position players
POSITION_METRIC_FIELDS = [
    "exit_velocity",
    "launch_angle",
    "xwoba",
    "xobp",
    "hard_hit_percentage",
    "zone_swing_percentage",
    "zone_swing_miss_percentage",
    "out_zone_swing_percentage",
    "out_zone_swing_miss_percentage",
]

def fetch_data(query,params=None):
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cur.execute(query,params)
    data = cur.fetchall()
    cur.close()
    conn.close()
    return data

# get the data but in a list of dicts instead of list of tuples
# easier for jsonify
def fetch_data_dict(query, params=None):
    return [dict(row) for row in fetch_data(query, params)]

# get a single row as a dict, or None if no rows
def fetch_one_data_dict(query, params=None):
    rows = fetch_data_dict(query, params)
    if rows:
        return rows[0]
    return None

# return a single float value or None
# if value is an empty string
def to_nullable_float(value):
    if value is None:
        return None
    if isinstance(value, str):
        value = value.strip()
        if value == "":
            return None
    return float(value)

# get all details for a report
# every metric, player info, scout info, team info
def get_report_detail_row(report_id):
    query = """
        SELECT
            r.report_id,
            r.report_date,
            r.overall_grade,
            p.player_id,
            p.first_name,
            p.last_name,
            p.primary_position,
            p.team_id,
            t.name AS team_name,
            s.scout_id,
            s.name AS scout_name,
            pm.exit_velocity,
            pm.launch_angle,
            pm.xwoba,
            pm.xobp,
            pm.hard_hit_percentage,
            pm.zone_swing_percentage,
            pm.zone_swing_miss_percentage,
            pm.out_zone_swing_percentage,
            pm.out_zone_swing_miss_percentage,
            pm.barrel_percentage,
            pm.k_percentage,
            pm.bb_percentage,
            pm.whiff_percentage,
            pm.gb_percentage,
            pm.four_seam_velocity,
            pm.four_seam_spin
        FROM ScoutingReport r
        JOIN Player p ON r.player_id = p.player_id
        JOIN Scout s ON r.scout_id = s.scout_id
        LEFT JOIN Team t ON p.team_id = t.team_id
        LEFT JOIN PerformanceMetrics pm ON r.report_id = pm.report_id
        WHERE r.report_id = %s
    """

    # return single dict with all info for this report
    return fetch_one_data_dict(query, (report_id,))

# turn the report details row into a more usable dict for the frontend
def serialize_report_detail(report_row):
    if not report_row:
        return None

    # report_row is already a dict, but reshape it for frontend
    report = dict(report_row)

    # if the player is a pitcher only include pitcher metrics, else only position player metrics
    is_pitcher = report.get("primary_position") == "P"
    metric_fields = PITCHER_METRIC_FIELDS if is_pitcher else POSITION_METRIC_FIELDS
    report["report_type"] = "pitcher" if is_pitcher else "position"

    # inside nested metrics dict, put needed metrics in with the value
    report["metrics"] = {field: report.get(field) for field in metric_fields}
    return report

# search for player or scout
def run_report_search(search_type, search_query):
    pattern = f"%{search_query}%"

    if search_type == "player":
        query = """
            SELECT
                r.report_id,
                p.first_name,
                p.last_name,
                s.name AS scout_name,
                r.report_date AS report_year,
                r.overall_grade
            FROM ScoutingReport r
            JOIN Player p ON r.player_id = p.player_id
            JOIN Scout s ON r.scout_id = s.scout_id
            WHERE p.first_name ILIKE %s OR p.last_name ILIKE %s
            ORDER BY r.report_date DESC, p.last_name, p.first_name
        """

        # return all reports for this search
        return fetch_data_dict(query, (pattern, pattern))

    if search_type == "scout":
        query = """
            SELECT
                r.report_id,
                p.first_name,
                p.last_name,
                s.name AS scout_name,
                r.report_date AS report_year,
                r.overall_grade
            FROM ScoutingReport r
            JOIN Player p ON r.player_id = p.player_id
            JOIN Scout s ON r.scout_id = s.scout_id
            WHERE s.name ILIKE %s
            ORDER BY r.report_date DESC, p.last_name, p.first_name
        """

        # return all reports for this search
        return fetch_data_dict(query, (pattern,))

    raise ValueError("Invalid search type")

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

# turn sql query for player into json for API
@app.route('/api/players')
def api_players():
    try:
        query = """
            SELECT player_id, first_name, last_name, primary_position, team_id
            FROM Player
            ORDER BY last_name, first_name
        """
        return jsonify(fetch_data_dict(query))
    except Exception:
        app.logger.exception("Failed to fetch players")
        return jsonify({"error": "Failed to fetch players"}), 500

# turn sql query for team into json for API
@app.route('/api/teams')
def api_teams():
    try:
        query = """
            SELECT team_id, name, division
            FROM Team
            ORDER BY division
        """
        return jsonify(fetch_data_dict(query))
    except Exception:
        app.logger.exception("Failed to fetch teams")
        return jsonify({"error": "Failed to fetch teams"}), 500

# turn sql query for scout into json for API
@app.route('/api/scouts')
def api_scouts():
    try:
        query = """
            SELECT s.scout_id, s.name, s.team_id, t.name AS team_name
            FROM Scout s
            LEFT JOIN Team t ON s.team_id = t.team_id
            ORDER BY s.name
        """
        return jsonify(fetch_data_dict(query))
    except Exception:
        app.logger.exception("Failed to fetch scouts")
        return jsonify({"error": "Failed to fetch scouts"}), 500

@app.route('/api/reports')
def api_reports():
    try:
        query = """
            SELECT
                r.report_id,
                p.player_id,
                p.first_name,
                p.last_name,
                p.primary_position,
                s.scout_id,
                s.name AS scout_name,
                r.overall_grade,
                r.report_date
            FROM ScoutingReport r
            JOIN Player p ON r.player_id = p.player_id
            JOIN Scout s ON r.scout_id = s.scout_id
            ORDER BY r.report_date DESC, p.last_name, p.first_name
        """
        return jsonify(fetch_data_dict(query))
    except Exception:
        app.logger.exception("Failed to fetch reports")
        return jsonify({"error": "Failed to fetch reports"}), 500

@app.route('/api/reports/<int:report_id>')
def api_report_details(report_id):
    try:
        report = serialize_report_detail(get_report_detail_row(report_id))
        if not report:
            return jsonify({"error": "Report not found"}), 404
        return jsonify(report)
    except Exception:
        app.logger.exception("Failed to fetch report details")
        return jsonify({"error": "Failed to fetch report details"}), 500

@app.route('/api/reports/<int:report_id>', methods=['PUT'])
def api_update_report(report_id):
    try:
        # get the metrics dict from the request body, or use empty dict if not provided
        metrics_dict = request.get_json(silent=True) or {}
        metrics = metrics_dict.get("metrics")

        # if the type is not a dict
        if not isinstance(metrics, dict):
            return jsonify({"error": "Request body must include a metrics object"}), 400

        report_row = get_report_detail_row(report_id)
        if not report_row:
            return jsonify({"error": "Report not found"}), 404

        is_pitcher = report_row.get("primary_position") == "P"

        # only care about the correpsonding metrics for player position
        if is_pitcher:
            values = [
                to_nullable_float(metrics.get(field, report_row.get(field)))
                for field in PITCHER_METRIC_FIELDS
            ]
            # update the metrics for this report, with all the stats updated
            update_message = updatePitcherMetrics(report_id, [value for value in values])
        else:
            values = [
                to_nullable_float(metrics.get(field, report_row.get(field)))
                for field in POSITION_METRIC_FIELDS
            ]
            # update the metrics for this report, with all the stats updated
            update_message = updatePositionMetrics(report_id, [value for value in values])

        update_single_grade(report_id)
        updated_report = serialize_report_detail(get_report_detail_row(report_id))
        return jsonify({"message": update_message, "report": updated_report})
    except ValueError as exc:
        return jsonify({"error": f"Invalid metric value: {str(exc)}"}), 400
    except Exception:
        app.logger.exception("Failed to update report")
        return jsonify({"error": "Failed to update report"}), 500

@app.route('/api/reports/<int:report_id>', methods=['DELETE'])
def api_delete_report(report_id):
    conn = None
    cur = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(
            "DELETE FROM ScoutingReport WHERE report_id = %s RETURNING report_id",
            (report_id,),
        )
        deleted = cur.fetchone()
        if not deleted:
            conn.rollback()
            return jsonify({"error": "Report not found"}), 404

        conn.commit()
        return jsonify({"message": "Report deleted successfully", "report_id": report_id})
    except Exception:
        if conn:
            conn.rollback()
        app.logger.exception("Failed to delete report")
        return jsonify({"error": "Failed to delete report"}), 500
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()

@app.route('/api/search')
def api_search():
    try:
        search_query = request.args.get("query", "").strip()
        search_type = request.args.get("type", "player").strip().lower()

        if not search_query:
            return jsonify([])

        # turn search results into json
        results = run_report_search(search_type, search_query)
        return jsonify(results)
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400
    except Exception:
        app.logger.exception("Failed to search reports")
        return jsonify({"error": "Failed to search reports"}), 500



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

        # get the query and the type of search
        search_query = request.form.get('search_query', '').strip()
        search_type = request.form.get('search_type', 'player').strip().lower()
        if search_query:
            try:
                # run the search and get a list of matching reports
                results = run_report_search(search_type, search_query)
            except ValueError:
                flash("Invalid search type")

    return render_template('search.html', results=results, search_query=search_query, search_type=search_type)

if __name__ == '__main__':
    app.run(debug=True)
