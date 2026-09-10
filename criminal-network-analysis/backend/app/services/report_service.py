"""Investigation report generation, including a PDF export.

Every report is clearly labeled as AI-assisted analytical output per brief
section M, and every finding it lists carries the same explicit label
vocabulary used everywhere else in the platform.
"""
from datetime import datetime, timezone

from fpdf import FPDF
from sqlalchemy.orm import Session

from app.analytics.centrality import compute_centrality, explain_entity_score, identify_bridge_entities
from app.analytics.community import detect_communities
from app.graph.graph_builder import build_case_graph
from app.models.alert import Alert
from app.models.case import Case
from app.models.evidence import Evidence
from app.models.event import Event
from app.models.relationship import Relationship
from app.services.entity_service import get_entity_detail

AI_LABEL = "AI-Assisted Analytical Output — Requires Investigator Verification"


def build_report(db: Session, case_id: str, investigator_notes: str = "") -> dict:
    case = db.get(Case, case_id)
    if not case:
        return None

    edges = db.query(Relationship).filter(Relationship.case_id == case_id).all()
    events = db.query(Event).filter(Event.case_id == case_id).order_by(Event.timestamp.asc()).all()
    alerts = db.query(Alert).filter(Alert.case_id == case_id).all()
    evidence_records = db.query(Evidence).filter(Evidence.case_id == case_id).all()

    graph = build_case_graph(db, case_id)
    metrics = compute_centrality(graph)
    communities, community_summary = detect_communities(graph)
    bridges = set(identify_bridge_entities(graph, communities))

    key_entities = []
    for node_id in sorted(graph.nodes, key=lambda n: metrics.get(n, {}).get("degree_centrality", 0), reverse=True)[:8]:
        detail = get_entity_detail(db, node_id)
        label = detail["label"] if detail else node_id
        related_case_count = len(detail["related_cases"]) if detail else 1
        explanation = explain_entity_score(node_id, label, metrics.get(node_id, {}), related_case_count, node_id in bridges, graph.number_of_nodes())
        key_entities.append(explanation)

    relationship_types: dict[str, int] = {}
    for e in edges:
        relationship_types[e.relation_type] = relationship_types.get(e.relation_type, 0) + 1

    return {
        "report_label": AI_LABEL,
        "case_id": case.id,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "case_information": {
            "title": case.title,
            "description": case.description,
            "category": case.category,
            "status": case.status,
            "priority": case.priority,
            "risk_level": case.risk_level,
            "region": case.region,
            "assigned_investigator": case.assigned_investigator,
            "opened_date": case.opened_date.isoformat(),
        },
        "network_statistics": {
            "entities_tracked": graph.number_of_nodes(),
            "relationships_recorded": graph.number_of_edges(),
            "relationship_breakdown": relationship_types,
            "communities_detected": len(community_summary),
            "bridge_entities": sorted(bridges),
        },
        "key_relationships": [
            {
                "source": e.source_id, "target": e.target_id, "relation_type": e.relation_type,
                "date": e.occurred_on.isoformat(), "confidence": e.confidence, "evidence": e.evidence,
                "label": "Potential connection",
            }
            for e in sorted(edges, key=lambda r: r.confidence, reverse=True)[:10]
        ],
        "timeline": [
            {"id": ev.id, "type": ev.event_type, "title": ev.title, "timestamp": ev.timestamp.isoformat(), "description": ev.description}
            for ev in events
        ],
        "alerts": [
            {"id": a.id, "severity": a.severity, "label": a.label, "title": a.title, "evidence": a.evidence, "status": a.status}
            for a in alerts
        ],
        "geographic_summary": _geographic_summary(db, edges),
        "ai_analytical_observations": key_entities,
        "evidence_references": [
            {"id": ev.id, "type": ev.evidence_type, "description": ev.description, "hash": ev.sha256_hash, "source": ev.source}
            for ev in evidence_records
        ],
        "investigator_notes": investigator_notes,
        "disclaimer": (
            "This report is an investigative decision-support aid. AI-generated findings are presented as "
            "potential connections, risk indicators, and analytical leads only -- never as proof of guilt -- "
            "and every finding requires independent investigator verification against authorized evidence."
        ),
    }


