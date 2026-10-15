from fastapi.testclient import TestClient
from backend.main import app

def test_health():
    with TestClient(app) as c:
        r=c.get('/healthz'); assert r.status_code==200; assert r.json()['status']=='ok'

def test_safe_settings():
    with TestClient(app) as c:
        data=c.get('/api/settings').json()
        assert data['management_interface']=='wlan0'
        assert data['scanner_interface']=='wlan1'
        assert data['active_radio_changes_enabled'] is False
