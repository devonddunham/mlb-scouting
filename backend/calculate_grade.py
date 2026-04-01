import psycopg2
import pandas as pd
from database import get_db_connection

def calculate_z_score_grade(val, mean, std, higher_is_better=True):
    
    if pd.isna(val) or val is None or std == 0:
        return 50 # default to average if missing data
    
    z_score = (val - mean) / std
    
    # flip if low is good like whiff for batters or hard hit for pitchers
    if higher_is_better:
        grade = 50 + (z_score * 10)
    else:
        grade = 50 - (z_score * 10) 
        
    # clamp the grade between 20 and 80
    # mlb scale
    return max(20, min(80, grade))

def update_all_grades():
    conn = get_db_connection()
    cur = conn.cursor()
    
    query = """
        SELECT p.primary_position, pm.* FROM ScoutingReport r
        JOIN Player p ON r.player_id = p.player_id
        JOIN PerformanceMetrics pm ON r.report_id = pm.report_id
    """
    cur.execute(query)
    data = cur.fetchall()
    
    columns = [desc[0] for desc in cur.description]
    df = pd.DataFrame(data, columns=columns)
    
    pitchers = df[df['primary_position'] == 'P'].copy()
    hitters = df[df['primary_position'] != 'P'].copy()

    # load the true MLB Averages CSV
    try:
        baselines = pd.read_csv('data/mlb_2025_league_averages.csv')
        
        # convert CSV into a dictionary -> dict[player_type][metric_name] = (mean, std) so its faster
        # nested dictionary with two main keys Hitter and Pitcher
        # then each of those is a dictionary of metric_name to (mean, std_dev) tuple
        b_dict = {'Hitter': {}, 'Pitcher': {}}
        for index, row in baselines.iterrows():
            b_dict[row['player_type']][row['metric_name']] = (row['mean'], row['std_dev'])
            
    except FileNotFoundError:
        print("Error: mlb_2025_league_averages.csv not found.")
        return

    # get the baseline mean and std for a given player type and metric
    def get_baseline(ptype, metric):
        return b_dict.get(ptype, {}).get(metric, (0, 0))

    # list of tuples (grade, report_id)
    updates = []

    # GRADE PITCHERS
    if not pitchers.empty:
        for index, row in pitchers.iterrows():
            m_velo, s_velo = get_baseline('Pitcher', 'four_seam_velocity')
            m_whiff, s_whiff = get_baseline('Pitcher', 'whiff_percentage')
            m_k, s_k = get_baseline('Pitcher', 'k_percentage')
            m_hard, s_hard = get_baseline('Pitcher', 'hard_hit_percentage')
            m_bb, s_bb = get_baseline('Pitcher', 'bb_percentage')

            # higher is better for these for pitchers
            velo_grade = calculate_z_score_grade(row.get('four_seam_velocity'), m_velo, s_velo)
            whiff_grade = calculate_z_score_grade(row.get('whiff_percentage'), m_whiff, s_whiff)
            k_grade = calculate_z_score_grade(row.get('k_percentage'), m_k, s_k)
            
            # lower is better for these for pitchers
            hard_hit_grade = calculate_z_score_grade(row.get('hard_hit_percentage'), m_hard, s_hard, False)
            bb_grade = calculate_z_score_grade(row.get('bb_percentage'), m_bb, s_bb, False)

            # we can change these weights later
            final_grade = (velo_grade * 0.2) + (whiff_grade * 0.25) + (k_grade * 0.25) + (hard_hit_grade * 0.2) + (bb_grade * 0.1)
            
            updates.append((int(final_grade), int(row['report_id'])))

    # GRADE HITTERS
    if not hitters.empty:
        for index, row in hitters.iterrows():
            m_xwoba, s_xwoba = get_baseline('Hitter', 'xwoba')
            m_hard, s_hard = get_baseline('Hitter', 'hard_hit_percentage')
            m_whiff, s_whiff = get_baseline('Hitter', 'whiff_percentage')
            m_chase, s_chase = get_baseline('Hitter', 'out_zone_swing_percentage')

            # higher is better for these for hitters
            xwoba_grade = calculate_z_score_grade(row.get('xwoba'), m_xwoba, s_xwoba)
            hard_hit_grade = calculate_z_score_grade(row.get('hard_hit_percentage'), m_hard, s_hard)
            
            # lower is better for these for hitters
            whiff_grade = calculate_z_score_grade(row.get('whiff_percentage'), m_whiff, s_whiff, False)
            chase_grade = calculate_z_score_grade(row.get('out_zone_swing_percentage'), m_chase, s_chase, False)

            # we can change these weights later
            final_grade = (xwoba_grade * 0.4) + (hard_hit_grade * 0.3) + (whiff_grade * 0.15) + (chase_grade * 0.15)
            
            updates.append((int(final_grade), int(row['report_id'])))

    # update the database with the new grades
    if updates:
        try:
            cur.executemany("""
                UPDATE ScoutingReport 
                SET overall_grade = %s 
                WHERE report_id = %s
            """, updates)
        
            conn.commit()
            print(f"Success, Calculated and updated {len(updates)} scouting grades using MLB 2025 baselines.")
        except Exception as e:
            conn.rollback()
            print(f"Error updating database: {e}")
        finally:
            cur.close()
            conn.close()
    else:
        print("No players found to update.")

