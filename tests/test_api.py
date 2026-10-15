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


def test_regions_are_listed_and_roads_are_filtered(tmp_path):
    client = make_client(tmp_path)
    regions = client.get("/api/regions").get_json()["regions"]
    assert {(region["state_name"], region["city_name"]) for region in regions} == {
        ("Maharashtra", "Pune"),
        ("Bihar", "Patna"),
        ("Uttar Pradesh", "Lucknow"),
        ("West Bengal", "Kolkata"),
    }
    roads = client.get("/api/roads?region_id=bihar").get_json()["roads"]
    assert roads
    assert all(road["region_id"] == "bihar" for road in roads)


def test_route_is_limited_to_selected_region(tmp_path):
    client = make_client(tmp_path)
    response = client.post("/api/route/calculate", json={
        "region_id": "bihar",
        "start": "patna_central",
        "destination": "patna_south",
    })
    assert response.status_code == 200
    assert all(road["road_id"].startswith("BR-") for road in response.get_json()["roads"])

    cross_region = client.post("/api/route/calculate", json={
        "region_id": "bihar",
        "start": "lucknow_central",
        "destination": "patna_south",
    })
    assert cross_region.status_code == 400


def test_patna_areas_and_hospital_routes_are_ranked(tmp_path):
    client = make_client(tmp_path)
    locations = client.get("/api/locations?region_id=bihar").get_json()["locations"]
    assert len(locations) >= 14
    assert any(location["name"] == "Kankarbagh" for location in locations)

    response = client.get("/api/hospitals/routes?region_id=bihar&start=patna_junction")
    assert response.status_code == 200
    hospitals = response.get_json()["hospitals"]
    assert len(hospitals) == 6
    distances = [entry["route"]["distance_km"] for entry in hospitals]
    assert distances == sorted(distances)
    assert hospitals[0]["hospital"]["name"].startswith("Demo Hospital")
    assert all(road["status"] != "blocked" for entry in hospitals for road in entry["route"]["roads"])


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
