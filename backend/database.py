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
                reason TEXT NOT NULL DEFAULT '', source TEXT NOT NULL, updated_at TEXT NOT NULL,
                region_id TEXT NOT NULL DEFAULT 'pune');
            CREATE TABLE IF NOT EXISTS alerts (
                alert_id TEXT PRIMARY KEY, severity TEXT NOT NULL, affected_area TEXT NOT NULL,
                message TEXT NOT NULL, source TEXT NOT NULL, updated_at TEXT NOT NULL, is_demo INTEGER NOT NULL DEFAULT 1,
                region_id TEXT NOT NULL DEFAULT 'pune');
            CREATE TABLE IF NOT EXISTS shelters (
                shelter_id TEXT PRIMARY KEY, name TEXT NOT NULL, lat REAL NOT NULL, lon REAL NOT NULL,
                availability TEXT NOT NULL, capacity INTEGER NOT NULL, source TEXT NOT NULL, is_demo INTEGER NOT NULL DEFAULT 1,
                region_id TEXT NOT NULL DEFAULT 'pune');
            CREATE TABLE IF NOT EXISTS regions (
                region_id TEXT PRIMARY KEY, state_name TEXT NOT NULL, city_name TEXT NOT NULL,
                center_lat REAL NOT NULL, center_lon REAL NOT NULL, source TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS areas (
                area_id TEXT PRIMARY KEY, region_id TEXT NOT NULL, name TEXT NOT NULL,
                lat REAL NOT NULL, lon REAL NOT NULL, nearest_node TEXT NOT NULL, source TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS hospitals (
                hospital_id TEXT PRIMARY KEY, region_id TEXT NOT NULL, name TEXT NOT NULL,
                nearest_node TEXT NOT NULL, lat REAL NOT NULL, lon REAL NOT NULL,
                availability TEXT NOT NULL, source TEXT NOT NULL);
        """)
        for table in ("roads", "alerts", "shelters"):
            columns = {row["name"] for row in db.execute(f"PRAGMA table_info({table})")}
            if "region_id" not in columns:
                db.execute(f"ALTER TABLE {table} ADD COLUMN region_id TEXT NOT NULL DEFAULT 'pune'")

        with open(os.path.join(sample_data_dir, "sample_regions.json"), encoding="utf-8") as sample:
            regional_data = json.load(sample)
        db.executemany(
            "INSERT OR IGNORE INTO regions VALUES (:region_id,:state_name,:city_name,:center_lat,:center_lon,:source)",
            regional_data["regions"],
        )
        samples = {
            "roads": ("sample_roads.json", "INSERT OR IGNORE INTO roads(road_id,name,from_node,to_node,from_lat,from_lon,to_lat,to_lon,distance_km,speed_kph,status,reason,source,updated_at,region_id) VALUES (:road_id,:name,:from_node,:to_node,:from_lat,:from_lon,:to_lat,:to_lon,:distance_km,:speed_kph,:status,:reason,:source,:updated_at,:region_id)"),
            "alerts": ("sample_alerts.json", "INSERT OR IGNORE INTO alerts(alert_id,severity,affected_area,message,source,updated_at,is_demo,region_id) VALUES (:alert_id,:severity,:affected_area,:message,:source,:updated_at,1,:region_id)"),
            "shelters": ("sample_shelters.json", "INSERT OR IGNORE INTO shelters(shelter_id,name,lat,lon,availability,capacity,source,is_demo,region_id) VALUES (:shelter_id,:name,:lat,:lon,:availability,:capacity,:source,1,:region_id)"),
        }
        for table, (filename, statement) in samples.items():
            if db.execute(f"SELECT COUNT(*) FROM {table} WHERE region_id='pune'").fetchone()[0] == 0:
                with open(os.path.join(sample_data_dir, filename), encoding="utf-8") as sample:
                    key = "roads" if table == "roads" else table
                    records = [{**record, "region_id": "pune"} for record in json.load(sample)[key]]
                    db.executemany(statement, records)
        for network in regional_data["networks"]:
            for table, (_, statement) in samples.items():
                records = [{**record, "region_id": network["region_id"]} for record in network[table]]
                db.executemany(statement, records)

        with open(os.path.join(sample_data_dir, "sample_patna_roads.json"), encoding="utf-8") as sample:
            patna_roads = [{**road, "region_id": "bihar"} for road in json.load(sample)["roads"]]
        db.executemany(samples["roads"][1], patna_roads)
        for filename, key, table in (
            ("sample_patna_areas.json", "areas", "areas"),
            ("sample_hospitals.json", "hospitals", "hospitals"),
        ):
            with open(os.path.join(sample_data_dir, filename), encoding="utf-8") as sample:
                records = json.load(sample)[key]
            columns = ",".join(records[0])
            values = ",".join(f":{column}" for column in records[0])
            db.executemany(f"INSERT OR IGNORE INTO {table} ({columns}) VALUES ({values})", records)
        db.commit()
