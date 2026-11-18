from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_rejects_invalid_request_without_link():
    response = client.post("/posting", json={"message": "A message without a CTA"})
    assert response.status_code == 422


def test_rejects_two_cta_links():
    response = client.post("/posting", json={"message": "https://one.example https://two.example"})
    assert response.status_code == 422


def test_posting_attempts_every_configured_platform(monkeypatch):
    from app import main
    from app.schemas import PlatformResult

    async def fake_publish(message):
        return [
            PlatformResult(platform="One", status="success", posted_url="https://social.example/p/1", public_access=True, date="2026-11-18", time="10:00:00Z"),
            PlatformResult(platform="Two", status="failed", error="Credentials are not configured."),
        ]

    monkeypatch.setattr(main, "publish_everywhere", fake_publish)
    response = client.post("/posting", json={"message": "Read this update: https://example.com"})
    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert [item["platform"] for item in payload["results"]] == ["One", "Two"]
    assert payload["results"][1]["status"] == "failed"


def test_overall_success_is_false_when_every_platform_fails(monkeypatch):
    from app import main
    from app.schemas import PlatformResult

    async def fake_publish(message):
        return [
            PlatformResult(platform=name, status="failed", error="Not configured.")
            for name in ["LinkedIn", "Mastodon", "Bluesky", "WordPress", "Telegram"]
        ]

    monkeypatch.setattr(main, "publish_everywhere", fake_publish)
    response = client.post("/posting", json={"message": "Read this: https://example.com"})
    assert response.status_code == 200
    assert response.json()["success"] is False
    assert len(response.json()["results"]) == 5
