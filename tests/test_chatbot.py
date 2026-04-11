import pytest
from app import create_app
import json

@pytest.fixture
def client():
    app = create_app()
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client

def test_greeting(client):
    resp = client.post("/api/chatbot", json={"message": "Hallo"})
    data = resp.get_json()
    assert resp.status_code == 200
    assert "Hallo!" in data["reply"]

def test_help(client):
    resp = client.post("/api/chatbot", json={"message": "hilfe"})
    data = resp.get_json()
    assert resp.status_code == 200
    assert "ShadowSeek findet Profile" in data["reply"]

def test_fallback_explanation(client):
    resp = client.post("/api/chatbot", json={"message": "Warum war vorher Fallback?"})
    data = resp.get_json()
    assert resp.status_code == 200
    assert "Fallback-Modus" in data["reply"]

def test_context_response(client):
    context = {
        "query": "testuser",
        "platforms": ["github", "twitter"],
        "results": [{"id": 1}],
        "deepsearch": True
    }
    resp = client.post("/api/chatbot", json={"message": "", "context": context})
    data = resp.get_json()
    assert resp.status_code == 200
    assert "Letzte Suche" in data["reply"]
    assert "DeepSearch war aktiviert" in data["reply"]

def test_no_context_standard_help(client):
    resp = client.post("/api/chatbot", json={"message": "Unbekannte Frage"})
    data = resp.get_json()
    assert resp.status_code == 200
    assert "ShadowSeek findet Profile" in data["reply"]

def test_no_openai_key_rule_mode(client):
    # Simuliere fehlenden Key
    app = create_app()
    app.config["OPENAI_API_KEY"] = None
    with app.test_client() as client2:
        resp = client2.post("/api/chatbot", json={"message": "Hallo"})
        data = resp.get_json()
        assert resp.status_code == 200
        assert "Hallo!" in data["reply"]

def test_no_503_anymore(client):
    resp = client.post("/api/chatbot", json={"message": "Hallo"})
    assert resp.status_code == 200
