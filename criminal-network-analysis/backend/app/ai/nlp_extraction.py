"""
Lightweight, fully offline named-entity and relationship extraction.

Design note: spaCy's statistical models require downloading a multi-hundred-
MB pipeline that this offline prototype cannot rely on being pre-fetched, so
this module implements the "lightweight NLP alternative" explicitly allowed
by the brief: deterministic pattern + gazetteer + context-rule matching. It
is explainable (every match records which rule produced it and the source
sentence) and needs no external API or model download.

PRECISION OVER RECALL. The previous version of this module classified any
capitalized two-word phrase as PERSON, which produced false positives like
"Police Station" -> PERSON, "Crime Category" -> PERSON, "Industrial Area" ->
PERSON. This rewrite validates every PERSON candidate against a stoplist and
either a person-name gazetteer or explicit person-referring context, and
routes field labels, locations, organizations, facilities, and crime
categories to their own dedicated classifiers instead of letting the PERSON
heuristic claim them by default. A candidate that fails validation is
reported as a REJECTED candidate (with a reason), not silently produced as a
wrong entity and not silently dropped -- an investigator should be able to
see what the engine considered and ruled out.
"""
from __future__ import annotations

import re
from datetime import date

# ---------------------------------------------------------------------------
# Stoplists / gazetteers
# ---------------------------------------------------------------------------

# Terms that must NEVER become a PERSON entity, regardless of capitalization.
# Matched as a normalized whole-phrase set, so "Police Station" is rejected
# even though both words are individually capitalized.
NON_PERSON_PHRASES: frozenset[str] = frozenset({
    "police station", "police department", "crime category", "organized theft",
    "organised theft", "industrial area", "metro city", "central city",
    "city", "area", "station", "location", "vehicle", "phone", "case", "date",
    "organization", "organisation", "warehouse", "road", "district", "state",
    "country", "case number", "fir no", "fir no.", "name", "address",
    "description", "evidence", "report date", "case file",
})

# Individual tokens that disqualify a candidate span from being PERSON even
# if the whole phrase isn't in NON_PERSON_PHRASES (e.g. "Coastal Industrial
# Area" or "Northern District").
NON_PERSON_TOKENS: frozenset[str] = frozenset({
    "police", "station", "department", "crime", "category", "organized",
    "organised", "theft", "industrial", "area", "metro", "city", "central",
    "location", "vehicle", "phone", "case", "date", "organization",
    "organisation", "warehouse", "road", "district", "state", "country",
    "robbery", "fraud", "cybercrime", "murder", "kidnapping", "burglary",
    "trafficking", "assault", "extortion", "smuggling", "logistics", "bank",
    "agency", "company", "firm", "trust", "foundation", "group", "hospital",
    "jail", "prison", "school", "college", "airport", "port", "terminal",
    "sector", "zone", "colony", "nagar", "town", "village", "highway",
    "street", "avenue",
})

# A small first-name gazetteer used only to *upgrade* an otherwise-generic
# capitalized-word-pair into a weak PERSON inference. Absence from this list
# does not reject a name (real names are infinite); presence just raises the
# floor confidence for the weak heuristic tier.
KNOWN_FIRST_NAMES: frozenset[str] = frozenset({
    "arjun", "rahul", "sameer", "aarav", "vikram", "priya", "anita", "kabir",
    "tara", "rohan", "ishita", "dev", "maya", "nisha", "aditya", "meera",
    "ravi", "lakshmi", "karthik", "vivek", "naveen", "anil", "manoj", "ritu",
    "gautam", "radhika", "arun",
})

KNOWN_LOCATIONS: frozenset[str] = frozenset({
    "kochi", "chennai", "bengaluru", "bangalore", "hyderabad", "mumbai",
    "delhi", "kolkata", "pune", "jaipur", "lucknow", "surat", "nagpur",
    "indore", "bhopal", "patna", "vadodara", "ludhiana", "agra", "nashik",
})

CRIME_TERMS: tuple[str, ...] = (
    "organized theft", "organised theft", "robbery", "fraud", "cybercrime",
    "murder", "kidnapping", "burglary", "vehicle theft", "drug trafficking",
    "human trafficking", "assault", "financial crime", "extortion",
    "smuggling", "money laundering", "identity theft", "forgery", "bribery",
)

