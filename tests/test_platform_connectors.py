import asyncio
from types import SimpleNamespace

import pytest

from app.config import settings
from app.platforms import bluesky, linkedin, mastodon, telegram, wordpress


class FakeResponse:
    def __init__(self, status_code=200, payload=None, headers=None):
        self.status_code = status_code
        self._payload = payload or {}
        self.headers = headers or {}
        self.text = ""

    def json(self):
        return self._payload


class FakeClient:
    def __init__(self, *args, **kwargs):
        self.calls = 0

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        return False

    async def post(self, url, *args, **kwargs):
        self.calls += 1
        if "createSession" in url:
            return FakeResponse(payload={"did": "did:plc:abc", "accessJwt": "test-jwt"})
        if "createRecord" in url:
            return FakeResponse(payload={"uri": "at://did:plc:abc/app.bsky.feed.post/record123"})
        if "sendMessage" in url:
            return FakeResponse(payload={"ok": True, "result": {"chat": {"username": "demo_channel"}, "message_id": 42}})
        if "api/v1/statuses" in url:
            return FakeResponse(payload={"url": "https://mastodon.example/@demo/123"})
        if "wp-json/wp/v2/posts" in url:
            return FakeResponse(status_code=201, payload={"link": "https://blog.example/update/"})
        if "api.linkedin.com/rest/posts" in url:
            return FakeResponse(status_code=201, headers={"x-restli-id": "urn:li:share:123"})
        raise AssertionError(f"Unexpected API URL in test: {url}")


@pytest.fixture
def fake_httpx(monkeypatch):
    monkeypatch.setattr("app.platforms.linkedin.httpx.AsyncClient", FakeClient)
    monkeypatch.setattr("app.platforms.mastodon.httpx.AsyncClient", FakeClient)
    monkeypatch.setattr("app.platforms.bluesky.httpx.AsyncClient", FakeClient)
    monkeypatch.setattr("app.platforms.wordpress.httpx.AsyncClient", FakeClient)
    monkeypatch.setattr("app.platforms.telegram.httpx.AsyncClient", FakeClient)


def test_linkedin_connector(fake_httpx, monkeypatch):
    monkeypatch.setattr(settings, "linkedin_access_token", "token")
    monkeypatch.setattr(settings, "linkedin_author_urn", "urn:li:person:123")
    result = asyncio.run(linkedin.post("Hello https://example.com"))
    assert result.status == "success"
    assert result.posted_url.endswith("urn:li:share:123")


def test_mastodon_connector(fake_httpx, monkeypatch):
    monkeypatch.setattr(settings, "mastodon_access_token", "token")
    monkeypatch.setattr(settings, "mastodon_base_url", "https://mastodon.example")
    result = asyncio.run(mastodon.post("Hello https://example.com"))
    assert result.status == "success"
    assert result.public_access is True


def test_bluesky_connector(fake_httpx, monkeypatch):
    monkeypatch.setattr(settings, "bluesky_handle", "demo.bsky.social")
    monkeypatch.setattr(settings, "bluesky_app_password", "app-password")
    result = asyncio.run(bluesky.post("Hello https://example.com"))
    assert result.status == "success"
    assert result.posted_url.endswith("/post/record123")


def test_wordpress_connector(fake_httpx, monkeypatch):
    monkeypatch.setattr(settings, "wordpress_base_url", "https://blog.example")
    monkeypatch.setattr(settings, "wordpress_username", "publisher")
    monkeypatch.setattr(settings, "wordpress_app_password", "application-password")
    result = asyncio.run(wordpress.post("Hello https://example.com"))
    assert result.status == "success"
    assert result.posted_url == "https://blog.example/update/"


def test_telegram_connector(fake_httpx, monkeypatch):
    monkeypatch.setattr(settings, "telegram_bot_token", "bot-token")
    monkeypatch.setattr(settings, "telegram_chat_id", "@demo_channel")
    result = asyncio.run(telegram.post("Hello https://example.com"))
    assert result.status == "success"
    assert result.posted_url == "https://t.me/demo_channel/42"


def test_wordpress_refuses_http_before_sending_credentials(monkeypatch):
    monkeypatch.setattr(settings, "wordpress_base_url", "http://blog.example")
    monkeypatch.setattr(settings, "wordpress_username", "publisher")
    monkeypatch.setattr(settings, "wordpress_app_password", "secret")
    result = asyncio.run(wordpress.post("Hello https://example.com"))
    assert result.status == "failed"
    assert "HTTPS" in result.error


def test_mastodon_refuses_http_instance(monkeypatch):
    monkeypatch.setattr(settings, "mastodon_base_url", "http://mastodon.example")
    monkeypatch.setattr(settings, "mastodon_access_token", "secret")
    result = asyncio.run(mastodon.post("Hello https://example.com"))
    assert result.status == "failed"
    assert "HTTPS" in result.error
