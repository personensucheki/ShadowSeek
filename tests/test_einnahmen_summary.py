
import pytest
from app import create_app

@pytest.fixture
def client():
    app = create_app()
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_einnahmen_summary_empty_state(client):
    """
    Regression: /api/einnahmen/summary returns 200 OK, normalized envelope, and safe empty payload
    """
    response = client.get('/api/einnahmen/summary')
    assert response.status_code == 200
    data = response.get_json()
    assert data is not None
    assert data.get('success') is True
    assert 'data' in data
    # Check for expected empty-state fields
    payload = data['data']
    assert isinstance(payload, dict)
    assert payload.get('active_creators', 0) == 0
    assert payload.get('record_count', 0) == 0
    assert payload.get('total_revenue', 0.0) == 0.0
    assert isinstance(payload.get('labels', []), list)
    assert isinstance(payload.get('values', []), list)
    # No NameError or crash
    # No 500 error
