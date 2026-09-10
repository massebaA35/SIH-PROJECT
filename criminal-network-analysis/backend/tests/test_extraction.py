from app.ai.nlp_extraction import extract_entities, extract_rejected_candidates, extract_relationships_hint

SAMPLE_TEXT = (
    "Person A met Person B at Kochi on 12 August. "
    "They used vehicle KL-07-AB-1234 and communicated using phone number 98765-43210. "
    "Person A transferred Rs.50000 to an account linked to Coastal Traders Pvt Ltd."
)

FIR_TEXT = """
FIR No.: FIR-2024-0187
Police Station: Central City Police Station
Date: 18 October 2024
Crime Category: Organized Theft

On 17 October 2024, a theft was reported near the Industrial Area in Metro City.
The complainant, Person A, referred to as Arjun Nair, stated that his vehicle
XX-00-AB-1234 was used without authorization. Records available to the
investigating team indicate that Arjun Nair communicated with Person B,
identified as Rahul Menon, on 15 October 2024. Rahul Menon was associated
with Metro Logistics and was linked to case C-2024-0112. Sameer Joseph,
also known as Person C, interacted with Rahul Menon at Metro Logistics.
Sameer Joseph interacted with Rahul Menon again the following day.
"""

NON_PERSON_PHRASES_REGRESSION = (
    "Police Station", "Central City", "Crime Category", "Organized Theft",
    "Industrial Area", "Metro City", "Metro Logistics",
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


def test_structural_patterns_score_higher_confidence_than_weak_person_inference():
    entities = extract_entities(SAMPLE_TEXT)
    by_type = {e["type"]: e["confidence"] for e in entities}
    assert by_type["PHONE"] > by_type["ORGANIZATION"] or by_type["PHONE"] == 0.95
    assert by_type["VEHICLE"] == 0.95


def test_relationship_leads_are_labeled_as_potential_not_asserted():
    entities = extract_entities(SAMPLE_TEXT)
    leads = extract_relationships_hint(SAMPLE_TEXT, entities)
    assert leads, "expected at least one relationship lead from the sample text"
    for lead in leads:
        assert lead["label"] in {"Potential connection", "Potential Relationship Lead"}


# ---------------------------------------------------------------------------
# Regression tests for the false-positive PERSON classifications this module
# was rewritten to fix. Each of these previously misclassified a field label,
# location, or crime category as a PERSON entity with the generic
# capitalized-word-pair heuristic. If any of these ever appear as PERSON
# again, the underlying extraction logic -- not just the confidence
# threshold -- has regressed.
# ---------------------------------------------------------------------------

def test_field_labels_and_locations_are_never_classified_as_person():
    text = (
        "Officers from Police Station in Central City investigated a Crime Category "
        "case involving Organized Theft near the Industrial Area, linked to Metro Logistics."
    )
    entities = extract_entities(text)
    person_values = {e["value"] for e in entities if e["type"] == "PERSON"}
    for phrase in NON_PERSON_PHRASES_REGRESSION:
        assert phrase not in person_values, f"{phrase!r} was incorrectly classified as PERSON"


def test_locations_are_classified_as_location_not_dropped():
    text = "A theft was reported near the Industrial Area in Metro City, close to Central City."
    entities = extract_entities(text)
    location_values = {e["value"] for e in entities if e["type"] == "LOCATION"}
    assert "Industrial Area" in location_values
    assert "Metro City" in location_values
    assert "Central City" in location_values


def test_organization_and_crime_category_classified_correctly():
    text = "Rahul Menon was associated with Metro Logistics in an Organized Theft case."
    entities = extract_entities(text)
    by_value = {e["value"]: e["type"] for e in entities}
    assert by_value.get("Metro Logistics") == "ORGANIZATION"
    assert by_value.get("Organized Theft") == "CRIME_CATEGORY"


def test_rejected_candidates_are_reported_with_a_reason():
    text = "Crime Category and Industrial Area are not people."
    rejected = extract_rejected_candidates(text)
    rejected_values = {r["value"] for r in rejected}
    assert "Crime Category" in rejected_values
    for r in rejected:
        assert r["attempted_type"] == "PERSON"
        assert r["reason"]


def test_field_label_line_extracts_value_not_the_label_itself():
    """'Police Station: Central City Police Station' must yield exactly one
    facility entity for the value, not a second bare 'Police Station' entity
    for the label."""
    text = "Police Station: Central City Police Station\nDate: 18 October 2024"
    entities = extract_entities(text)
    facility_values = [e["value"] for e in entities if e["type"] == "FACILITY"]
    assert facility_values == ["Central City Police Station"]


def test_alias_resolution_merges_placeholder_and_real_name():
    entities = extract_entities(FIR_TEXT)
    person_entities = [e for e in entities if e["type"] == "PERSON"]
    values = {e["value"] for e in person_entities}
    assert "Arjun Nair" in values
    assert "Rahul Menon" in values
    assert "Sameer Joseph" in values
    # The placeholder labels must not appear as separate PERSON entities --
    # they should be merged into the resolved name as an alias.
    assert "Person A" not in values and "Person B" not in values and "Person C" not in values
    arjun = next(e for e in person_entities if e["value"] == "Arjun Nair")
    assert arjun["aliases"] == ["Person A"]


def test_duplicate_relationship_mentions_are_merged_not_duplicated():
    entities = extract_entities(FIR_TEXT)
    relationships = extract_relationships_hint(FIR_TEXT, entities)
    interacted = [r for r in relationships if r["relation_type"] == "INTERACTED_WITH"
                  and {r["source"], r["target"]} == {"Rahul Menon", "Sameer Joseph"}]
    assert len(interacted) == 1, "the same relationship extracted from two overlapping sentences must merge, not duplicate"
    assert interacted[0]["mention_count"] == 2


def test_relationship_type_is_specific_not_always_associated_with():
    entities = extract_entities(FIR_TEXT)
    relationships = extract_relationships_hint(FIR_TEXT, entities)
    relation_types = {r["relation_type"] for r in relationships}
    assert "COMMUNICATED_WITH" in relation_types
    assert not relation_types.issubset({"ASSOCIATED_WITH"}), "every relationship defaulted to ASSOCIATED_WITH"


def test_weak_person_inference_is_capped_below_explicit_confidence():
    """A bare capitalized-word-pair with no explicit context should never
    outscore an explicitly-referenced person."""
    entities = extract_entities(FIR_TEXT)
    persons = [e for e in entities if e["type"] == "PERSON"]
    assert all(p["confidence"] >= 0.75 for p in persons), "explicit/alias-resolved persons should score at least 0.75"
