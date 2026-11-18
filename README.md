# Automated Multi-Platform Posting API

A FastAPI service that validates a short message and independently attempts to publish it through five third-party APIs: LinkedIn, Mastodon, Bluesky, WordPress and Telegram.

## Run locally

```bash
python -m venv .venv
# Windows PowerShell: .venv\\Scripts\\Activate.ps1
# macOS/Linux: source .venv/bin/activate
python -m pip install -r requirements.txt
cp .env.example .env
# Add credentials only for accounts and destinations you own or are authorized to use.
uvicorn app.main:app --host 0.0.0.0 --port 4000
```

Open `http://localhost:4000/docs`.

## Request

`POST /posting`

```json
{"message":"Read the latest update and share your feedback: https://example.com"}
```

The message is limited to 200 characters and must contain exactly one valid public HTTP or HTTPS URL. Platform selection is handled internally.

## Results

Each platform returns its own status, posted URL when available, public-access flag, date/time and error detail. A provider success means that provider accepted the publish request; it does not imply all platforms succeeded. A private Telegram destination may not have a public permalink.

## Verification and limitations

- 28 automated tests passed locally.
- Python syntax compilation and local FastAPI smoke checks passed.
- Automated provider tests use mocked HTTP responses; no real social post was made during the test run.
- Real publishing requires authorized credentials and the relevant app/product permissions. LinkedIn access is restricted; other providers also require configured accounts and destinations.
- Test against accounts and staging destinations you control before using production channels.

See `TEST_RESULTS.md` and `OFFICIAL_API_REFERENCES.md`. Never commit `.env`, bot tokens or application passwords.