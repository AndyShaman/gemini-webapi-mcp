"""Unit tests for the image-generation fallbacks added by this PR.

Covers the offline behaviour of ``_pollinations_generate_image`` (URL build,
Chrome impersonation, error handling) without needing network access, an API
key, or browser cookies — so it runs in CI as-is.
"""
import asyncio
import os
import sys
import urllib.parse

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from gemini_webapi_mcp import server as S


class _FakeResp:
    def __init__(self, status_code=200, content=b"\x89PNG" + b"x" * 4000):
        self.status_code = status_code
        self.content = content


class _FakeSession:
    """Stand-in for curl_cffi.requests.AsyncSession used as an async ctx mgr."""

    last_url = None
    last_impersonate = None
    resp = _FakeResp()

    def __init__(self, *args, **kwargs):
        _FakeSession.last_impersonate = kwargs.get("impersonate")

    async def __aenter__(self):
        return self

    async def __aexit__(self, *exc):
        return False

    async def get(self, url, **kwargs):
        _FakeSession.last_url = url
        return _FakeSession.resp


def _run(coro):
    return asyncio.new_event_loop().run_until_complete(coro)


@pytest.fixture(autouse=True)
def _patch_curl(monkeypatch, tmp_path):
    import curl_cffi.requests as cffi

    monkeypatch.setattr(cffi, "AsyncSession", _FakeSession)
    monkeypatch.setattr(S, "IMAGES_DIR", tmp_path)
    _FakeSession.resp = _FakeResp()
    yield


def test_pollinations_returns_saved_path():
    paths = _run(S._pollinations_generate_image("a red circle"))
    assert len(paths) == 1
    assert os.path.exists(paths[0])
    assert os.path.getsize(paths[0]) > 1000


def test_pollinations_url_is_encoded_and_impersonates_chrome():
    _run(S._pollinations_generate_image("cat & dog/at noon"))
    assert _FakeSession.last_url.startswith("https://image.pollinations.ai/prompt/")
    assert urllib.parse.quote("cat & dog/at noon") in _FakeSession.last_url
    assert _FakeSession.last_impersonate == "chrome110"


def test_pollinations_raises_on_http_error():
    _FakeSession.resp = _FakeResp(status_code=403)
    with pytest.raises(RuntimeError):
        _run(S._pollinations_generate_image("anything"))


def test_pollinations_raises_on_tiny_response():
    _FakeSession.resp = _FakeResp(content=b"err")
    with pytest.raises(RuntimeError):
        _run(S._pollinations_generate_image("anything"))
