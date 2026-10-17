from fastapi.testclient import TestClient
from backend.main import app
c=TestClient(app)
def test_health(): assert c.get('/healthz').status_code==200
def test_no_login(): assert c.get('/api/auth/status').json()['authenticated'] is True