# Field labels that appear in structured documents (FIRs, intake forms). The
# label itself is never an entity; only the value after the colon is.
FIELD_LABELS: frozenset[str] = frozenset({
    "fir no", "fir no.", "police station", "date", "crime category", "name",
    "address", "description", "evidence", "vehicle", "phone", "location",
    "organization", "organisation", "case number", "case", "reported by",
    "investigating officer",
})

RELATION_TYPES: tuple[str, ...] = (
    "KNOWS", "COMMUNICATED_WITH", "CALLED", "MET", "INTERACTED_WITH",
    "ASSOCIATED_WITH", "WORKED_WITH", "TRAVELLED_TO", "USED", "OWNED",
    "TRANSFERRED_TO", "LINKED_TO_CASE", "LOCATED_AT", "INTERACTED_AT",
    "ATTENDED", "RELATED_TO",
)

RELATIONSHIP_CONFIDENCE_THRESHOLD = 0.70

# ---------------------------------------------------------------------------
# Structural (high-precision) regex patterns
# ---------------------------------------------------------------------------

_RE_EMAIL = re.compile(r"[\w.\-]+@[\w\-]+\.[a-zA-Z]{2,}")
_RE_PHONE_NUMBER = re.compile(r"(?:\+?\d{1,3}[\s-]?)?\d{5}[\s-]?\d{5}\b")
_RE_PHONE_ID = re.compile(r"\bPH-\d{3,6}\b")
_RE_VEHICLE = re.compile(r"\b[A-Z]{2}-?\d{2}-?[A-Z]{1,2}-?\d{4}\b")
_RE_ACCOUNT = re.compile(r"\b(?:A/C|ACC|ACCOUNT)[\s:#-]*[0-9Xx]{4,20}\b", re.IGNORECASE)
_RE_CASE = re.compile(r"\b(?:CASE|FIR|C)-\d{4}-\d{3,6}\b|\bCASE-\d{3,6}\b", re.IGNORECASE)
_RE_DATE = re.compile(
    r"\b\d{1,2}\s+(?:January|February|March|April|May|June|July|August|"
    r"September|October|November|December)(?:\s+\d{4})?\b"
    r"|\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b",
    re.IGNORECASE,
)
# All three of these use a "consecutive-capitalized-words" prefix, not a
# generic \w+ blob. \w includes lowercase, so a naive `[\w\s]{1,35}` prefix
# greedily backtracks across lowercase connector words ("from", "in", "the",
# "near") and swallows them into the match -- e.g. "Officers from Police
# Station" instead of just "Police Station", or "Theft near the Industrial
# Area" instead of "Industrial Area". Restricting the prefix to a short run
# of Capitalized tokens stops at the first lowercase word, which is exactly
# where a proper-noun phrase actually ends.
_CAP_WORD_PREFIX = r"(?:[A-Z][a-zA-Z]*\s){0,3}[A-Z][a-zA-Z]*"

_RE_ORG_SUFFIX = re.compile(
    rf"\b{_CAP_WORD_PREFIX}\s"
    r"(?:Ltd|Pvt\.?\s?Ltd|LLP|Bank|Corp|Corporation|Trust|Group|Enterprises|"
    r"Enterprise|Foundation|Association|Logistics|Services|Solutions|"
    r"Systems|Technologies|Agency|Traders)\b"
)
_RE_FACILITY = re.compile(
    rf"\b{_CAP_WORD_PREFIX}\s"
    r"(?:Police Station|Hospital|Prison|Jail|School|College|University|"
    r"Airport|Port|Terminal|Warehouse|Station)\b"
)
_RE_LOCATION_SUFFIX = re.compile(
    rf"\b{_CAP_WORD_PREFIX}\s"
    r"(?:City|Town|District|State|Province|Zone|Sector|Area|Region|Nagar|"
    r"Puram|Colony|Village|Road|Street|Avenue)\b"
)
_RE_LOCATION_CONTEXT = re.compile(
    r"\b(?:located at|near|from|to|at|location)\s+"
    r"([A-Z][\w]+(?:\s+[A-Z][\w]+){0,3})",
)
_RE_CRIME_CATEGORY = re.compile(
    r"\b(?:" + "|".join(re.escape(t) for t in sorted(CRIME_TERMS, key=len, reverse=True)) + r")\b",
    re.IGNORECASE,
)
_RE_FINANCIAL = re.compile(r"\b(?:transferred|paid|deposited|withdrew|₹|Rs\.?|INR)\s?[\d,]+\b", re.IGNORECASE)

