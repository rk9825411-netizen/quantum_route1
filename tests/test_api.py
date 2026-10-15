from pathlib import Path

from app import create_app


def make_client(tmp_path):
    data_dir = Path(__file__).parents[1] / "data"
    app = create_app({"TESTING": True, "DATABASE_PATH": str(tmp_path / "test.sqlite3"), "SAMPLE_DATA_DIR": str(data_dir), "ADMIN_TOKEN": "test-token"})
    return app.test_client()


def test_seeded_api_and_route(tmp_path):
    client = make_client(tmp_path)
    assert client.get("/api/roads").status_code == 200
    response = client.post("/api/route/calculate", json={"start": "old_market", "destination": "south_hub"})
    assert response.status_code == 200
    assert "south_hub" in response.get_json()["nodes"]


def test_admin_requires_token_and_updates_database(tmp_path):
    client = make_client(tmp_path)
    payload = {"road_id": "R-01", "status": "blocked", "reason": "Test closure"}
    assert client.post("/api/admin/roads/status", json=payload).status_code == 401
    response = client.post("/api/admin/roads/status", json=payload, headers={"X-Admin-Token": "test-token"})
    assert response.status_code == 200
    roads = client.get("/api/roads").get_json()["roads"]
    assert next(road for road in roads if road["road_id"] == "R-01")["status"] == "blocked"


def test_route_request_validates_locations(tmp_path):
    response = make_client(tmp_path).post("/api/route/calculate", json={"start": "", "destination": "north_gate"})
    assert response.status_code == 400


def test_admin_rejects_non_string_status(tmp_path):
    response = make_client(tmp_path).post(
        "/api/admin/roads/status",
        json={"road_id": "R-01", "status": []},
        headers={"X-Admin-Token": "test-token"},
    )
    assert response.status_code == 400
