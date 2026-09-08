from datetime import datetime, timezone
from hashlib import sha256
from typing import Any

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from app.ai.entity_extraction import extract_entities
from app.ai.network_analysis import calculate_metrics
from app.ai.explanation_engine import explain_metric
from app.ai.crime_dataset import crime_analysis
from app.integrations import integration_status
from app.data import NOW, NAMES, ORG_NAMES, LOC_NAMES, create_nodes, create_edges, CASES, ALERTS, COMMUNITIES
from app.config import settings
from app.logging_config import logger

app = FastAPI(title=settings.API_TITLE, version=settings.API_VERSION)
app.add_middleware(CORSMiddleware, allow_origins=settings.CORS_ORIGINS, allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

NODES = create_nodes()
EDGES = create_edges(NODES)
METRICS = calculate_metrics(NODES, EDGES)
for case in CASES:
    if case["id"] == "CASE-001":
        case["relationships"] = len(EDGES)

class ReviewRequest(BaseModel):
    relationship_id: str
    decision: str = Field(pattern="^(accepted|rejected|uncertain)$")

class NoteRequest(BaseModel):
    content: str = Field(..., min_length=1, max_length=5000)
    priority: str = Field(default="normal", pattern="^(low|normal|high)$")

ENTITY_NOTES: dict[str, list[dict[str, Any]]] = {}
RELATIONSHIP_NOTES: dict[str, list[dict[str, Any]]] = {}

@app.get("/")
def root():
    return {"service": "NETRA API", "status": "ok", "health": "/api/health", "docs": "/docs"}

@app.get("/api/health")
def health():
    integrations = integration_status()
    return {"status":"ok", "mode":"synthetic-demo", "integrations": integrations.__dict__}

@app.post("/api/auth/login")
def login(payload: dict[str, str]):
    if payload.get("username") not in {"admin", "investigator", "analyst"} or payload.get("password") != "netra-demo":
        raise HTTPException(401, "Invalid demo credentials")
    return {"access_token":"demo-token","token_type":"bearer","user":{"name":"A. Sen","role":"Senior Investigator"}}

@app.get("/api/dashboard")
def dashboard():
    return {"kpis":[{"label":"Active cases","value":"08","delta":"+2 this month"},{"label":"Persons of interest","value":"30","delta":"+4 this week"},{"label":"Connected entities","value":"87","delta":"Across 3 communities"},{"label":"Risk indicators","value":"12","delta":"3 require review"}],"alerts":ALERTS,"top_entities":[{"id":node["id"],"label":node["label"],"score":round(METRICS.get(node["id"],{}).get("betweenness",0)*100,1)} for node in NODES if node["type"] == "PERSON"][:6]}

@app.get("/api/crime-analysis")
def crime_dataset_analysis():
    return crime_analysis()

@app.get("/api/cases")
def cases(): return CASES
@app.get("/api/cases/{case_id}")
def case(case_id: str):
    found = next((item for item in CASES if item["id"] == case_id), None)
    if not found: raise HTTPException(404, "Case not found")
    return {**found, "description":"Synthetic intelligence records for an investigator-assistance demonstration.", "disclaimer":"Analytical scores and inferred relationships are not proof of criminal activity or guilt."}

@app.get("/api/graph/case/{case_id}")
def graph(case_id: str, depth: int = 2):
    return {"nodes":NODES,"edges":EDGES,"metrics":METRICS,"communities":COMMUNITIES,"depth":min(depth,3)}

@app.get("/api/entities")
def entities(q: str = ""):
    query = q.lower().strip()
    return [{**node, "connections": sum(node["id"] in (e["source"],e["target"]) for e in EDGES), "metrics":METRICS.get(node["id"],{})} for node in NODES if not query or query in node["id"].lower() or query in node["label"].lower()]

@app.get("/api/entities/{entity_id}")
def entity(entity_id: str):
    found = next((node for node in NODES if node["id"] == entity_id), None)
    if not found: raise HTTPException(404, "Entity not found")
    metrics = METRICS.get(entity_id, {})
    betweenness = metrics.get("betweenness", 0) if isinstance(metrics.get("betweenness"), (int, float)) else 0
    score = min(100, round(betweenness * 100 + 52))
    entity_data = {**found, "connections": sum(entity_id in (e["source"], e["target"]) for e in EDGES)}
    result = {**entity_data, "metrics": metrics, "score": score, "insight": explain_metric(entity_data, metrics), "evidence": [e for e in EDGES if entity_id in (e["source"], e["target"])][:6]}
    return result

@app.get("/api/alerts")
def alerts(): return ALERTS

@app.get("/api/timeline")
def timeline(case_id: str = "CASE-001"):
    if case_id != "CASE-001": raise HTTPException(404, "Case timeline not found")
    events = [{"id": edge["id"], "timestamp": edge["timestamp"], "kind": "relationship", "title": f"{edge['source']} {edge['relation']} {edge['target']}", "description": edge["evidence"], "confidence": edge["confidence"], "source": edge["id"]} for edge in EDGES]
    events.extend({"id": alert["id"], "timestamp": NOW, "kind": "alert", "title": alert["title"], "description": alert["explanation"], "confidence": None, "source": alert["id"]} for alert in ALERTS)
    return {"case_id": case_id, "events": sorted(events, key=lambda e: e["timestamp"], reverse=True)}

@app.get("/api/review")
def review(): return [{"id": "REL-041", "source":"P014", "target":"P025", "relation":"ASSOCIATED_WITH", "confidence":0.87, "evidence":"Person P014 was observed meeting Person P025 near Cedar Junction.", "status":"Pending review"},{"id":"REL-044","source":"P010","target":"P011","relation":"CALLED", "confidence":0.91, "evidence":"CDR records show repeated calls within a two-hour window.", "status":"Pending review"}]
@app.post("/api/relationships/review")
def review_relationship(payload: ReviewRequest): return {"status":"recorded","relationship_id":payload.relationship_id,"decision":payload.decision,"reviewer":"demo-user","timestamp":NOW}

@app.post("/api/documents/upload")
async def upload_document(file: UploadFile = File(...)):
    if not file.filename or file.filename.split(".")[-1].lower() not in {"txt","csv","json","pdf"}: raise HTTPException(400,"Supported files: PDF, TXT, CSV, JSON")
    content = await file.read()
    if len(content) > 10 * 1024 * 1024: raise HTTPException(413,"Maximum upload size is 10 MB")
    is_pdf = file.filename.lower().endswith(".pdf")
    if is_pdf and not content.startswith(b"%PDF"): raise HTTPException(400,"Invalid PDF file")
    text = content.decode("utf-8", errors="ignore") if not is_pdf else ""
    return {"id":"DOC-009","filename":file.filename,"status":"Complete","size":len(content),"entities":extract_entities(text),"relationships":[],"hash":sha256(content).hexdigest(),"timestamp":NOW}

@app.post("/api/evidence/{evidence_id}/verify")
def verify_evidence(evidence_id: str): return {"evidence_id":evidence_id,"status":"VERIFIED","hash":"7f2b...c91a","chain_hash":"b12e...8d44","verified_at":NOW}

@app.post("/api/reports/generate")
def report(payload: dict[str, str] = {}): return {"status":"ready","case_id":payload.get("case_id","CASE-001"),"format":"json","sections":["Case Information","Network Overview","Analytical Observations","Evidence Integrity","Limitations"],"disclaimer":"This report is an analytical aid and does not establish criminal responsibility."}

@app.post("/api/entities/{entity_id}/notes")
def add_entity_note(entity_id: str, payload: NoteRequest):
    found = next((node for node in NODES if node["id"] == entity_id), None)
    if not found: raise HTTPException(404, "Entity not found")
    note = {"id": f"NOTE-{len(ENTITY_NOTES.get(entity_id, []))+1:03}", "content": payload.content, "priority": payload.priority, "created": NOW, "author": "demo-user"}
    if entity_id not in ENTITY_NOTES: ENTITY_NOTES[entity_id] = []
    ENTITY_NOTES[entity_id].append(note)
    return note

@app.get("/api/entities/{entity_id}/notes")
def get_entity_notes(entity_id: str):
    found = next((node for node in NODES if node["id"] == entity_id), None)
    if not found: raise HTTPException(404, "Entity not found")
    return {"entity_id": entity_id, "notes": ENTITY_NOTES.get(entity_id, [])}

@app.post("/api/relationships/{rel_id}/notes")
def add_relationship_note(rel_id: str, payload: NoteRequest):
    found = next((e for e in EDGES if e["id"] == rel_id), None)
    if not found: raise HTTPException(404, "Relationship not found")
    note = {"id": f"NOTE-{len(RELATIONSHIP_NOTES.get(rel_id, []))+1:03}", "content": payload.content, "priority": payload.priority, "created": NOW, "author": "demo-user"}
    if rel_id not in RELATIONSHIP_NOTES: RELATIONSHIP_NOTES[rel_id] = []
    RELATIONSHIP_NOTES[rel_id].append(note)
    return note

@app.get("/api/relationships/{rel_id}/notes")
def get_relationship_notes(rel_id: str):
    found = next((e for e in EDGES if e["id"] == rel_id), None)
    if not found: raise HTTPException(404, "Relationship not found")
    return {"relationship_id": rel_id, "notes": RELATIONSHIP_NOTES.get(rel_id, [])}