# PERSON context patterns, highest precision first.
_RE_PERSON_EXPLICIT_LABEL = re.compile(r"\bPerson\s+([A-Z])\b")
_RE_PERSON_TITLED = re.compile(
    r"\b(?:Mr|Mrs|Ms|Dr|Prof|Inspector|Insp|Constable|SI|DySP|DSP|SP|ACP|DCP|SSP|SHO)\.?\s+"
    r"([A-Z][a-z]+(?:\s+[A-Z][a-z]+){0,2})\b"
)
_RE_PERSON_CONTEXT = re.compile(
    r"(?:referred to as|also known as|a\.k\.a\.?|identified as|individual named|person named)\s+"
    r"(?!Person\b)([A-Z][a-z]+(?:\s+[A-Z][a-z]+){0,2})",
    re.IGNORECASE,
)
_RE_PERSON_GENERIC_PAIR = re.compile(r"\b([A-Z][a-z]{2,})\s+([A-Z][a-z]{2,})\b")

# Alias linkage: "Person A, referred to as Arjun Nair" / "Person A (Arjun Nair)"
# and the reversed form "Arjun Nair, also known as Person A".
_RE_ALIAS_FORWARD = re.compile(
    r"\bPerson\s+([A-Z])\b\s*[,(]?\s*(?:referred to as|also known as|a\.k\.a\.?|identified as)?\s*"
    r"\(?([A-Z][a-z]+(?:\s+[A-Z][a-z]+){0,2})\)?",
)
_RE_ALIAS_REVERSE = re.compile(
    r"\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+){0,2})\b\s*,?\s*"
    r"(?:referred to as|also known as|a\.k\.a\.?|identified as)\s+Person\s+([A-Z])\b",
)


_RE_FIELD_LABEL_LINE = re.compile(r"(?m)^([ \t]*)([A-Za-z][A-Za-z .]{1,30}?):([ \t]*)")


def _mask_field_labels(text: str) -> str:
    """Blank out structured-document field labels ('Police Station:',
    'Crime Category:', 'FIR No.:') at the start of a line so the label text
    itself is never scanned as entity content, while the *value* that
    follows the colon is left untouched at its original offset and goes
    through the normal extraction pipeline. Replacing with spaces (not
    deleting) keeps every other match's character offsets valid."""
    def mask(match: re.Match) -> str:
        label = match.group(2).strip().rstrip(".").lower()
        if label in FIELD_LABELS:
            return " " * len(match.group(0))
        return match.group(0)
    return _RE_FIELD_LABEL_LINE.sub(mask, text)


def _normalize(value: str) -> str:
    """Whitespace/punctuation/case-insensitive comparison key."""
    return re.sub(r"\s+", " ", value.strip().rstrip(".,;:")).lower()


def _is_non_person(phrase: str) -> bool:
    normalized = _normalize(phrase)
    if normalized in NON_PERSON_PHRASES:
        return True
    tokens = normalized.split()
    if any(tok in NON_PERSON_TOKENS for tok in tokens):
        return True
    if normalized in KNOWN_LOCATIONS:
        return True
    return False


def _confidence_for(entity_type: str, value: str, tier: str = "") -> float:
    """Calibrated, explainable confidence. Structural patterns (regex-exact
    formats like a vehicle plate or phone number) are near-certain; context-
    validated classifications sit in the 85-90% band; the weak generic
    name-pair heuristic is capped at 65-75% and must never be the majority
    of results for a well-formed document."""
    structural = {"EMAIL", "PHONE", "VEHICLE", "ACCOUNT", "CASE", "DATE"}
    if entity_type in structural:
        return 0.95
    if entity_type == "CRIME_CATEGORY":
        return 0.95
    if entity_type in {"ORGANIZATION", "FACILITY", "LOCATION"}:
        return 0.90
    if entity_type == "PERSON":
        if tier == "explicit":
            return 0.90
        if tier == "placeholder":
            return 0.75
        return 0.70  # weak generic-pair inference
    if entity_type == "FINANCIAL_ENTITY":
        return 0.75
    return 0.60


# ---------------------------------------------------------------------------
# Alias resolution
# ---------------------------------------------------------------------------

