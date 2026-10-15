from backend.route_engine import RouteNotFoundError, calculate_route


def roads():
    return [
        {"road_id":"a","name":"Direct","from_node":"start","to_node":"end","from_lat":0,"from_lon":0,"to_lat":0,"to_lon":1,"distance_km":1,"speed_kph":30,"status":"blocked"},
        {"road_id":"b","name":"North leg","from_node":"start","to_node":"via","from_lat":0,"from_lon":0,"to_lat":1,"to_lon":0,"distance_km":2,"speed_kph":30,"status":"open"},
        {"road_id":"c","name":"East leg","from_node":"via","to_node":"end","from_lat":1,"from_lon":0,"to_lat":0,"to_lon":1,"distance_km":2,"speed_kph":30,"status":"open"},
    ]


def test_route_avoids_blocked_road():
    result = calculate_route(roads(), "start", "end")
    assert result["nodes"] == ["start", "via", "end"]
    assert [road["road_id"] for road in result["roads"]] == ["b", "c"]
    assert result["distance_km"] == 4


def test_no_route_when_all_connections_are_blocked():
    data = roads()
    for road in data:
        road["status"] = "blocked"
    try:
        calculate_route(data, "start", "end")
    except RouteNotFoundError as error:
        assert "No route" in str(error)
    else:
        raise AssertionError("Expected a no-route response")


def test_unknown_road_is_not_described_as_safe():
    data = roads()[1:]
    data[0]["status"] = "unknown"
    result = calculate_route(data, "start", "end")
    assert any("not confirmed safe" in warning for warning in result["warnings"])
