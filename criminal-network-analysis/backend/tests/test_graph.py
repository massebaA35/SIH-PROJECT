def test_case_graph_renders(client, auth_headers):
    case_id = client.get("/api/cases?page_size=1", headers=auth_headers).json()["items"][0]["id"]
    response = client.get(f"/api/graph/case/{case_id}", headers=auth_headers)
    assert response.status_code == 200
    body = response.json()
    assert body["node_count"] > 0
    assert body["edge_count"] > 0
    assert len(body["nodes"]) == body["node_count"]
    assert len(body["edges"]) == body["edge_count"]
    assert "communities" in body


def test_case_graph_not_found(client, auth_headers):
    response = client.get("/api/graph/case/CASE-9999", headers=auth_headers)
    assert response.status_code == 404


def test_entity_graph_neighborhood(client, auth_headers):
    response = client.get("/api/graph/entity/PERSON-101?depth=1", headers=auth_headers)
    assert response.status_code == 200
    body = response.json()
    assert any(node["data"]["id"] == "PERSON-101" for node in body["nodes"])


def test_centrality_calculation_returns_all_metrics():
    import networkx as nx
    from app.analytics.centrality import compute_centrality
    g = nx.MultiGraph()
    g.add_edge("A", "B", relation_type="KNOWS")
    g.add_edge("B", "C", relation_type="KNOWS")
    g.add_edge("C", "A", relation_type="KNOWS")
    metrics = compute_centrality(g)
    assert set(metrics.keys()) == {"A", "B", "C"}
    for node_metrics in metrics.values():
        for key in ("degree_centrality", "betweenness_centrality", "closeness_centrality", "pagerank"):
            assert key in node_metrics


def test_community_detection_finds_separate_clusters():
    import networkx as nx
    from app.analytics.community import detect_communities
    g = nx.MultiGraph()
    # two dense triangles connected by a single bridge edge
    g.add_edges_from([("A", "B"), ("B", "C"), ("C", "A")])
    g.add_edges_from([("D", "E"), ("E", "F"), ("F", "D")])
    g.add_edge("C", "D")
    mapping, summary = detect_communities(g)
    assert mapping["A"] == mapping["B"] == mapping["C"]
    assert mapping["D"] == mapping["E"] == mapping["F"]
    assert mapping["A"] != mapping["D"]
    assert len(summary) == 2


def test_bridge_entity_identification():
    import networkx as nx
    from app.analytics.centrality import identify_bridge_entities
    g = nx.MultiGraph()
    g.add_edges_from([("A", "B"), ("B", "C"), ("C", "A")])
    g.add_edges_from([("D", "E"), ("E", "F"), ("F", "D")])
    g.add_edge("C", "D")
    communities = {"A": 0, "B": 0, "C": 0, "D": 1, "E": 1, "F": 1}
    bridges = identify_bridge_entities(g, communities)
    assert set(bridges) == {"C", "D"}