def _resolve_aliases(text: str) -> dict[str, str]:
    """Return {placeholder_label: canonical_name}, e.g. {"Person A": "Arjun Nair"}."""
    aliases: dict[str, str] = {}
    for match in _RE_ALIAS_FORWARD.finditer(text):
        letter, name = match.group(1), match.group(2).strip()
        if name and not _is_non_person(name):
            aliases[f"Person {letter}"] = name
    for match in _RE_ALIAS_REVERSE.finditer(text):
        name, letter = match.group(1).strip(), match.group(2)
        if name and not _is_non_person(name):
            aliases.setdefault(f"Person {letter}", name)
    return aliases


# ---------------------------------------------------------------------------
# Entity extraction
# ---------------------------------------------------------------------------

def extract_entities(text: str) -> list[dict]:
    entities, _rejected = _run_extraction(text)
    return entities


def extract_rejected_candidates(text: str) -> list[dict]:
    _entities, rejected = _run_extraction(text)
    return rejected


def _run_extraction(raw_text: str) -> tuple[list[dict], list[dict]]:
    if not raw_text or not raw_text.strip():
        return [], []

    text = _mask_field_labels(raw_text)
    aliases = _resolve_aliases(text)
    alias_by_name = {name: label for label, name in aliases.items()}

    found: list[dict] = []
    rejected: list[dict] = []
    seen: set[tuple[str, str]] = set()
    claimed_spans: list[tuple[int, int]] = []
    counter = 0
    today = date.today().isoformat()

    def overlaps(start: int, end: int) -> bool:
        return any(start < c_end and end > c_start for c_start, c_end in claimed_spans)

    def add_entity(start: int, end: int, value: str, etype: str, method: str, tier: str = "", extra: dict | None = None) -> dict | None:
        nonlocal counter
        value = re.sub(r"\s+", " ", value.strip().rstrip(".,;:"))
        if not value:
            return None
        key = (etype, _normalize(value))
        if key in seen or overlaps(start, end):
            return None
        seen.add(key)
        claimed_spans.append((start, end))
        counter += 1
        entity = {
            "id": f"EXT-{counter:03}",
            "value": value,
            "type": etype,
            "confidence": round(_confidence_for(etype, value, tier), 2),
            "source": f"AI text extraction ({method})",
            "extraction_method": method,
            "first_seen": today,
            "last_seen": today,
        }
        if extra:
            entity.update(extra)
        found.append(entity)
        return entity

    def add_rejected(start: int, end: int, value: str, attempted_type: str, reason: str) -> None:
        if overlaps(start, end):
            return
        rejected.append({"value": value.strip(), "attempted_type": attempted_type, "reason": reason})

    # 1. Structural, highest precision -------------------------------------------------
    for etype, pat in [("EMAIL", _RE_EMAIL), ("PHONE", _RE_PHONE_ID), ("PHONE", _RE_PHONE_NUMBER),
                       ("VEHICLE", _RE_VEHICLE), ("ACCOUNT", _RE_ACCOUNT), ("CASE", _RE_CASE),
                       ("DATE", _RE_DATE)]:
        for m in pat.finditer(text):
            add_entity(m.start(), m.end(), m.group(0), etype, "structural pattern")

    # 2. Facilities (named police stations etc.) -- claimed before ORGANIZATION/LOCATION
    #    so "Central City Police Station" isn't split into pieces. A city name
    #    embedded as a prefix of a facility name (e.g. "Central City" inside
    #    "Central City Police Station") is still worth surfacing as its own
    #    LOCATION entity for geographic analytics, so that one case is
    #    deliberately allowed to nest inside the claimed facility span.
    for m in _RE_FACILITY.finditer(text):
        add_entity(m.start(), m.end(), m.group(0), "FACILITY", "facility pattern")
        nested = _RE_LOCATION_SUFFIX.search(m.group(0))
        if nested and _normalize(nested.group(0)) != _normalize(m.group(0)):
            key = ("LOCATION", _normalize(nested.group(0)))
            if key not in seen:
                seen.add(key)
                counter += 1
                found.append({
                    "id": f"EXT-{counter:03}", "value": nested.group(0).strip(), "type": "LOCATION",
                    "confidence": round(_confidence_for("LOCATION", nested.group(0)), 2),
                    "source": "AI text extraction (location nested in facility name)",
                    "extraction_method": "location nested in facility name",
                    "first_seen": today, "last_seen": today,
                })

    # 3. Organizations (suffix-bearing names)
    for m in _RE_ORG_SUFFIX.finditer(text):
        add_entity(m.start(), m.end(), m.group(0), "ORGANIZATION", "organization suffix pattern")

    # 4. Crime categories
    for m in _RE_CRIME_CATEGORY.finditer(text):
        add_entity(m.start(), m.end(), m.group(0), "CRIME_CATEGORY", "crime-category gazetteer")

    # 5. Locations -- structural suffix, then contextual preposition cue, then gazetteer.
    for m in _RE_LOCATION_SUFFIX.finditer(text):
        val = m.group(0).strip()
        if _normalize(val) in NON_PERSON_PHRASES or not overlaps(m.start(), m.end()):
            add_entity(m.start(), m.end(), val, "LOCATION", "location suffix pattern")
    for m in _RE_LOCATION_CONTEXT.finditer(text):
        candidate = m.group(1)
        start = m.start(1)
        end = m.end(1)
        if _is_non_person(candidate) or not any(c.isalpha() for c in candidate):
            continue
        add_entity(start, end, candidate, "LOCATION", "location context cue")
    for word in KNOWN_LOCATIONS:
        pat = re.compile(rf"\b{re.escape(word)}\b", re.IGNORECASE)
        m = pat.search(text)
        if m and not overlaps(m.start(), m.end()):
            add_entity(m.start(), m.end(), m.group(0).title(), "LOCATION", "location gazetteer")

    # 6. PERSON -- alias-resolved canonical names get top billing.
    for label, name in aliases.items():
        m = re.search(re.escape(name), text)
        if m:
            add_entity(m.start(), m.end(), name, "PERSON", "alias-resolved explicit reference", tier="explicit",
                       extra={"aliases": [label]})
        else:
            add_entity(0, 0, name, "PERSON", "alias-resolved explicit reference", tier="explicit", extra={"aliases": [label]})

    # 6b. Explicit person-referring context ("identified as X", titled names)
    for pattern, method in [(_RE_PERSON_TITLED, "titled person reference"), (_RE_PERSON_CONTEXT, "explicit person context")]:
        for m in pattern.finditer(text):
            name = m.group(1).strip()
            if _is_non_person(name):
                add_rejected(m.start(1), m.end(1), name, "PERSON", "matches non-person stoplist term")
                continue
            add_entity(m.start(1), m.end(1), name, "PERSON", method, tier="explicit")

    # 6c. Bare "Person X" labels that were never resolved to a real name.
    for m in _RE_PERSON_EXPLICIT_LABEL.finditer(text):
        label = f"Person {m.group(1)}"
        if label in aliases:
            continue  # already represented by the canonical name entity above
        add_entity(m.start(), m.end(), label, "PERSON", "unresolved placeholder label", tier="placeholder")

    # 6d. Weak generic two-capitalized-word heuristic -- validated against the
    #     stoplist and, for a confidence bump, the first-name gazetteer. This
    #     is the pattern that used to promote "Police Station"/"Crime
    #     Category"/"Industrial Area" to PERSON; now it rejects them instead.
    for m in _RE_PERSON_GENERIC_PAIR.finditer(text):
        phrase = m.group(0)
        if overlaps(m.start(), m.end()):
            continue
        if _is_non_person(phrase):
            add_rejected(m.start(), m.end(), phrase, "PERSON", "matches non-person stoplist term")
            continue
        first_token = m.group(1).lower()
        if first_token not in KNOWN_FIRST_NAMES:
            add_rejected(m.start(), m.end(), phrase, "PERSON", "capitalized phrase without person-name or contextual evidence")
            continue
        add_entity(m.start(), m.end(), phrase, "PERSON", "name-gazetteer heuristic", tier="weak")

    # 7. Financial cues
    for m in _RE_FINANCIAL.finditer(text):
        add_entity(m.start(), m.end(), m.group(0), "FINANCIAL_ENTITY", "financial amount cue")

    return found, rejected


