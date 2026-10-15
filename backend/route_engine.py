import networkx as nx

STATUS_PENALTIES = {"open": 1.0, "risky": 2.5, "unknown": 1.4}


class RouteNotFoundError(ValueError):
    pass


def calculate_route(roads, start, destination):
    graph = nx.Graph()
    coordinates = {}
    for road in roads:
        left, right = road["from_node"], road["to_node"]
        coordinates[left] = [road["from_lat"], road["from_lon"]]
        coordinates[right] = [road["to_lat"], road["to_lon"]]
        graph.add_nodes_from((left, right))
        if road["status"] != "blocked":
            graph.add_edge(left, right, weight=road["distance_km"] * STATUS_PENALTIES[road["status"]],
                           road_id=road["road_id"], name=road["name"], distance_km=road["distance_km"],
                           speed_kph=road["speed_kph"], status=road["status"])
    if start not in graph or destination not in graph:
        raise ValueError("Starting point or destination is not in the demo road network.")
    try:
        nodes = nx.shortest_path(graph, start, destination, weight="weight")
    except nx.NetworkXNoPath as error:
        raise RouteNotFoundError("No route is available without using blocked roads.") from error
    edges = [graph[left][right] for left, right in zip(nodes, nodes[1:])]
    statuses = {edge["status"] for edge in edges}
    warnings = []
    if "unknown" in statuses:
        warnings.append("This route includes roads with unknown status; they are not confirmed safe.")
    if "risky" in statuses:
        warnings.append("This route includes potentially risky roads.")
    if any(road["status"] in ("unknown", "risky") for road in roads):
        warnings.append("Road-status information is demo/manual and may be incomplete or outdated.")
    return {
        "nodes": nodes,
        "coordinates": [coordinates[node] for node in nodes],
        "roads": [{key: edge[key] for key in ("road_id", "name", "status")} for edge in edges],
        "distance_km": round(sum(edge["distance_km"] for edge in edges), 2),
        "estimated_minutes": round(sum(edge["distance_km"] / edge["speed_kph"] * 60 for edge in edges)),
        "warnings": list(dict.fromkeys(warnings)),
        "selection_reason": "Shortest weighted route found after excluding blocked roads and penalizing risky and unknown roads.",
    }
