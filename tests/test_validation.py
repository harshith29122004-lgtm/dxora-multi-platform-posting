import pytest
from pydantic import ValidationError
from app.schemas import PostingRequest, validate_cta_link


def test_accepts_one_valid_link():
    request = PostingRequest(message="Read the details here: https://example.com/page")
    assert request.message.endswith("https://example.com/page")


def test_rejects_missing_link():
    with pytest.raises(ValidationError):
        PostingRequest(message="There is no link in this message")


def test_rejects_two_links():
    with pytest.raises(ValidationError):
        PostingRequest(message="Visit https://one.example and https://two.example")


def test_rejects_private_ip_link():
    with pytest.raises(ValidationError):
        PostingRequest(message="Visit https://127.0.0.1/admin")


def test_rejects_non_http_link():
    with pytest.raises(ValidationError):
        PostingRequest(message="Download ftp://example.com/file")


def test_rejects_message_over_200_characters():
    with pytest.raises(ValidationError):
        PostingRequest(message="A" * 181 + " https://example.com")


def test_rejects_malformed_link():
    with pytest.raises(ValidationError):
        PostingRequest(message="Visit https://")


def test_accepts_www_hostname_with_https_prefix():
    from app.schemas import PostingRequest

    request = PostingRequest(message="Visit our website: https://www.example.com/services")
    assert request.message.endswith("https://www.example.com/services")


def test_rejects_bare_www_link_without_scheme():
    from pydantic import ValidationError
    from app.schemas import PostingRequest

    with pytest.raises(ValidationError):
        PostingRequest(message="Visit www.example.com today")


def test_rejects_ftp_link_even_when_http_link_is_present():
    from pydantic import ValidationError
    from app.schemas import PostingRequest

    with pytest.raises(ValidationError):
        PostingRequest(message="Visit https://example.com and ftp://files.example.com")


def test_rejects_malformed_domain_label():
    with pytest.raises(ValidationError):
        PostingRequest(message="Visit https://-bad.example today")


def test_rejects_single_label_hostname():
    with pytest.raises(ValidationError):
        PostingRequest(message="Visit https://intranet today")


def test_accepts_url_followed_by_sentence_punctuation():
    request = PostingRequest(message="Read more at https://example.com/page.")
    assert request.message.endswith("https://example.com/page.")
    assert validate_cta_link(request.message) == "https://example.com/page"


def test_rejects_port_zero():
    with pytest.raises(ValidationError):
        PostingRequest(message="Visit https://example.com:0/page")
