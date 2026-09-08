"""Rule-based extraction fallback; external NLP providers can be added later."""
import re


def extract_entities(text: str) -> list[dict[str, str]]:
    entities = []
    for match in re.finditer(r"\\b(?:P|ORG|PH|LOC)-\\d{3}\\b", text.upper()):
        value = match.group(0)
        prefix = value.split("-")[0]
        type_map = {"P": "PERSON", "ORG": "ORGANIZATION", "PH": "PHONE", "LOC": "LOCATION"}
        entities.append({"id": value, "type": type_map.get(prefix, "ENTITY"), "value": value, "evidence": text[max(0, match.start()-35):match.end()+35]})
    return entities
