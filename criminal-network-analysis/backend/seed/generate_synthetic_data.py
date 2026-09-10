"""
Synthetic crime-investigation dataset generator.

Everything here is fictional: names, plate numbers, phone numbers, and
account numbers are generated, not sampled from any real registry. The
generator builds several communities of persons/organizations plus a
handful of "bridge" persons who link communities together, and
deliberately plants a few duplicate vehicles/phones/financial cycles so the
rule-based anomaly detector (app/analytics/anomaly_detection.py) has real
patterns to find once the seed script loads this data.

Running this module directly prints summary counts; `generate()` is the
importable entry point used by seed/seed_db.py.
"""
import hashlib
import itertools
import random
from datetime import date, datetime, timedelta

random.seed(42)  # deterministic dataset across runs, for reproducible demos

FIRST_NAMES = [
    "Arjun", "Meera", "Rohan", "Divya", "Karthik", "Ananya", "Vikram", "Priya",
    "Rahul", "Sneha", "Amit", "Kavya", "Suresh", "Lakshmi", "Nikhil", "Pooja",
    "Manoj", "Ritu", "Sanjay", "Deepa", "Arun", "Neha", "Vivek", "Shreya",
    "Ravi", "Anita", "Kiran", "Swati", "Ajay", "Rekha", "Sameer", "Tanvi",
    "Gautam", "Isha", "Harish", "Nandini", "Prakash", "Sunita", "Yash", "Bhavna",
    "Naveen", "Radhika", "Dinesh", "Aarti", "Mahesh", "Preeti", "Rajesh", "Sonia",
    "Anil", "Kritika",
]
LAST_NAMES = [
    "Nair", "Menon", "Iyer", "Pillai", "Reddy", "Rao", "Sharma", "Verma",
    "Gupta", "Kumar", "Das", "Patel", "Shah", "Joshi", "Bose", "Chatterjee",
    "Mishra", "Singh", "Yadav", "Pandey",
]
ORG_NAMES = [
    "Coastal Traders Pvt Ltd", "Nexora Logistics Corp", "Silverline Freight Group",
    "Bluewave Exports Ltd", "Meridian Holdings Trust", "Harborview Enterprises",
    "Northgate Shipping Corp", "Sunrise Textiles Pvt Ltd", "Vantage Realty Group",
    "Crescent Finance Bank",
]
VEHICLE_TYPES = ["Sedan", "SUV", "Motorcycle", "Pickup Truck", "Van", "Hatchback"]
VEHICLE_COLORS = ["White", "Black", "Silver", "Blue", "Red", "Grey"]
CARRIERS = ["Synthetic Telecom A", "Synthetic Telecom B", "Synthetic Telecom C"]
STATE_CODES = ["KL", "TN", "KA", "MH", "DL", "TG", "WB", "GJ", "UP", "RJ"]

# City-level, publicly-known place names only -- never a specific private address.
CITIES = [
    ("Kochi", "Kerala", 9.9312, 76.2673), ("Chennai", "Tamil Nadu", 13.0827, 80.2707),
    ("Bengaluru", "Karnataka", 12.9716, 77.5946), ("Hyderabad", "Telangana", 17.3850, 78.4867),
    ("Mumbai", "Maharashtra", 19.0760, 72.8777), ("Delhi", "Delhi", 28.7041, 77.1025),
    ("Kolkata", "West Bengal", 22.5726, 88.3639), ("Pune", "Maharashtra", 18.5204, 73.8567),
    ("Jaipur", "Rajasthan", 26.9124, 75.7873), ("Lucknow", "Uttar Pradesh", 26.8467, 80.9462),
    ("Cedar Junction (synthetic)", "Synthetic Region", 11.2, 78.9),
    ("Harbor District (synthetic)", "Synthetic Region", 9.95, 76.3),
]

