import json
import sqlite3
from .config import DB_PATH

def connect():
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    return con

def initialize():
    with connect() as con:
        con.execute("""CREATE TABLE IF NOT EXISTS advisory_history (
          id INTEGER PRIMARY KEY, timestamp TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP, location TEXT, crop TEXT,
          growth_stage TEXT, soil_n REAL, soil_p REAL, soil_k REAL, soil_ph REAL, weather_json TEXT,
          predicted_crop TEXT, confidence REAL, selected_crop_score REAL, selected_crop_rank INTEGER,
          irrigation TEXT, pest_risk TEXT, final_advice TEXT, data_source_status TEXT, payload_json TEXT)""")
        columns = {row[1] for row in con.execute("PRAGMA table_info(advisory_history)")}
        if "selected_crop_score" not in columns:
            con.execute("ALTER TABLE advisory_history ADD COLUMN selected_crop_score REAL")
        if "selected_crop_rank" not in columns:
            con.execute("ALTER TABLE advisory_history ADD COLUMN selected_crop_rank INTEGER")

def save(result):
    c, soil, weather = result["context"], result["context"]["soil"], result["context"]["weather"]
    pred = result.get("crop_suitability") or {}
    with connect() as con:
        cur = con.execute("""INSERT INTO advisory_history(location,crop,growth_stage,soil_n,soil_p,soil_k,soil_ph,weather_json,predicted_crop,confidence,selected_crop_score,selected_crop_rank,irrigation,pest_risk,final_advice,data_source_status,payload_json)
        VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""", (c["location"], c["crop"], c["growth_stage"], soil["nitrogen"], soil["phosphorus"], soil["potassium"], soil["ph"], json.dumps(weather), pred.get("crop"), pred.get("confidence"), pred.get("selected_crop_score"), pred.get("selected_crop_rank"), result["irrigation"]["action"], result["pest_risk"]["level"], result["final_advice"], weather.get("status"), json.dumps(result)))
        return cur.lastrowid

def history(limit=200):
    with connect() as con:
        return con.execute("SELECT * FROM advisory_history ORDER BY timestamp DESC LIMIT ?", (limit,)).fetchall()

def get_record(record_id):
    with connect() as con:
        return con.execute("SELECT * FROM advisory_history WHERE id=?", (record_id,)).fetchone()
