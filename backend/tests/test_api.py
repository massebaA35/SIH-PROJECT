from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_health():
    response = client.get('/api/health')
    assert response.status_code == 200
    assert response.json()['status'] == 'ok'

def test_case_graph_has_synthetic_network():
    response = client.get('/api/graph/case/CASE-001')
    assert response.status_code == 200
    body = response.json()
    assert len(body['nodes']) >= 40
    assert len(body['edges']) >= 50

def test_entity_exposes_evidence_and_explanation():
    response = client.get('/api/entities/P014')
    assert response.status_code == 200
    body = response.json()
    assert body['evidence']
    assert 'not a finding of wrongdoing' in body['insight'] or 'Review' in body['insight']
