import asyncio
from app.schemas import PlatformResult
from app.services import posting_service


def test_one_connector_exception_does_not_stop_others(monkeypatch):
    async def raises(message):
        raise RuntimeError("test-only failure")

    async def succeeds(message):
        return PlatformResult(platform="Working", status="success", public_access=False)

    monkeypatch.setattr(posting_service, "PLATFORM_POSTERS", [raises, succeeds])
    results = asyncio.run(posting_service.publish_everywhere("Hello https://example.com"))
    assert len(results) == 2
    assert results[0].status == "failed"
    assert results[1].status == "success"


def test_application_has_five_platform_connectors():
    assert len(posting_service.PLATFORM_POSTERS) == 5