# ---------------------------------------------------------------------------
# Relationship extraction
# ---------------------------------------------------------------------------

_VERB_RELATION_MAP: tuple[tuple[re.Pattern, str, float], ...] = (
    (re.compile(r"\bcommunicated\s+with\b", re.IGNORECASE), "COMMUNICATED_WITH", 0.95),
    (re.compile(r"\bcalled\b|\bcalling\b", re.IGNORECASE), "CALLED", 0.95),
    (re.compile(r"\bmet\b|\bmeeting\b", re.IGNORECASE), "MET", 0.90),
    (re.compile(r"\binteracted\s+with\b", re.IGNORECASE), "INTERACTED_WITH", 0.90),
    (re.compile(r"\bworked\s+with\b", re.IGNORECASE), "WORKED_WITH", 0.90),
    (re.compile(r"\bassociated\s+with\b", re.IGNORECASE), "ASSOCIATED_WITH", 0.85),
    (re.compile(r"\btravell?ed\s+to\b", re.IGNORECASE), "TRAVELLED_TO", 0.90),
    (re.compile(r"\btransferred\b", re.IGNORECASE), "TRANSFERRED_TO", 0.90),
    (re.compile(r"\bowned\b|\bowns\b", re.IGNORECASE), "OWNED", 0.90),
    (re.compile(r"\bused\b", re.IGNORECASE), "USED", 0.85),
    (re.compile(r"\battended\b", re.IGNORECASE), "ATTENDED", 0.90),
    (re.compile(r"\bknows\b|\backnowledged\s+knowing\b", re.IGNORECASE), "KNOWS", 0.85),
    (re.compile(r"\blinked\s+to\b", re.IGNORECASE), "LINKED_TO_CASE", 0.90),
    (re.compile(r"\blocated\s+at\b|\bnear\b", re.IGNORECASE), "LOCATED_AT", 0.85),
    (re.compile(r"\binteracted\s+at\b", re.IGNORECASE), "INTERACTED_AT", 0.85),
)