CRIME_CATEGORIES = [
    "Organized Crime", "Financial Fraud", "Human Trafficking Risk Indicators",
    "Narcotics Network", "Cybercrime", "Extortion Ring", "Smuggling Network",
    "Missing Person Investigation", "Women Safety Incident Cluster", "Counterfeit Trade",
]
INVESTIGATORS = [
    "Insp. A. Sen", "Insp. R. Krishnan", "Insp. D. Fernandes", "Insp. M. Bano",
    "Insp. S. Thomas", "Insp. P. Chawla",
]
REGIONS = ["South Zone", "West Zone", "North Zone", "East Zone", "Coastal Zone"]

N_PERSONS = 50
N_ORGS = 10
N_VEHICLES = 30
N_PHONES = 50
N_LOCATIONS = 20
N_ACCOUNTS = 15
N_CASES = 20
N_EVENTS = 100
N_COMMUNITIES = 5
CASES_PER_COMMUNITY = N_CASES // N_COMMUNITIES

TODAY = date(2026, 9, 9)  # fixed "now" so the dataset reads consistently in every demo
NOW_DT = datetime(2026, 9, 9, 12, 0, 0)

_rel_counter = itertools.count(1)
_evt_counter = itertools.count(1)
_ev_counter = itertools.count(1)


def _rand_date(days_back_min: int, days_back_max: int) -> date:
    return TODAY - timedelta(days=random.randint(days_back_min, days_back_max))


def _rand_datetime(days_back_min: int, days_back_max: int, force_night: bool = False) -> datetime:
    d = _rand_date(days_back_min, days_back_max)
    hour = random.randint(0, 5) if force_night else random.randint(6, 22)
    return datetime(d.year, d.month, d.day, hour, random.randint(0, 59))


def _new_rel_id() -> str:
    return f"REL-{next(_rel_counter):04d}"


def _new_evt_id() -> str:
    return f"EVT-{next(_evt_counter):04d}"


def _new_ev_id() -> str:
    return f"EV-{next(_ev_counter):04d}"


def _base_entities() -> dict:
    persons = []
    for i in range(N_PERSONS):
        persons.append({
            "id": f"PERSON-{101 + i}",
            "name": f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}",
            "gender": random.choice(["Male", "Female"]),
            "age_range": random.choice(["18-25", "26-35", "36-45", "46-60"]),
            "nationality": "India (synthetic)",
            "occupation": random.choice([
                "Trader", "Driver", "Clerk", "Consultant", "Logistics Coordinator",
                "Unemployed", "Shop Owner", "Contractor",
            ]),
            "region": random.choice(REGIONS),
            "first_seen": _rand_date(300, 720),
            "last_seen": _rand_date(0, 60),
            "source": "Synthetic demo dataset",
        })

    organizations = []
    for i in range(N_ORGS):
        organizations.append({
            "id": f"ORG-{201 + i}",
            "name": ORG_NAMES[i],
            "org_type": random.choice(["Logistics", "Trading", "Financial Services", "Real Estate", "Shipping"]),
            "region": random.choice(REGIONS),
            "first_seen": _rand_date(400, 900),
            "last_seen": _rand_date(0, 90),
            "source": "Synthetic demo dataset",
        })

    vehicles = []
    for i in range(N_VEHICLES):
        state = random.choice(STATE_CODES)
        plate = f"{state}-{random.randint(1,99):02d}-{random.choice('ABCDEFGH')}{random.choice('ABCDEFGH')}-{random.randint(1000,9999)}"
        vehicles.append({
            "id": f"VEHICLE-{301 + i}",
            "registration": plate,
            "vehicle_type": random.choice(VEHICLE_TYPES),
            "color": random.choice(VEHICLE_COLORS),
            "first_seen": _rand_date(300, 700),
            "last_seen": _rand_date(0, 60),
            "source": "Synthetic demo dataset",
        })

    phones = []
    for i in range(N_PHONES):
        phones.append({
            "id": f"PHONE-{401 + i}",
            "number": f"XXXXX-{90000 + i}",
            "carrier": random.choice(CARRIERS),
            "first_seen": _rand_date(300, 700),
            "last_seen": _rand_date(0, 30),
            "source": "Synthetic demo dataset",
        })

    locations = []
    for i in range(N_LOCATIONS):
        city, region, lat, lng = CITIES[i % len(CITIES)]
        name = city if i < len(CITIES) else f"{city} Sector {i + 1}"
        locations.append({
            "id": f"LOC-{501 + i}",
            "name": name,
            "region": region,
            "location_type": random.choice(["Residential Area", "Commercial Hub", "Transit Point", "Warehouse Zone", "Market"]),
            "latitude": round(lat + random.uniform(-0.05, 0.05), 4),
            "longitude": round(lng + random.uniform(-0.05, 0.05), 4),
            "first_seen": _rand_date(300, 700),
            "last_seen": _rand_date(0, 60),
            "source": "Synthetic demo dataset",
        })

    accounts = []
    for i in range(N_ACCOUNTS):
        accounts.append({
            "id": f"ACCOUNT-{601 + i}",
            "masked_number": f"XXXX-XXXX-{random.randint(1000, 9999)}",
            "institution": random.choice(["Crescent Finance Bank", "Unity Cooperative Bank (synthetic)", "Coastal Trust Bank (synthetic)"]),
            "account_type": random.choice(["Savings", "Current", "Business"]),
            "first_seen": _rand_date(300, 700),
            "last_seen": _rand_date(0, 60),
            "source": "Synthetic demo dataset",
        })

    return {
        "persons": persons, "organizations": organizations, "vehicles": vehicles,
        "phones": phones, "locations": locations, "accounts": accounts,
    }