def update_single_grade(report_id):
    conn = get_db_connection()
    cur = conn.cursor()
    
    query = """
        SELECT p.primary_position, pm.* FROM ScoutingReport r
        JOIN Player p ON r.player_id = p.player_id
        JOIN PerformanceMetrics pm ON r.report_id = pm.report_id
    """
    cur.execute(query)
    data = cur.fetchall()
    
    columns = [desc[0] for desc in cur.description]
    df = pd.DataFrame(data, columns=columns)
    
    # only find the report we need
    target_row = df[df['report_id'] == int(report_id)]
    
    if target_row.empty:
        print(f"Error: Report ID {report_id} not found.")
        return
        
    # get the row as a series
    row = target_row.iloc[0]

    # load the true MLB Averages CSV
    try:
        baselines = pd.read_csv('data/mlb_2025_league_averages.csv')
        b_dict = {'Hitter': {}, 'Pitcher': {}}
        for index, b_row in baselines.iterrows():
            b_dict[b_row['player_type']][b_row['metric_name']] = (b_row['mean'], b_row['std_dev'])
    except FileNotFoundError:
        print("Error: mlb_2025_league_averages.csv not found.")
        return

    def get_baseline(ptype, metric):
        return b_dict.get(ptype, {}).get(metric, (0, 0))

    update = None

    # we only need the one row
    if row['primary_position'] == 'P':
        # pitcher math
        m_velo, s_velo = get_baseline('Pitcher', 'four_seam_velocity')
        m_whiff, s_whiff = get_baseline('Pitcher', 'whiff_percentage')
        m_k, s_k = get_baseline('Pitcher', 'k_percentage')
        m_hard, s_hard = get_baseline('Pitcher', 'hard_hit_percentage')
        m_bb, s_bb = get_baseline('Pitcher', 'bb_percentage')

        velo_grade = calculate_z_score_grade(row.get('four_seam_velocity'), m_velo, s_velo)
        whiff_grade = calculate_z_score_grade(row.get('whiff_percentage'), m_whiff, s_whiff)
        k_grade = calculate_z_score_grade(row.get('k_percentage'), m_k, s_k)
        hard_hit_grade = calculate_z_score_grade(row.get('hard_hit_percentage'), m_hard, s_hard, False)
        bb_grade = calculate_z_score_grade(row.get('bb_percentage'), m_bb, s_bb, False)

        final_grade = (velo_grade * 0.2) + (whiff_grade * 0.25) + (k_grade * 0.25) + (hard_hit_grade * 0.2) + (bb_grade * 0.1)
        update = (int(final_grade), int(report_id))

    else:
        # hitter Math
        m_xwoba, s_xwoba = get_baseline('Hitter', 'xwoba')
        m_hard, s_hard = get_baseline('Hitter', 'hard_hit_percentage')
        m_whiff, s_whiff = get_baseline('Hitter', 'whiff_percentage')
        m_chase, s_chase = get_baseline('Hitter', 'out_zone_swing_percentage')

        xwoba_grade = calculate_z_score_grade(row.get('xwoba'), m_xwoba, s_xwoba)
        hard_hit_grade = calculate_z_score_grade(row.get('hard_hit_percentage'), m_hard, s_hard)
        whiff_grade = calculate_z_score_grade(row.get('whiff_percentage'), m_whiff, s_whiff, False)
        chase_grade = calculate_z_score_grade(row.get('out_zone_swing_percentage'), m_chase, s_chase, False)

        final_grade = (xwoba_grade * 0.4) + (hard_hit_grade * 0.3) + (whiff_grade * 0.15) + (chase_grade * 0.15)
        update = (int(final_grade), int(report_id))

    # update DB
    if update:
        try:
            cur.execute("""
                UPDATE ScoutingReport 
                SET overall_grade = %s 
                WHERE report_id = %s
            """, update)
            conn.commit()
            print(f"Success, updated scouting grade for report_id {update[1]}")
        except Exception as e:
            conn.rollback()
            print(f"Error updating database: {e}")
        finally:
            cur.close()
            conn.close()

if __name__ == "__main__":
    update_all_grades()