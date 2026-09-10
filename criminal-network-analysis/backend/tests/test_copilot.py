def test_copilot_response_has_structured_fields(client, auth_headers):
    case_id = client.get("/api/cases?page_size=1", headers=auth_headers).json()["items"][0]["id"]
    response = client.post("/api/assistant/ask", json={"question": f"What entities are connected to {case_id}?"}, headers=auth_headers)
    assert response.status_code == 200
    body = response.json()
    for field in ("answer", "reasoning", "related_entities", "related_cases", "source_records", "interpretation", "supporting", "disclaimer"):
        assert field in body
    assert isinstance(body["reasoning"], list)
    assert isinstance(body["related_entities"], list)
    assert all("id" in e and "label" in e for e in body["related_entities"])


def test_copilot_finds_hidden_link_between_connected_entities(client, auth_headers, seeded_database):
    edge = seeded_database["relationships"][0]
    response = client.post("/api/assistant/ask", json={
        "question": f"Find hidden links between {edge['source_id']} and {edge['target_id']}",
    }, headers=auth_headers)
    assert response.status_code == 200
    body = response.json()
    assert edge["source_id"] in body["answer"] or any(e["id"] == edge["source_id"] for e in body["related_entities"])
    assert "verification" in body["interpretation"].lower() or "verification" in body["answer"].lower()


def test_copilot_hidden_link_no_connection_says_so(client, auth_headers):
    response = client.post("/api/assistant/ask", json={"question": "Find hidden links between PERSON-9998 and PERSON-9999"}, headers=auth_headers)
    body = response.json()
    assert "No hidden link" in body["answer"] or "No supporting information" in body["answer"]


def test_copilot_never_declares_guilt(client, auth_headers):
    entity_id = client.get("/api/entities?page_size=1&type=PERSON", headers=auth_headers).json()["items"][0]["id"]
    response = client.post("/api/assistant/ask", json={"question": f"Show the strongest connections of {entity_id}"}, headers=auth_headers)
    body = response.json()
    forbidden = ["is a criminal", "is guilty", "will commit a crime"]
    combined_text = (body["answer"] + " " + body.get("interpretation", "")).lower()
    for phrase in forbidden:
        assert phrase not in combined_text
