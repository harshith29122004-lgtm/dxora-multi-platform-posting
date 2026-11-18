# Automated Multi-Platform Posting System

This project accepts one short message and attempts to publish it to five services. Each platform has a separate connector and returns its own result. A problem with one account should not cancel the other posting attempts.

## Platforms

| Platform | API operation | Credentials / permission |
|---|---|---|
| LinkedIn | Create a public post with `POST /rest/posts` | Access token with posting access, author URN and a supported API version |
| Mastodon | Create a public status with `POST /api/v1/statuses` | Instance URL and user token with `write:statuses` |
| Bluesky | Create an `app.bsky.feed.post` record | Handle and app password |
| WordPress | Create a published post with `POST /wp-json/wp/v2/posts` | HTTPS site URL, username and Application Password |
| Telegram | Send a message with Bot API `sendMessage` | Bot token and destination chat/channel ID; bot must be allowed to post |

The application attempts all five connectors internally. The caller cannot choose a subset. A missing credential or a provider rejection is returned as a failure for that platform while the other connectors continue.

## Technology

- Python 3.10+
- FastAPI, Uvicorn and Pydantic
- HTTPX for asynchronous REST requests
- Pytest for validation and connector tests

## Setup

From this project directory:

```powershell
py -m venv .venv
.venv\\Scripts\\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
```

On macOS or Linux, activate the environment with `source .venv/bin/activate` and copy the example file with `cp .env.example .env`.

Add credentials for accounts you own or are authorised to publish to in `.env`. The example file lists the required variables. Do not commit `.env`. For a first run, leaving credentials blank is safe: each connector reports a missing-credential failure and no message is sent.

Start the server:

```bash
uvicorn app.main:app --host 0.0.0.0 --port 4000
```

Open `http://localhost:4000/docs` to try the endpoint.

## Request

```http
POST http://localhost:4000/posting
Content-Type: application/json
```

```json
{
  "message": "Read the latest update and share your feedback: https://example.com"
}
```

The message must be 200 characters or fewer and contain exactly one valid HTTP or HTTPS CTA link. Bare `www.` links, FTP links, local addresses and embedded URL credentials are rejected. The application validates the input before any connector runs.

## Response behavior

The response contains an overall `success` flag and one result for each platform. Each result includes the platform name, `success` or `failed` status, a post URL when the provider returns one, a public-access flag, a UTC date/time and an error message when appropriate.

See [`examples/sample_response_missing_credentials.json`](examples/sample_response_missing_credentials.json) for the actual response returned in a local run with no provider credentials configured. An overall `success: true` means at least one provider accepted the post; it does not mean all five succeeded. A provider success means its API accepted the publish request. Telegram destinations without a public username may not have a public permalink, so `posted_url` can be `null` and `public_access` can be `false` even when the message was delivered. The timestamp is recorded by this application immediately after the provider accepts the request, not copied from a provider-side publication timestamp.

## Credentials and account access

- **LinkedIn:** the app must have the relevant posting product/permission. Member and organization author URNs have different access requirements. Set `LINKEDIN_API_VERSION` to a version currently supported for your app; LinkedIn retires versions over time.
- **Mastodon:** create a user token on the chosen instance with `write:statuses`. The connector sets visibility to `public`.
- **Bluesky:** use an app password, not your normal account password. The connector uses the Bluesky-hosted `bsky.social` XRPC service.
- **WordPress:** create a revocable Application Password for a user who can publish posts. The connector requires HTTPS because Basic Authentication credentials must not be sent over plain HTTP. Posts are published immediately with the title `Update`; test with a staging site first.
- **Telegram:** add the bot to the destination group or channel and grant it permission to send messages. Public channel permalinks are returned when Telegram provides a public username.

## Official API references

- LinkedIn Posts API: https://learn.microsoft.com/en-us/linkedin/marketing/community-management/shares/posts-api
- Mastodon statuses API: https://docs.joinmastodon.org/methods/statuses/
- Bluesky API: https://bsky.network/docs/bluesky-api/
- WordPress REST API posts: https://developer.wordpress.org/rest-api/reference/posts/
- WordPress Application Passwords: https://developer.wordpress.org/advanced-administration/security/application-passwords/
- Telegram Bot API `sendMessage`: https://core.telegram.org/bots/api#sendmessage

## Tests

```bash
python -m pytest -q
```

The automated tests cover message length, missing/multiple/malformed links, non-public IP URLs, HTTPS requirements for credential-bearing services, connector request shapes and failure isolation. Connector tests use mocked HTTP responses; they do not publish to real accounts. A live test requires valid credentials and should be performed only with accounts and destinations you control.

## Important limitations

- LinkedIn posting access is restricted; having a developer app does not automatically grant permission to publish.
- WordPress creates a blog post rather than a short-form social update. The site owner should test with a staging site before using a production account.
- Telegram messages in private chats are not publicly accessible. A permalink is only returned when the destination is a public channel with a username.
- Provider rate limits, permission requirements and API versions can change. Review the official documentation before configuring live credentials.

## Project layout

```text
app/
  main.py
  config.py
  schemas.py
  platforms/
    common.py
    linkedin.py
    mastodon.py
    bluesky.py
    wordpress.py
    telegram.py
  services/
    posting_service.py
tests/
  test_api.py
  test_validation.py
  test_posting_service.py
  test_platform_connectors.py
examples/
  sample_response_missing_credentials.json
.github/workflows/tests.yml
.env.example
requirements.txt
README.md
```

## Deployment note

The service runs locally on port 4000. The connectors are implemented against the providers' HTTP APIs, but this repository's automated tests mock those API responses. Actual publishing requires valid credentials and posting permissions for accounts you control. No live post has been made as part of the test run. Before deployment, configure the credentials in the hosting provider's secret/environment settings, use test destinations you own, and verify each connector separately. Do not commit a `.env` file or application passwords.
