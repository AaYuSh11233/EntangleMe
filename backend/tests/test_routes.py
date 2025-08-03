import pytest
from app import create_app

@pytest.fixture
def client():
    app = create_app()
    app.testing = True
    return app.test_client()

def test_teleport_0(client):
    response = client.post("/teleport", json={"state": "0"})
    assert response.status_code == 200
    data = response.get_json()
    assert "counts" in data

def test_teleport_1(client):
    response = client.post("/teleport", json={"state": "1"})
    assert response.status_code == 200
    data = response.get_json()
    assert "counts" in data
