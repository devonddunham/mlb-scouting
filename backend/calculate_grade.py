# an advanced function

import psycopg2
import pandas as pd
import numpy as np
from database import get_db_connection

def calculate_z_score_grade(val, mean, std, higher_is_better=True):
    
    # using standard mlb scale 20-80 with 50 as average, 10 points per std deviation

    if pd.isna(val) or std == 0:
        return 50 # Default to average if missing data
    
    z_score = (val - mean) / std
    
    if higher_is_better:
        grade = 50 + (z_score * 10)
    else:
        grade = 50 - (z_score * 10) # flip it for stats like whiff for pitchers where its better to be lower
        
    # clamp the grade between 20 and 80 (the MLB scale limits)
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
    
    # get column names from the cursor description
    columns = [desc[0] for desc in cur.description]
    
    # load into Pandas DataFrame manually
    df = pd.DataFrame(data, columns=columns)
    
    # seperate pitchers and hitters
    pitchers = df[df['primary_position'] == 'P'].copy()
    hitters = df[df['primary_position'] != 'P'].copy()

    updates = []

    # GRADE PITCHERS
    if not pitchers.empty:
        # get the means and stds for each metric to calculate z-scores
        p_means = pitchers.mean(numeric_only=True)
        p_stds = pitchers.std(numeric_only=True)


        for index, row in pitchers.iterrows():
            # higher is better for these
            velo_grade = calculate_z_score_grade(row['four_seam_velocity'], p_means['four_seam_velocity'], p_stds['four_seam_velocity'])
            whiff_grade = calculate_z_score_grade(row['whiff_percentage'], p_means['whiff_percentage'], p_stds['whiff_percentage'])
            k_grade = calculate_z_score_grade(row['k_percentage'], p_means['k_percentage'], p_stds['k_percentage'])
            
            # lower is better for these
            hard_hit_grade = calculate_z_score_grade(row['hard_hit_percentage'], p_means['hard_hit_percentage'], p_stds['hard_hit_percentage'], False)
            bb_grade = calculate_z_score_grade(row['bb_percentage'], p_means['bb_percentage'], p_stds['bb_percentage'], False)

            # we can change the weights later if we want
            final_grade = (velo_grade * 0.2) + (whiff_grade * 0.25) + (k_grade * 0.25) + (hard_hit_grade * 0.2) + (bb_grade * 0.1)
            updates.append((int(final_grade), int(row['report_id'])))

    # GRADE HITTERS
    if not hitters.empty:
        # get the means and stds for each metric to calculate z-scores
        h_means = hitters.mean(numeric_only=True)
        h_stds = hitters.std(numeric_only=True)

        for index, row in hitters.iterrows():
            # higher is better for theser
            xwoba_grade = calculate_z_score_grade(row['xwoba'], h_means['xwoba'], h_stds['xwoba'])
            hard_hit_grade = calculate_z_score_grade(row['hard_hit_percentage'], h_means['hard_hit_percentage'], h_stds['hard_hit_percentage'])
            
            # lower is better for these
            whiff_grade = calculate_z_score_grade(row['whiff_percentage'], h_means['whiff_percentage'], h_stds['whiff_percentage'], False)
            chase_grade = calculate_z_score_grade(row['out_zone_swing_percentage'], h_means['out_zone_swing_percentage'], h_stds['out_zone_swing_percentage'], False)

            # we can change the weights later if we want
            final_grade = (xwoba_grade * 0.4) + (hard_hit_grade * 0.3) + (whiff_grade * 0.15) + (chase_grade * 0.15)
            updates.append((int(final_grade), int(row['report_id'])))

    # UPDATE DATABASE
    try:
        cur.executemany("""
            UPDATE ScoutingReport 
            SET overall_grade = %s 
            WHERE report_id = %s
        """, updates)
    
        conn.commit()
        print(f"Successfully calculated and updated {len(updates)} scouting grades.")
    except Exception as e:
        conn.rollback()
        print(f"Error updating database: {e}")
    finally:
        cur.close()
        conn.close()

if __name__ == "__main__":
    update_all_grades()