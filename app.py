import os
from datetime import datetime, timezone

import networkx as nx
from dotenv import load_dotenv
from flask import Flask, jsonify, render_template, request

from backend.database import connect_db, initialize_database
from backend.route_engine import RouteNotFoundError, calculate_route

load_dotenv()


def create_app(test_config=None):
    app = Flask(__name__)
    app.config.from_mapping(
        DATABASE_PATH=os.path.join(app.instance_path, "quantumroute.sqlite3"),
        SAMPLE_DATA_DIR=os.path.join(app.root_path, "data"),
        ADMIN_TOKEN=os.environ.get("QUANTUMROUTE_ADMIN_TOKEN", "demo-admin-token"),
    )
    if test_config:
        app.config.update(test_config)
    os.makedirs(app.instance_path, exist_ok=True)
    initialize_database(app.config["DATABASE_PATH"], app.config["SAMPLE_DATA_DIR"])

    @app.get("/")
    def index():
        return render_template("index.html")

    @app.get("/api/roads")
    def roads():
        with connect_db(app.config["DATABASE_PATH"]) as db:
            items = [dict(row) for row in db.execute("SELECT * FROM roads ORDER BY road_id")]
        return jsonify(roads=items, data_mode="demo/manual")

    @app.get("/api/locations")
    def locations():
        with connect_db(app.config["DATABASE_PATH"]) as db:
            rows = db.execute("SELECT * FROM roads").fetchall()
        nodes = {}
        for row in rows:
            for side in ("from", "to"):
                node = row[f"{side}_node"]
                nodes[node] = {"id": node, "name": node.replace("_", " ").title(), "lat": row[f"{side}_lat"], "lon": row[f"{side}_lon"]}
        return jsonify(locations=list(nodes.values()))

    @app.get("/api/alerts")
    def alerts():
        with connect_db(app.config["DATABASE_PATH"]) as db:
            rows = [dict(row) for row in db.execute("SELECT * FROM alerts ORDER BY updated_at DESC")]
        return jsonify(alerts=rows)

    @app.get("/api/shelters")
    def shelters():
        with connect_db(app.config["DATABASE_PATH"]) as db:
            rows = [dict(row) for row in db.execute("SELECT * FROM shelters ORDER BY name")]
        return jsonify(shelters=rows)

    @app.post("/api/route/calculate")
    def route():
        payload = request.get_json(silent=True) or {}
        start, destination = payload.get("start"), payload.get("destination")
        if not isinstance(start, str) or not isinstance(destination, str) or not start or not destination:
            return jsonify(error="Choose both a starting point and a destination."), 400
        if start == destination:
            return jsonify(error="Starting point and destination must be different."), 400
        with connect_db(app.config["DATABASE_PATH"]) as db:
            roads_data = [dict(row) for row in db.execute("SELECT * FROM roads")]
        try:
            return jsonify(calculate_route(roads_data, start, destination))
        except RouteNotFoundError as error:
            return jsonify(error=str(error)), 404
        except (nx.NodeNotFound, ValueError) as error:
            return jsonify(error=str(error)), 400

    @app.post("/api/admin/roads/status")
    def update_status():
        if request.headers.get("X-Admin-Token") != app.config["ADMIN_TOKEN"]:
            return jsonify(error="Admin authorization required."), 401
        payload = request.get_json(silent=True) or {}
        road_id, status = payload.get("road_id"), payload.get("status")
        reason, source = payload.get("reason", ""), payload.get("source", "Manual demo update")
        if not isinstance(road_id, str) or not road_id.strip():
            return jsonify(error="A road ID is required."), 400
        if not isinstance(status, str) or status not in {"open", "blocked", "risky", "unknown"}:
            return jsonify(error="Status must be open, blocked, risky, or unknown."), 400
        if not isinstance(reason, str) or len(reason) > 240 or not isinstance(source, str) or not source.strip() or len(source) > 120:
            return jsonify(error="Reason or data source is invalid or too long."), 400
        with connect_db(app.config["DATABASE_PATH"]) as db:
            cursor = db.execute(
                "UPDATE roads SET status=?, reason=?, source=?, updated_at=? WHERE road_id=?",
                (status, reason.strip(), source.strip(), datetime.now(timezone.utc).isoformat(), road_id.strip()),
            )
            if not cursor.rowcount:
                return jsonify(error="Road not found."), 404
            row = dict(db.execute("SELECT * FROM roads WHERE road_id=?", (road_id.strip(),)).fetchone())
        return jsonify(road=row)

    return app


app = create_app()

if __name__ == "__main__":
    app.run(debug=os.environ.get("FLASK_DEBUG", "0") == "1")
