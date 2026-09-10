import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from app.ai.nlp_extraction import extract_entities, extract_rejected_candidates, extract_relationships_hint

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
with Metro Logistics and was linked to case C-2024-0112. A second vehicle
XX-00-CD-5678 was also recorded. Sameer Joseph, also known as Person C,
interacted with Rahul Menon at Metro Logistics. Sameer Joseph interacted
with Rahul Menon again the following day. Investigators may be reached at
PH-1007.
"""

print("=" * 70)
print("ENTITIES")
print("=" * 70)
entities = extract_entities(FIR_TEXT)
for e in entities:
    alias = f"  (alias: {e['aliases'][0]})" if e.get("aliases") else ""
    print(f"{e['id']:8} {e['value']:35} {e['type']:16} {int(e['confidence']*100)}%{alias}")

print()
print("=" * 70)
print("REJECTED CANDIDATES")
print("=" * 70)
for r in extract_rejected_candidates(FIR_TEXT):
    print(f"  {r['value']:30} attempted={r['attempted_type']:8} reason={r['reason']}")

print()
print("=" * 70)
print("RELATIONSHIPS")
print("=" * 70)
for rel in extract_relationships_hint(FIR_TEXT, entities):
    print(f"  {rel['source']:15} {rel['relation_type']:18} {rel['target']:15} "
          f"conf={int(rel['confidence']*100)}% mentions={rel['mention_count']} label={rel['label']}")

print()
print("=" * 70)
print("SUMMARY")
print("=" * 70)
print(f"Entities extracted: {len(entities)}")
print(f"Rejected candidates: {len(extract_rejected_candidates(FIR_TEXT))}")
person_count = sum(1 for e in entities if e["type"] == "PERSON")
print(f"PERSON entities: {person_count}")
bad_persons = [e for e in entities if e["type"] == "PERSON" and e["value"] in
               {"Police Station", "Central City", "Crime Category", "Organized Theft", "Industrial Area", "Metro City", "Metro Logistics"}]
print(f"Incorrectly classified PERSON entities: {len(bad_persons)} {bad_persons}")
