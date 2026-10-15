import json
import os
import sqlite3
from contextlib import closing, contextmanager


@contextmanager
def connect_db(database_path):
    connection = sqlite3.connect(database_path)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    try:
        yield connection
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def initialize_database(database_path, sample_data_dir):
    os.makedirs(os.path.dirname(database_path) or ".", exist_ok=True)
    with closing(sqlite3.connect(database_path)) as db:
        db.row_factory = sqlite3.Row
        db.executescript("""
            CREATE TABLE IF NOT EXISTS roads (
                road_id TEXT PRIMARY KEY, name TEXT NOT NULL, from_node TEXT NOT NULL, to_node TEXT NOT NULL,
                from_lat REAL NOT NULL, from_lon REAL NOT NULL, to_lat REAL NOT NULL, to_lon REAL NOT NULL,
                distance_km REAL NOT NULL CHECK(distance_km > 0), speed_kph REAL NOT NULL CHECK(speed_kph > 0),
                status TEXT NOT NULL CHECK(status IN ('open','blocked','risky','unknown')),
                reason TEXT NOT NULL DEFAULT '', source TEXT NOT NULL, updated_at TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS alerts (
                alert_id TEXT PRIMARY KEY, severity TEXT NOT NULL, affected_area TEXT NOT NULL,
                message TEXT NOT NULL, source TEXT NOT NULL, updated_at TEXT NOT NULL, is_demo INTEGER NOT NULL DEFAULT 1);
            CREATE TABLE IF NOT EXISTS shelters (
                shelter_id TEXT PRIMARY KEY, name TEXT NOT NULL, lat REAL NOT NULL, lon REAL NOT NULL,
                availability TEXT NOT NULL, capacity INTEGER NOT NULL, source TEXT NOT NULL, is_demo INTEGER NOT NULL DEFAULT 1);
        """)
        samples = {
            "roads": ("sample_roads.json", "INSERT INTO roads VALUES (:road_id,:name,:from_node,:to_node,:from_lat,:from_lon,:to_lat,:to_lon,:distance_km,:speed_kph,:status,:reason,:source,:updated_at)"),
            "alerts": ("sample_alerts.json", "INSERT INTO alerts(alert_id,severity,affected_area,message,source,updated_at,is_demo) VALUES (:alert_id,:severity,:affected_area,:message,:source,:updated_at,1)"),
            "shelters": ("sample_shelters.json", "INSERT INTO shelters(shelter_id,name,lat,lon,availability,capacity,source,is_demo) VALUES (:shelter_id,:name,:lat,:lon,:availability,:capacity,:source,1)"),
        }
        for table, (filename, statement) in samples.items():
            if db.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0] == 0:
                with open(os.path.join(sample_data_dir, filename), encoding="utf-8") as sample:
                    key = "roads" if table == "roads" else table
                    db.executemany(statement, json.load(sample)[key])
        db.commit()