def _make_relationship(source_id, source_type, target_id, target_type, relation_type,
                        case_id="", frequency=1, evidence="", confidence=0.75, occurred_on=None) -> dict:
    return {
        "id": _new_rel_id(),
        "source_id": source_id, "source_type": source_type,
        "target_id": target_id, "target_type": target_type,
        "relation_type": relation_type, "case_id": case_id,
        "occurred_on": occurred_on or _rand_date(1, 300),
        "frequency": frequency, "evidence": evidence,
        "source": "Synthetic demo dataset", "confidence": round(confidence, 2),
    }


def _assemble(entities: dict) -> dict:
    persons = entities["persons"]
    organizations = entities["organizations"]
    vehicles = entities["vehicles"]
    phones = entities["phones"]
    locations = entities["locations"]
    accounts = entities["accounts"]

    # --- partition persons into communities, each anchored by one org ---
    community_size = N_PERSONS // N_COMMUNITIES
    communities: list[list[dict]] = [
        persons[i * community_size:(i + 1) * community_size] for i in range(N_COMMUNITIES)
    ]
    anchor_orgs = organizations[:N_COMMUNITIES]
    person_community: dict[str, int] = {}
    for idx, group in enumerate(communities):
        for p in group:
            person_community[p["id"]] = idx

    relationships: list[dict] = []

    # --- WORKED_WITH: person -> anchor org ---
    for idx, group in enumerate(communities):
        org = anchor_orgs[idx]
        for p in group:
            relationships.append(_make_relationship(
                p["id"], "PERSON", org["id"], "ORGANIZATION", "WORKED_WITH",
                frequency=random.randint(1, 3), confidence=round(random.uniform(0.7, 0.95), 2),
                evidence=f"{p['name']} is recorded as affiliated with {org['name']}.",
            ))

    # --- intra-community person-person subgraph ---
    person_relation_types = ["KNOWS", "MET", "ASSOCIATED_WITH", "WORKED_WITH", "CALLED", "COMMUNICATED_WITH"]
    for group in communities:
        ids = [p["id"] for p in group]
        for p in group:
            peers = random.sample([i for i in ids if i != p["id"]], k=min(random.randint(2, 4), len(ids) - 1))
            for peer_id in peers:
                if random.random() < 0.5:  # avoid doubling every pair both directions
                    continue
                relation = random.choice(person_relation_types)
                relationships.append(_make_relationship(
                    p["id"], "PERSON", peer_id, "PERSON", relation,
                    frequency=random.randint(1, 6), confidence=round(random.uniform(0.55, 0.95), 2),
                    evidence=f"Recorded {relation.replace('_',' ').lower()} interaction between {p['id']} and {peer_id}.",
                ))

    # --- vehicles: mostly one owner/user, a handful deliberately shared across cases later ---
    vehicle_owner: dict[str, str] = {}
    shuffled_persons = persons[:]
    random.shuffle(shuffled_persons)
    for i, vehicle in enumerate(vehicles):
        owner = shuffled_persons[i % len(shuffled_persons)]
        vehicle_owner[vehicle["id"]] = owner["id"]
        relationships.append(_make_relationship(
            owner["id"], "PERSON", vehicle["id"], "VEHICLE", "USED",
            frequency=random.randint(1, 5), confidence=round(random.uniform(0.7, 0.97), 2),
            evidence=f"{owner['name']} was recorded using vehicle {vehicle['registration']}.",
        ))

    # --- phones: mostly 1:1, a few deliberately shared by 2-3 persons ---
    shared_phone_ids = {phones[i]["id"] for i in range(3)}
    for i, phone in enumerate(phones):
        owners = [shuffled_persons[i % len(shuffled_persons)]]
        if phone["id"] in shared_phone_ids:
            extra = random.sample([p for p in persons if p["id"] != owners[0]["id"]], k=2)
            owners += extra
        for owner in owners:
            relationships.append(_make_relationship(
                owner["id"], "PERSON", phone["id"], "PHONE", "USED",
                frequency=random.randint(1, 8), confidence=round(random.uniform(0.75, 0.98), 2),
                evidence=f"Phone {phone['number']} was recorded in use by {owner['name']}.",
            ))

    # --- accounts: subset of persons hold an account ---
    account_holders: dict[str, str] = {}
    for i, account in enumerate(accounts):
        holder = shuffled_persons[(i * 3) % len(shuffled_persons)]
        account_holders[account["id"]] = holder["id"]
        relationships.append(_make_relationship(
            holder["id"], "PERSON", account["id"], "ACCOUNT", "USED",
            frequency=random.randint(1, 4), confidence=round(random.uniform(0.7, 0.95), 2),
            evidence=f"{holder['name']} is the recorded holder of account {account['masked_number']}.",
        ))

    # --- financial transfers: build one guaranteed cycle + one high fan-out + random noise ---
    account_ids = [a["id"] for a in accounts]
    cycle = account_ids[:3]
    for a, b in zip(cycle, cycle[1:] + cycle[:1]):
        relationships.append(_make_relationship(
            a, "ACCOUNT", b, "ACCOUNT", "TRANSFERRED_TO",
            frequency=random.randint(1, 3), confidence=round(random.uniform(0.6, 0.9), 2),
            evidence=f"Fund transfer recorded from {a} to {b}.",
        ))
    fan_out_source = account_ids[3]
    for target in account_ids[4:8]:
        relationships.append(_make_relationship(
            fan_out_source, "ACCOUNT", target, "ACCOUNT", "TRANSFERRED_TO",
            frequency=random.randint(1, 2), confidence=round(random.uniform(0.6, 0.85), 2),
            evidence=f"Fund transfer recorded from {fan_out_source} to {target}.",
        ))
    for _ in range(8):
        a, b = random.sample(account_ids, 2)
        relationships.append(_make_relationship(
            a, "ACCOUNT", b, "ACCOUNT", "TRANSFERRED_TO",
            frequency=random.randint(1, 3), confidence=round(random.uniform(0.55, 0.9), 2),
            evidence=f"Fund transfer recorded from {a} to {b}.",
        ))

    # --- location visits, with a few repeated-movement pairs ---
    for group in communities:
        home_location = random.choice(locations)
        for p in group:
            visits = random.sample(locations, k=min(2, len(locations)))
            for loc in visits:
                relationships.append(_make_relationship(
                    p["id"], "PERSON", loc["id"], "LOCATION", random.choice(["TRAVELLED_TO", "MET"]),
                    frequency=random.randint(1, 3), confidence=round(random.uniform(0.6, 0.9), 2),
                    evidence=f"{p['name']} was recorded at {loc['name']}.",
                ))
        # repeated movement pattern for one representative person per community
        representative = group[0]
        relationships.append(_make_relationship(
            representative["id"], "PERSON", home_location["id"], "LOCATION", "TRAVELLED_TO",
            frequency=random.randint(4, 7), confidence=0.85,
            evidence=f"{representative['name']} shows a repeated travel pattern to {home_location['name']}.",
        ))

    # --- bridge relationships: deliberately connect otherwise separate communities ---
    for i in range(N_COMMUNITIES):
        bridge_person = communities[i][0]
        target_person = communities[(i + 1) % N_COMMUNITIES][1]
        relationships.append(_make_relationship(
            bridge_person["id"], "PERSON", target_person["id"], "PERSON", "ASSOCIATED_WITH",
            frequency=random.randint(1, 3), confidence=round(random.uniform(0.5, 0.8), 2),
            evidence=f"Cross-network association recorded between {bridge_person['id']} and {target_person['id']}.",
        ))

    # --- cases: 4 per community ---
    cases = []
    case_ids_by_community: list[list[str]] = [[] for _ in range(N_COMMUNITIES)]
    case_counter = 1001
    for community_idx in range(N_COMMUNITIES):
        for _ in range(CASES_PER_COMMUNITY):
            case_id = f"CASE-{case_counter}"
            case_counter += 1
            category = random.choice(CRIME_CATEGORIES)
            status = random.choices(["Active", "Under review", "Closed"], weights=[0.6, 0.25, 0.15])[0]
            priority = random.choices(["low", "normal", "high"], weights=[0.25, 0.45, 0.30])[0]
            risk_level = random.choices(["Low", "Medium", "High", "Critical"], weights=[0.2, 0.4, 0.3, 0.1])[0]
            cases.append({
                "id": case_id,
                "title": f"{category} -- {REGIONS[community_idx % len(REGIONS)]} Cluster {community_idx + 1}.{len(case_ids_by_community[community_idx]) + 1}",
                "description": f"Synthetic investigation into {category.lower()} activity linked to a network cluster in the {REGIONS[community_idx % len(REGIONS)]} region. All entities and events are fictional demonstration data.",
                "category": category,
                "status": status,
                "priority": priority,
                "risk_level": risk_level,
                "region": REGIONS[community_idx % len(REGIONS)],
                "assigned_investigator": random.choice(INVESTIGATORS),
                "opened_date": _rand_date(30, 640),
            })
            case_ids_by_community[community_idx].append(case_id)

    # --- tag relationships with a primary case from their community ---
    def community_of(entity_id: str, entity_type: str) -> int | None:
        if entity_type == "PERSON":
            return person_community.get(entity_id)
        if entity_type == "VEHICLE":
            owner = vehicle_owner.get(entity_id)
            return person_community.get(owner) if owner else None
        if entity_type == "ACCOUNT":
            holder = account_holders.get(entity_id)
            return person_community.get(holder) if holder else None
        if entity_type == "ORGANIZATION":
            idx = next((i for i, org in enumerate(anchor_orgs) if org["id"] == entity_id), None)
            return idx
        return None

    for rel in relationships:
        idx = community_of(rel["source_id"], rel["source_type"])
        if idx is None:
            idx = community_of(rel["target_id"], rel["target_type"])
        if idx is None:
            idx = random.randrange(N_COMMUNITIES)
        rel["case_id"] = random.choice(case_ids_by_community[idx])

    # --- duplicate-tag ~15 relationships into a second case, to create real
    #     "entity/vehicle appears in multiple cases" and cross-case connections ---
    duplicate_candidates = random.sample(relationships, k=min(15, len(relationships)))
    for rel in duplicate_candidates:
        other_community = random.randrange(N_COMMUNITIES)
        new_case_id = random.choice(case_ids_by_community[other_community])
        if new_case_id == rel["case_id"]:
            continue
        relationships.append(_make_relationship(
            rel["source_id"], rel["source_type"], rel["target_id"], rel["target_type"], rel["relation_type"],
            case_id=new_case_id, frequency=random.randint(1, 3), confidence=round(random.uniform(0.55, 0.85), 2),
            evidence=f"Also referenced under a separate investigation ({new_case_id}): {rel['evidence']}",
        ))

    # --- deliberately force 3 vehicles into a second, different case each,
    #     so "same vehicle appears across multiple cases" reliably fires ---
    forced_multi_case_vehicles = list(vehicle_owner.items())[:3]
    for vehicle_id, owner_id in forced_multi_case_vehicles:
        owner_community = person_community.get(owner_id, 0)
        other_community = (owner_community + 1) % N_COMMUNITIES
        new_case_id = case_ids_by_community[other_community][0]
        relationships.append(_make_relationship(
            owner_id, "PERSON", vehicle_id, "VEHICLE", "USED",
            case_id=new_case_id, frequency=random.randint(1, 3), confidence=round(random.uniform(0.65, 0.9), 2),
            evidence=f"Vehicle also referenced under a separate investigation ({new_case_id}).",
        ))

    # --- deliberately give 2 low-baseline-connectivity entities a burst of
    #     very recent, high-frequency communication so "unusual communication
    #     frequency" and "rapid connectivity change" reliably fire (picking
    #     the least-connected persons so far guarantees the burst clearly
    #     exceeds their historical baseline) ---
    baseline_connection_count: dict[str, int] = {}
    for rel in relationships:
        if rel["source_type"] == "PERSON":
            baseline_connection_count[rel["source_id"]] = baseline_connection_count.get(rel["source_id"], 0) + 1
        if rel["target_type"] == "PERSON":
            baseline_connection_count[rel["target_id"]] = baseline_connection_count.get(rel["target_id"], 0) + 1
    all_person_ids = [p["id"] for p in persons]
    burst_entities = sorted(all_person_ids, key=lambda pid: baseline_connection_count.get(pid, 0))[:2]
    for entity_id in burst_entities:
        home_community = person_community.get(entity_id, 0)
        added = 0
        while added < 11:
            peer = random.choice(communities[home_community])["id"]
            if peer == entity_id:
                continue
            added += 1
            relationships.append(_make_relationship(
                entity_id, "PERSON", peer, "PERSON", random.choice(["CALLED", "COMMUNICATED_WITH"]),
                case_id=case_ids_by_community[home_community][0],
                frequency=random.randint(3, 6), confidence=round(random.uniform(0.75, 0.95), 2),
                occurred_on=_rand_date(0, 10),
                evidence=f"High-frequency recent communication involving {entity_id}.",
            ))

    # --- events across cases ---
    all_relationships_by_case: dict[str, list[dict]] = {}
    for rel in relationships:
        all_relationships_by_case.setdefault(rel["case_id"], []).append(rel)

    event_type_titles = {
        "CALL": "Recorded phone call",
        "MEETING": "In-person meeting observed",
        "TRANSACTION": "Financial transaction recorded",
        "TRAVEL": "Travel movement recorded",
        "CASE_EVENT": "Case milestone recorded",
        "EVIDENCE_EVENT": "Evidence intake recorded",
    }
    events = []
    events_per_case = max(1, N_EVENTS // N_CASES)
    # a couple of "hot" entities get a burst of very recent CALL events (sudden-increase rule)
    hot_entities = [communities[0][0]["id"], communities[2][1]["id"]]

    for case in cases:
        case_id = case["id"]
        case_rels = all_relationships_by_case.get(case_id, [])
        entity_pool = sorted({r["source_id"] for r in case_rels} | {r["target_id"] for r in case_rels}) or [case_id]
        for _ in range(events_per_case):
            event_type = random.choices(
                list(event_type_titles.keys()), weights=[0.3, 0.2, 0.15, 0.15, 0.1, 0.1]
            )[0]
            related = random.sample(entity_pool, k=min(random.choice([1, 1, 2]), len(entity_pool)))
            force_night = random.random() < 0.08
            events.append({
                "id": _new_evt_id(),
                "case_id": case_id,
                "event_type": event_type,
                "title": f"{event_type_titles[event_type]} ({case_id})",
                "description": f"{event_type_titles[event_type]} involving {', '.join(related)}.",
                "timestamp": _rand_datetime(1, 300, force_night=force_night),
                "location_id": random.choice(locations)["id"] if random.random() < 0.4 else "",
                "related_entities": related,
                "source": "Synthetic demo dataset",
            })

    # deliberately concentrate several recent CALL events + night events on hot entities
    for entity_id in hot_entities:
        home_case = next((c["id"] for c in cases if entity_id in
                           ({r["source_id"] for r in all_relationships_by_case.get(c["id"], [])} |
                            {r["target_id"] for r in all_relationships_by_case.get(c["id"], [])})), cases[0]["id"])
        for _ in range(4):
            events.append({
                "id": _new_evt_id(), "case_id": home_case, "event_type": "CALL",
                "title": f"Recorded phone call ({home_case})",
                "description": f"Recent call activity involving {entity_id}.",
                "timestamp": _rand_datetime(0, 10), "location_id": "",
                "related_entities": [entity_id], "source": "Synthetic demo dataset",
            })
        for _ in range(2):
            events.append({
                "id": _new_evt_id(), "case_id": home_case, "event_type": "MEETING",
                "title": f"In-person meeting observed ({home_case})",
                "description": f"Late-hour activity involving {entity_id}.",
                "timestamp": _rand_datetime(1, 60, force_night=True), "location_id": "",
                "related_entities": [entity_id], "source": "Synthetic demo dataset",
            })

    # --- evidence records, 1-2 per case ---
    evidence_types = ["Document", "Call Log Extract", "Transaction Record", "Field Statement", "Surveillance Note"]
    evidence = []
    for case in cases:
        for _ in range(random.choice([1, 1, 2])):
            description = f"{random.choice(evidence_types)} associated with {case['id']}, entered into the synthetic evidence log."
            ev_id = _new_ev_id()
            evidence.append({
                "id": ev_id,
                "case_id": case["id"],
                "entity_id": "",
                "evidence_type": random.choice(evidence_types),
                "description": description,
                "sha256_hash": hashlib.sha256(f"{ev_id}:{description}".encode()).hexdigest(),
                "source": "Synthetic demo dataset",
                "uploaded_by": random.choice(INVESTIGATORS),
                "uploaded_at": _rand_datetime(1, 300),
            })

    # --- demo users (plaintext demo passwords here; hashed at seed-insert time) ---
    users = [
        {"id": "USER-001", "username": "admin.demo", "full_name": "A. Administrator", "email": "admin.demo@ncrb.example",
         "role": "ADMINISTRATOR", "password": "AdminDemo@123"},
        {"id": "USER-002", "username": "investigator.demo", "full_name": "A. Sen", "email": "investigator.demo@ncrb.example",
         "role": "INVESTIGATOR", "password": "InvestigatorDemo@123"},
        {"id": "USER-003", "username": "analyst.demo", "full_name": "R. Krishnan", "email": "analyst.demo@ncrb.example",
         "role": "ANALYST", "password": "AnalystDemo@123"},
    ]

    return {
        "users": users,
        "cases": cases,
        "persons": persons,
        "organizations": organizations,
        "vehicles": vehicles,
        "phones": phones,
        "locations": locations,
        "accounts": accounts,
        "relationships": relationships,
        "events": events,
        "evidence": evidence,
    }


def generate() -> dict:
    return _assemble(_base_entities())


if __name__ == "__main__":
    data = generate()
    for key, value in data.items():
        print(f"{key:16s}: {len(value):4d} records")
    print(f"\nTotal relationships >= 100 required: {len(data['relationships'])}")
