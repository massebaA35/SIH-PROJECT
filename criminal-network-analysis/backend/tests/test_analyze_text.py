def test_analyze_text_returns_rejected_candidates_and_summary(client, auth_headers):
    text = (
        "Officers from Police Station in Central City investigated a Crime Category "
        "case involving Organized Theft near the Industrial Area, linked to Metro Logistics."
    )
    response = client.post("/api/analyze/text", json={"text": text}, headers=auth_headers)
    assert response.status_code == 200
    body = response.json()

    person_values = {e["value"] for e in body["entities"] if e["type"] == "PERSON"}
    assert not person_values, "no PERSON entities should be produced from this label/location-only text"

    assert body["rejected_candidates"], "the field-label/location phrases should show up as rejected PERSON candidates"

    summary = body["summary"]
    assert summary["entities_extracted"] == len(body["entities"])
    assert summary["rejected_candidates"] == len(body["rejected_candidates"])
    check_labels = {c["label"]: c["passed"] for c in summary["checks"]}
    assert check_labels["No field labels classified as PERSON"] is True


def test_analyze_text_requires_authentication(client):
    response = client.post("/api/analyze/text", json={"text": "Person A met Person B."})
    assert response.status_code == 401
