"""
Lightweight, fully offline named-entity extraction.

Design note: spaCy's statistical models require downloading a multi-hundred-
MB pipeline that this offline prototype cannot rely on being pre-fetched, so
this module implements the "lightweight NLP alternative" explicitly allowed
by the brief: deterministic pattern + gazetteer matching. It is
explainable (every match cites the pattern that produced it) and needs no
external API or model download, matching the "no paid APIs" requirement.
"""
import re
from datetime import date, datetime

# A small gazetteer of synthetic place names used by the seed dataset, so the
# extractor can recognize LOCATION mentions that don't have a structural cue.
KNOWN_LOCATIONS = {
    "kochi", "chennai", "bengaluru", "bangalore", "hyderabad", "mumbai", "delhi",
    "kolkata", "pune", "jaipur", "lucknow", "surat", "nagpur", "indore", "bhopal",
    "patna", "vadodara", "ludhiana", "agra", "nashik", "cedar junction", "harbor district",
}

PATTERNS: list[tuple[str, str, re.Pattern]] = [
    ("EMAIL", r"[\w.\-]+@[\w\-]+\.[a-zA-Z]{2,}", re.compile(r"[\w.\-]+@[\w\-]+\.[a-zA-Z]{2,}")),
    ("PHONE", r"phone/mobile pattern", re.compile(r"(?:\+?\d{1,3}[\s-]?)?\d{5}[\s-]?\d{5}\b")),
    ("VEHICLE", r"Indian-style plate KL-07-AB-1234", re.compile(r"\b[A-Z]{2}-?\d{2}-?[A-Z]{1,2}-?\d{4}\b")),
    ("ACCOUNT", r"account/IBAN-like token", re.compile(r"\b(?:A/C|ACC|ACCOUNT)[\s:#-]*[0-9Xx]{4,20}\b", re.IGNORECASE)),
    ("CASE", r"CASE-#### token", re.compile(r"\bCASE-\d{3,6}\b", re.IGNORECASE)),
    ("DATE", r"'12 August' / '12 August 2024' / '12/08/2024'", re.compile(
        r"\b\d{1,2}\s+(?:January|February|March|April|May|June|July|August|September|October|November|December)(?:\s+\d{4})?\b"
        r"|\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b", re.IGNORECASE)),
    # ORGANIZATION is matched before PERSON (see extract_entities) so a phrase like
    # "Coastal Traders Pvt Ltd" is claimed whole rather than the generic
    # capitalized-word-pair PERSON heuristic splitting it into false-positive names.
    ("ORGANIZATION", r"'... Ltd/Pvt/Bank/Corp/Trust'", re.compile(
        r"\b[A-Z][\w&.\s]{2,40}?\s(?:Ltd|Pvt\.?\s?Ltd|Bank|Corp|Corporation|Trust|Group|Enterprises|Foundation)\b")),
    ("PERSON", r"'Person A' / 'Person B' capitalized-name heuristic", re.compile(
        r"\b(?:Person\s+[A-Z]|[A-Z][a-z]+\s+[A-Z][a-z]+)\b")),
    ("EVENT", r"'meeting'/'transferred'/'called'/'travelled' verb cue", re.compile(
        r"\b(?:met|meeting|called|calling|transferred|travelled|traveled|communicated)\b", re.IGNORECASE)),
]

FINANCIAL_CUES = re.compile(r"\b(?:transferred|paid|deposited|withdrew|₹|Rs\.?|INR)\s?[\d,]+\b", re.IGNORECASE)


def _confidence_for(entity_type: str, matched_text: str) -> float:
    """Deterministic, explainable confidence: structural cues (phone, plate,
    email, case id) are near-certain; free-text heuristics (person names,
    org names) are scored lower because they can false-positive."""
    high_confidence_types = {"EMAIL", "PHONE", "VEHICLE", "ACCOUNT", "CASE", "DATE"}
    if entity_type in high_confidence_types:
        return 0.95
    if entity_type == "ORGANIZATION":
        return 0.8
    if entity_type == "PERSON":
        return 0.7 if matched_text.lower().startswith("person") else 0.65
    if entity_type == "FINANCIAL_ENTITY":
        return 0.75
    return 0.6


