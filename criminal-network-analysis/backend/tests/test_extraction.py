from app.ai.nlp_extraction import extract_entities, extract_relationships_hint

SAMPLE_TEXT = (
    "Person A met Person B at Kochi on 12 August. "
    "They used vehicle KL-07-AB-1234 and communicated using phone number 98765-43210. "
    "Person A transferred Rs.50000 to an account linked to Coastal Traders Pvt Ltd."
)


def test_extracts_expected_entity_types():
    entities = extract_entities(SAMPLE_TEXT)
    types_found = {e["type"] for e in entities}
    assert {"PERSON", "VEHICLE", "PHONE", "LOCATION", "DATE", "ORGANIZATION", "FINANCIAL_ENTITY"} <= types_found


def test_organization_not_split_into_spurious_persons():
    """Regression test: 'Coastal Traders Pvt Ltd' was previously split into
    two bogus PERSON matches ('Coastal Traders', 'Pvt Ltd') because the
    PERSON heuristic ran without respecting spans already claimed by the
    more specific ORGANIZATION pattern."""
    entities = extract_entities(SAMPLE_TEXT)
    org_matches = [e["value"] for e in entities if e["type"] == "ORGANIZATION"]
    assert "Coastal Traders Pvt Ltd" in org_matches
    person_values = {e["value"] for e in entities if e["type"] == "PERSON"}
    assert "Coastal Traders" not in person_values
    assert "Pvt Ltd" not in person_values


def test_every_entity_has_confidence_and_source():
    entities = extract_entities(SAMPLE_TEXT)
    assert entities, "expected at least one entity from the sample text"
    for e in entities:
        assert 0 < e["confidence"] <= 1
        assert e["source"]
        assert e["id"].startswith("EXT-")


def test_empty_text_returns_no_entities():
    assert extract_entities("") == []
    assert extract_entities("   ") == []


def test_structural_patterns_score_higher_confidence_than_free_text():
    entities = extract_entities(SAMPLE_TEXT)
    by_type = {e["type"]: e["confidence"] for e in entities}
    assert by_type["PHONE"] > by_type["PERSON"]
    assert by_type["VEHICLE"] > by_type["PERSON"]


def test_relationship_leads_are_labeled_as_potential_not_asserted():
    entities = extract_entities(SAMPLE_TEXT)
    leads = extract_relationships_hint(SAMPLE_TEXT, entities)
    assert leads, "expected at least one relationship lead from the sample text"
    for lead in leads:
        assert lead["label"] == "Potential connection"