_ACTOR_TYPES = {"PERSON", "ORGANIZATION", "VEHICLE", "LOCATION", "CASE", "ACCOUNT"}


def _relation_for_sentence(sentence: str) -> tuple[str, float]:
    for pattern, relation, confidence in _VERB_RELATION_MAP:
        if pattern.search(sentence):
            return relation, confidence
    return "RELATED_TO", 0.65  # indirect inference: no explicit verb cue


def extract_relationships_hint(text: str, entities: list[dict]) -> list[dict]:
    """Sentence-scoped relationship extraction with deduplication.

    Two entities co-occurring merely in the same *paragraph* is not enough --
    they must co-occur in the same *sentence*, and the relationship type is
    chosen from the most specific verb cue present rather than defaulting to
    ASSOCIATED_WITH for everything. Duplicate (source, relation, target)
    triples extracted from overlapping sentence matches are merged into one
    record with a mention_count rather than appearing twice.
    """
    sentences = re.split(r"(?<=[.!?])\s+", text)
    merged: dict[tuple[str, str, str], dict] = {}

    for sentence in sentences:
        actors = [e for e in entities if e["type"] in _ACTOR_TYPES and e["value"] in sentence]
        if len(actors) < 2:
            continue
        relation, confidence = _relation_for_sentence(sentence)
        for i in range(len(actors) - 1):
            source, target = actors[i], actors[i + 1]
            if source["value"] == target["value"]:
                continue
            pair_relation = relation
            # A person-oriented verb (interacted with, met, worked with...)
            # applied to a LOCATION target isn't the most specific relation
            # for that pair -- "at <place>" is a location reference, not a
            # second person being interacted with.
            if target["type"] == "LOCATION" and pair_relation in {"INTERACTED_WITH", "MET", "WORKED_WITH", "KNOWS"}:
                pair_relation = "INTERACTED_AT" if pair_relation == "INTERACTED_WITH" else "LOCATED_AT"
            key = (_normalize(source["value"]), pair_relation, _normalize(target["value"]))
            reverse_key = (_normalize(target["value"]), pair_relation, _normalize(source["value"]))
            existing_key = key if key in merged else (reverse_key if reverse_key in merged else key)
            if existing_key in merged:
                record = merged[existing_key]
                record["mention_count"] += 1
                record["source_records"].append(sentence.strip())
                record["confidence"] = max(record["confidence"], confidence)
            else:
                is_confirmed = confidence >= RELATIONSHIP_CONFIDENCE_THRESHOLD
                merged[key] = {
                    "source": source["value"],
                    "target": target["value"],
                    "relation_type": pair_relation,
                    "evidence_sentence": sentence.strip(),
                    "source_records": [sentence.strip()],
                    "mention_count": 1,
                    "label": "Potential connection" if is_confirmed else "Potential Relationship Lead",
                    "confidence": round(confidence, 2),
                    "extraction_method": "sentence-level verb-cue matching",
                }
    return list(merged.values())
