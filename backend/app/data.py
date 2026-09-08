from typing import Any

NOW = "2026-09-04T10:42:00Z"

NAMES = [
    "Aarav Mehta", "Nisha Rao", "Vikram Sen", "Maya Iyer", "Kabir Shah",
    "Tara Bose", "Rohan Das", "Ishita Nair", "Dev Malhotra", "P014"
]

ORG_NAMES = ["Nexus Logistics", "Blue Arc Trading", "Northstar Finance", "Civic Works", "Orbit Telecom"]
LOC_NAMES = ["Harbor District", "Cedar Junction", "East Market", "Riverside Depot", "Old Mill Road"]

def create_nodes() -> list[dict[str, Any]]:
    nodes = [
        {"id": f"P{i:03}", "label": NAMES[i-1] if i <= len(NAMES) else f"Person {i:03}", "type": "PERSON", "status": "person of interest"}
        for i in range(1, 31)
    ]
    nodes += [
        {"id": f"ORG-{i:03}", "label": ORG_NAMES[i-1] if i <= len(ORG_NAMES) else f"Organization {i:03}", "type": "ORGANIZATION", "status": "associated entity"}
        for i in range(1, 11)
    ]
    nodes += [
        {"id": f"PH-{i:03}", "label": f"+91 98XX XX{i:03}", "type": "PHONE", "status": "reference"}
        for i in range(1, 9)
    ]
    nodes += [
        {"id": f"LOC-{i:03}", "label": LOC_NAMES[i-1] if i <= len(LOC_NAMES) else f"Location {i:03}", "type": "LOCATION", "status": "reference"}
        for i in range(1, 9)
    ]
    return nodes

def create_edges(nodes: list[dict[str, Any]]) -> list[dict[str, Any]]:
    edges = []

    def edge(source: str, target: str, relation: str, evidence: str, confidence: float, timestamp: str = NOW) -> dict[str, Any]:
        return {
            "id": f"REL-{len(edges)+1:03}",
            "source": source,
            "target": target,
            "relation": relation,
            "evidence": evidence,
            "confidence": confidence,
            "timestamp": timestamp,
            "case_id": "CASE-001"
        }

    for a, b in [(1,2),(2,3),(3,4),(4,5),(5,6),(6,7),(7,8),(8,9),(9,10),(10,11),(11,12),(12,13),(13,14),(14,15),(15,16),(16,17),(17,18),(18,19),(19,20),(20,21),(21,22),(22,23),(23,24),(24,25),(25,26),(26,27),(27,28),(28,29),(29,30),(5,20),(14,25),(10,22)]:
        edges.append(edge(f"P{a:03}", f"P{b:03}", "CONNECTED_TO", f"Synthetic relationship record REL-{len(edges)+1:03}", 0.78 + ((a+b) % 20)/100))

    for person, org in [(1,1),(4,2),(8,3),(14,1),(14,4),(20,4),(25,5),(29,2)]:
        edges.append(edge(f"P{person:03}", f"ORG-{org:03}", "ASSOCIATED_WITH", "Synthetic case file CASE-001", 0.86))

    for person, phone in [(1,1),(2,2),(5,3),(10,4),(11,4),(14,5),(20,6),(25,7),(29,8)]:
        edges.append(edge(f"P{person:03}", f"PH-{phone:03}", "CALLED", f"CDR-{person:03}{phone:02}", 0.94))

    for person, loc in [(1,1),(5,2),(10,3),(14,4),(20,5),(25,1),(29,3)]:
        edges.append(edge(f"P{person:03}", f"LOC-{loc:03}", "VISITED", "Synthetic observation report", 0.73))

    return edges

CASES = [
    {
        "id": "CASE-001",
        "title": "Operation Nexus",
        "status": "Active",
        "priority": "High",
        "investigator": "A. Sen",
        "entities": 47,
        "relationships": 0,
        "updated": "12 min ago",
        "risk": "Elevated"
    },
    {
        "id": "CASE-014",
        "title": "Harbor Ledger",
        "status": "Under review",
        "priority": "Medium",
        "investigator": "M. Iyer",
        "entities": 18,
        "relationships": 42,
        "updated": "Yesterday",
        "risk": "Watch"
    },
    {
        "id": "CASE-021",
        "title": "Cedar Junction",
        "status": "Active",
        "priority": "Low",
        "investigator": "R. Bose",
        "entities": 12,
        "relationships": 27,
        "updated": "3 days ago",
        "risk": "Low"
    }
]

ALERTS = [
    {
        "id": "ALT-204",
        "severity": "High",
        "title": "Potential bridge entity",
        "explanation": "P014 links two otherwise weakly connected communities in CASE-001.",
        "entity": "P014",
        "time": "18 min ago",
        "case": "CASE-001"
    },
    {
        "id": "ALT-203",
        "severity": "Medium",
        "title": "Communication anomaly",
        "explanation": "P010 and P011 show a short-duration communication burst.",
        "entity": "P010",
        "time": "42 min ago",
        "case": "CASE-001"
    },
    {
        "id": "ALT-202",
        "severity": "Medium",
        "title": "Potential financial anomaly",
        "explanation": "A circular flow pattern was found across four synthetic accounts.",
        "entity": "P020",
        "time": "1 hr ago",
        "case": "CASE-001"
    },
    {
        "id": "ALT-201",
        "severity": "Low",
        "title": "New high-connectivity entity",
        "explanation": "P005 has above-average network connectivity in the supplied data.",
        "entity": "P005",
        "time": "3 hrs ago",
        "case": "CASE-001"
    }
]

COMMUNITIES = [
    {"id": "COMM-A", "label": "Harbor cluster", "members": [f"P{i:03}" for i in range(1, 11)]},
    {"id": "COMM-B", "label": "Market cluster", "members": [f"P{i:03}" for i in range(11, 21)]},
    {"id": "COMM-C", "label": "Cedar cluster", "members": [f"P{i:03}" for i in range(21, 31)]}
]
