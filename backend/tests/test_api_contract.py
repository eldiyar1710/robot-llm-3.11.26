from fastapi.testclient import TestClient

from app.main import create_app


def test_liveness_and_readiness_are_distinct() -> None:
    with TestClient(create_app()) as client:
        live = client.get("/api/v1/health/live")
        ready = client.get("/api/v1/health/ready")
    assert live.status_code == 200
    assert live.json()["status"] == "alive"
    assert ready.status_code == 503
    assert ready.json()["error"]["code"] == "SERVICE_NOT_READY"
    assert ready.json()["error"]["request_id"] == ready.headers["X-Request-ID"]


def test_text_question_never_invents_unindexed_university_facts() -> None:
    with TestClient(create_app()) as client:
        response = client.post(
            "/api/v1/dialog/text", json={"question": "Кто ректор?", "language": "ru"}
        )
    assert response.status_code == 503
    assert response.json()["error"]["code"] == "KNOWLEDGE_NOT_READY"


def test_invalid_language_uses_error_contract() -> None:
    with TestClient(create_app()) as client:
        response = client.post("/api/v1/dialog/text", json={"question": "Hello", "language": "de"})
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"


def test_openapi_has_unique_operation_ids_and_error_models() -> None:
    with TestClient(create_app()) as client:
        schema = client.get("/openapi.json").json()
    operations = [value for path in schema["paths"].values() for value in path.values()]
    ids = [operation["operationId"] for operation in operations]
    assert len(ids) == len(set(ids))
    assert "ErrorResponse" in schema["components"]["schemas"]
    assert "/api/v1/dialog/text" in schema["paths"]


def test_unknown_route_uses_error_contract() -> None:
    with TestClient(create_app()) as client:
        response = client.get("/api/v1/unknown")
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "NOT_FOUND"