def _geographic_summary(db: Session, edges: list[Relationship]) -> list[dict]:
    from app.models.entities import Location
    location_ids = sorted({e.target_id for e in edges if e.target_type == "LOCATION"} | {e.source_id for e in edges if e.source_type == "LOCATION"})
    summary = []
    for loc_id in location_ids:
        loc = db.get(Location, loc_id)
        if loc:
            summary.append({"id": loc.id, "name": loc.name, "region": loc.region, "latitude": loc.latitude, "longitude": loc.longitude})
    return summary


_PDF_CHAR_MAP = {
    "—": "-", "–": "-",  # em dash, en dash
    "‘": "'", "’": "'",  # curly single quotes
    "“": '"', "”": '"',  # curly double quotes
    "·": "-", "•": "-",  # middot, bullet
    "…": "...",  # ellipsis
}


def _pdf_safe(value):
    """fpdf2's built-in Helvetica font only supports Latin-1. Our JSON/UI
    text uses a few common Unicode punctuation marks (em dash, middot,
    curly quotes); map those to ASCII equivalents and fall back to
    dropping anything else so PDF generation never crashes on them."""
    if isinstance(value, str):
        for unicode_char, ascii_char in _PDF_CHAR_MAP.items():
            value = value.replace(unicode_char, ascii_char)
        return value.encode("latin-1", "replace").decode("latin-1")
    if isinstance(value, dict):
        return {k: _pdf_safe(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_pdf_safe(v) for v in value]
    return value


def render_pdf(report: dict) -> bytes:
    report = _pdf_safe(report)
    pdf = FPDF()
    pdf.add_page()

    def block(text: str, height: int = 6):
        """multi_cell in this fpdf2 version leaves the X cursor wherever the
        last line ended rather than resetting it to the left margin, which
        starves the *next* full-width call of horizontal space. Resetting X
        explicitly before every call keeps each block a full-width paragraph."""
        pdf.set_x(pdf.l_margin)
        pdf.multi_cell(0, height, text)

    pdf.set_font("Helvetica", "B", 16)
    block(f"Investigation Report: {report['case_information']['title']} ({report['case_id']})", 8)
    pdf.set_font("Helvetica", "I", 10)
    pdf.set_text_color(180, 30, 30)
    block(report["report_label"])
    pdf.set_text_color(0, 0, 0)
    pdf.ln(2)

    def section(title: str):
        pdf.set_font("Helvetica", "B", 12)
        pdf.ln(3)
        pdf.set_x(pdf.l_margin)
        pdf.cell(0, 8, title, new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("Helvetica", "", 10)

    section("Case Information")
    ci = report["case_information"]
    block(f"Status: {ci['status']} | Priority: {ci['priority']} | Risk level: {ci['risk_level']}\n"
          f"Category: {ci['category']} | Region: {ci['region']} | Investigator: {ci['assigned_investigator']}\n"
          f"Opened: {ci['opened_date']}\n{ci['description']}")

    section("Network Statistics")
    ns = report["network_statistics"]
    block(f"Entities tracked: {ns['entities_tracked']} | Relationships: {ns['relationships_recorded']} | "
          f"Communities detected: {ns['communities_detected']}\nBridge entities: {', '.join(ns['bridge_entities']) or 'None identified'}")

    section("AI-Assisted Analytical Observations (Requires Investigator Verification)")
    if report["ai_analytical_observations"]:
        for obs in report["ai_analytical_observations"]:
            block(f"- {obs['entity_label']} ({obs['entity_id']}): {obs['finding_label']}, "
                  f"connectivity score {obs['network_connectivity_score']}/100. {obs['analytical_interpretation']}")
    else:
        block("No analytical observations available for this case.")

    section("Key Relationships")
    if report["key_relationships"]:
        for rel in report["key_relationships"]:
            block(f"- {rel['source']} {rel['relation_type']} {rel['target']} on {rel['date']} "
                  f"(confidence {round(rel['confidence']*100)}%): {rel['evidence']}")
    else:
        block("No relationships recorded for this case.")

    section("Alerts")
    if report["alerts"]:
        for alert in report["alerts"]:
            block(f"- [{alert['severity']}/{alert['label']}] {alert['title']}: {alert['evidence']} (status: {alert['status']})")
    else:
        block("No alerts recorded for this case.")

    section("Timeline")
    if report["timeline"]:
        for ev in report["timeline"][:25]:
            block(f"- {ev['timestamp']}: [{ev['type']}] {ev['title']}")
    else:
        block("No timeline events recorded for this case.")

    section("Investigator Notes")
    block(report["investigator_notes"] or "(none entered)")

    section("Disclaimer")
    block(report["disclaimer"])

    return bytes(pdf.output())
