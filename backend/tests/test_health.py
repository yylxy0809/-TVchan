from fastapi.testclient import TestClient
from tvchan.bootstrap.api import app


def test_health_is_independent_of_external_services() -> None:
    response = TestClient(app).get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
