from fastapi.testclient import TestClient
from backend.main import app


def test_home_redirects_to_dashboard_when_bundled():
    with TestClient(app) as client:
        response = client.get("/", follow_redirects=False)
        assert response.status_code in (200, 307)
        if response.status_code == 307:
            assert response.headers["location"] == "/dashboard/demo.html"
            demo = client.get("/dashboard/demo.html")
            assert demo.status_code == 200
            assert "NEXUS" in demo.text


def test_health_stays_public():
    with TestClient(app) as client:
        assert client.get("/health").json()["status"] == "ok"
