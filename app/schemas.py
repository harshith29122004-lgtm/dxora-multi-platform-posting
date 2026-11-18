import ipaddress
import re
from typing import Literal
from urllib.parse import urlparse

from pydantic import BaseModel, Field, field_validator

# Keep common trailing sentence punctuation out of the URL match.
URL_PATTERN = re.compile(r"https?://[^\s<>\"']+", re.IGNORECASE)
OTHER_LINK_PATTERN = re.compile(r"(?<!://)(?<![\w.-])(?:ftp://|www\.)[^\s<>\"\']+", re.IGNORECASE)
TRAILING_PUNCTUATION = ".,!?;:)]}"


def _clean_url(match: str) -> str:
    return match.rstrip(TRAILING_PUNCTUATION)


def validate_cta_link(message: str) -> str:
    links = [_clean_url(item) for item in URL_PATTERN.findall(message)]
    other_links = OTHER_LINK_PATTERN.findall(message)
    if len(links) != 1 or other_links:
        raise ValueError("Include exactly one HTTP or HTTPS CTA link in the message.")

    candidate = links[0]
    parsed = urlparse(candidate)
    if parsed.scheme.lower() not in {"http", "https"} or not parsed.hostname:
        raise ValueError("The CTA link must be a valid HTTP or HTTPS URL.")
    if parsed.username or parsed.password:
        raise ValueError("The CTA link must not contain embedded login credentials.")
    try:
        if parsed.port is not None and not 1 <= parsed.port <= 65535:
            raise ValueError("The CTA link contains an invalid port.")
    except ValueError:
        raise ValueError("The CTA link contains an invalid port.")

    host = parsed.hostname.rstrip(".").lower()
    if host == "localhost" or host.endswith((".localhost", ".local", ".internal")):
        raise ValueError("Use a public website URL for the CTA link.")

    try:
        address = ipaddress.ip_address(host)
    except ValueError:
        # A public DNS name needs at least two labels. Validate the IDNA form
        # so malformed labels such as underscores or leading hyphens fail early.
        try:
            ascii_host = host.encode("idna").decode("ascii")
        except UnicodeError as exc:
            raise ValueError("The CTA link must contain a valid public hostname.") from exc
        labels = ascii_host.split(".")
        valid_label = re.compile(r"^(?!-)[a-z0-9-]{1,63}(?<!-)$", re.IGNORECASE)
        if len(ascii_host) > 253 or len(labels) < 2 or any(not valid_label.fullmatch(label) for label in labels):
            raise ValueError("The CTA link must contain a valid public hostname.")
    else:
        if not address.is_global:
            raise ValueError("Use a public website URL for the CTA link.")
    return candidate


class PostingRequest(BaseModel):
    message: str = Field(min_length=1, max_length=200)

    @field_validator("message")
    @classmethod
    def validate_message(cls, value: str) -> str:
        if value != value.strip():
            value = value.strip()
        if not value:
            raise ValueError("Message cannot be empty.")
        validate_cta_link(value)
        return value


class PlatformResult(BaseModel):
    platform: str
    status: Literal["success", "failed"]
    posted_url: str | None = None
    public_access: bool = False
    date: str | None = None
    time: str | None = None
    error: str | None = None


class PostingResponse(BaseModel):
    success: bool
    results: list[PlatformResult]
