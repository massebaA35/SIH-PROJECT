from app.ai.nlp_extraction import extract_entities, extract_relationships_hint

problem_inputs = [
    "Police Station",
    "Central City",
    "Crime Category",
    "Organized Theft",
    "Industrial Area",
    "Metro City",
    "Metro Logistics",
]
print("=== BLOCKLIST / NON-PERSON TESTS ===")
for phrase in problem_inputs:
    results = extract_entities(phrase)
    person_hits = [r for r in results if r["type"] == "PERSON"]
    status = "FAIL" if person_hits else "PASS"
    entity_summary = [r["type"] + "::" + r["value"] for r in results] or ["(no entities)"]
    print(f"  [{status}] {phrase!r} -> {entity_summary}")

print()
print("=== REAL PERSON DETECTION ===")
person_inputs = [
    "Rahul Sharma met Priya Verma at the park.",
    "Inspector Singh arrested Vikram Malhotra.",
    "Person A called Person B on 12 August 2024.",
    "Dr. Anita Roy submitted the report.",
]
for text in person_inputs:
    results = extract_entities(text)
    persons = [r["value"] for r in results if r["type"] == "PERSON"]
    print(f"  Text: {text[:70]!r}")
    print(f"  PERSONS: {persons}")

print()
print("=== NEW ENTITY TYPES ===")
test_text = "The suspect was booked at Andheri Police Station for Organised Theft in the North Industrial Zone."
results = extract_entities(test_text)
for r in results:
    print(f"  {r['type']:20} | {r['value']}")

print()
print("=== RELATIONSHIP DEDUP ===")
text2 = "Rahul Sharma met Priya Verma. Rahul Sharma met Priya Verma again later. Priya Verma met Rahul Sharma once more."
entities2 = extract_entities(text2)
rels = extract_relationships_hint(text2, entities2)
print(f"  Sentences with same pair: 3, Unique rels produced: {len(rels)}")
for r in rels:
    print(f"    {r['source']} --[{r['relation_type']}]--> {r['target']}")