def extract_entities(text: str) -> list[dict]:
    """Run every pattern over the text and return deduplicated structured
    entities: id, value, type, confidence, source, span."""
    if not text or not text.strip():
        return []

    found: list[dict] = []
    seen: set[tuple[str, str]] = set()
    counter = 0
    # Track which character ranges are already claimed by a higher-priority
    # match, so a looser heuristic (PERSON's capitalized-word-pair regex)
    # can't re-carve a span already claimed by a more specific one (e.g. an
    # ORGANIZATION name, or a structural pattern like VEHICLE/EMAIL). This
    # is what stops "Coastal Traders Pvt Ltd" from also being reported as
    # two bogus PERSON matches ("Coastal Traders", "Pvt Ltd").
    claimed_spans: list[tuple[int, int]] = []

    def overlaps_claimed(start: int, end: int) -> bool:
        return any(start < c_end and end > c_start for c_start, c_end in claimed_spans)

    for entity_type, _label, pattern in PATTERNS:
        if entity_type == "EVENT":
            continue  # verb cues feed relationship extraction, not the entity table
        for match in pattern.finditer(text):
            value = match.group(0).strip()
            if not value or overlaps_claimed(match.start(), match.end()):
                continue
            key = (entity_type, value.lower())
            if key in seen:
                continue
            seen.add(key)
            claimed_spans.append((match.start(), match.end()))
            counter += 1
            found.append({
                "id": f"EXT-{counter:03}",
                "value": value,
                "type": entity_type,
                "confidence": round(_confidence_for(entity_type, value), 2),
                "source": "AI text extraction (offline pattern engine)",
                "first_seen": date.today().isoformat(),
                "last_seen": date.today().isoformat(),
            })

    # LOCATION via gazetteer (separate pass so it doesn't collide with PERSON heuristic)
    for word in KNOWN_LOCATIONS:
        pattern = re.compile(rf"\b{re.escape(word)}\b", re.IGNORECASE)
        match = pattern.search(text)
        if match and not overlaps_claimed(match.start(), match.end()):
            value = match.group(0)
            key = ("LOCATION", value.lower())
            if key not in seen:
                seen.add(key)
                claimed_spans.append((match.start(), match.end()))
                counter += 1
                found.append({
                    "id": f"EXT-{counter:03}",
                    "value": value.title(),
                    "type": "LOCATION",
                    "confidence": 0.85,
                    "source": "AI text extraction (gazetteer match)",
                    "first_seen": date.today().isoformat(),
                    "last_seen": date.today().isoformat(),
                })

    # FINANCIAL_ENTITY via amount cues
    for match in FINANCIAL_CUES.finditer(text):
        value = match.group(0).strip()
        key = ("FINANCIAL_ENTITY", value.lower())
        if key not in seen:
            seen.add(key)
            counter += 1
            found.append({
                "id": f"EXT-{counter:03}",
                "value": value,
                "type": "FINANCIAL_ENTITY",
                "confidence": 0.75,
                "source": "AI text extraction (financial cue)",
                "first_seen": date.today().isoformat(),
                "last_seen": date.today().isoformat(),
            })

    return found


def extract_relationships_hint(text: str, entities: list[dict]) -> list[dict]:
    """Very small explainable heuristic: if two PERSON/ORG entities and a
    relationship verb cue co-occur in the same sentence, propose a
    candidate relationship. Always returned as a *lead*, never asserted."""
    sentences = re.split(r"(?<=[.!?])\s+", text)
    candidates = []
    verb_map = {
        "met": "MET", "meeting": "MET", "called": "CALLED", "calling": "CALLED",
        "transferred": "TRANSFERRED_TO", "travelled": "TRAVELLED_TO", "traveled": "TRAVELLED_TO",
        "communicated": "COMMUNICATED_WITH",
    }
    actor_types = {"PERSON", "ORGANIZATION"}
    for sentence in sentences:
        actors = [e for e in entities if e["type"] in actor_types and e["value"] in sentence]
        if len(actors) < 2:
            continue
        relation = "ASSOCIATED_WITH"
        for verb, mapped in verb_map.items():
            if re.search(rf"\b{verb}\b", sentence, re.IGNORECASE):
                relation = mapped
                break
        candidates.append({
            "source": actors[0]["value"],
            "target": actors[1]["value"],
            "relation_type": relation,
            "evidence_sentence": sentence.strip(),
            "label": "Potential connection",
            "confidence": 0.6,
        })
    return candidates
