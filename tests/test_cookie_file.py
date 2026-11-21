"""GEMINI_COOKIES_FILE: load the full Gemini session from a cookie file the user exported.

On Windows, Chrome's cookie store can't be read by browser-cookie3 (app-bound
encryption), and since Google's 2026-11-12 web build the two PSID cookies alone get
every request answered with HTTP 400. The user exports google.com cookies from their
browser (Netscape cookies.txt or a JSON array) and points GEMINI_COOKIES_FILE at it.
"""
import json
import time

import pytest

from gemini_webapi_mcp import server

FUTURE = int(time.time()) + 86400
PAST = int(time.time()) - 86400


def _netscape(lines):
    return "# Netscape HTTP Cookie File\n\n" + "\n".join("\t".join(map(str, l)) for l in lines) + "\n"


def _write(tmp_path, name, text):
    p = tmp_path / name
    p.write_text(text, encoding="utf-8")
    return p


def test_netscape_file_keeps_google_cookies_with_their_domains(tmp_path):
    p = _write(tmp_path, "c.txt", _netscape([
        (".google.com", "TRUE", "/", "TRUE", FUTURE, "__Secure-1PSID", "psid-value"),
        ("#HttpOnly_.google.com", "TRUE", "/", "TRUE", FUTURE, "__Secure-1PSIDTS", "ts-value"),
        (".google.com", "TRUE", "/", "FALSE", FUTURE, "SID", "sid-value"),
        ("gemini.google.com", "FALSE", "/", "TRUE", FUTURE, "_ga", "ga-value"),
        (".google.co.uk", "TRUE", "/", "TRUE", FUTURE, "SID", "foreign"),
        (".youtube.com", "TRUE", "/", "TRUE", FUTURE, "VISITOR", "yt"),
    ]))
    jar = server._file_cookie_jar(str(p))
    assert jar is not None
    assert jar.get("__Secure-1PSID", domain=".google.com") == "psid-value"
    assert jar.get("__Secure-1PSIDTS", domain=".google.com") == "ts-value"   # #HttpOnly_ prefix stripped
    assert jar.get("SID", domain=".google.com") == "sid-value"
    assert jar.get("_ga", domain="gemini.google.com") == "ga-value"
    domains = {c.domain for c in jar.jar}
    assert ".google.co.uk" not in domains and ".youtube.com" not in domains


def test_space_separated_netscape_is_read(tmp_path):
    # A file whose columns are space-delimited instead of tab-delimited.
    p = _write(tmp_path, "c.txt", "# Netscape HTTP Cookie File\n\n" + "\n".join(
        " ".join(map(str, l)) for l in [
            (".google.com", "TRUE", "/", "TRUE", FUTURE, "__Secure-1PSID", "psid-value"),
            ("#HttpOnly_.google.com", "TRUE", "/", "TRUE", FUTURE, "SID", "sid-value"),
        ]) + "\n")
    jar = server._file_cookie_jar(str(p))
    assert jar.get("__Secure-1PSID", domain=".google.com") == "psid-value"
    assert jar.get("SID", domain=".google.com") == "sid-value"


def test_expired_cookies_are_skipped(tmp_path):
    p = _write(tmp_path, "c.txt", _netscape([
        (".google.com", "TRUE", "/", "TRUE", FUTURE, "__Secure-1PSID", "psid-value"),
        (".google.com", "TRUE", "/", "TRUE", PAST, "OLD", "stale"),
        (".google.com", "TRUE", "/", "TRUE", 0, "SESSIONONLY", "kept"),  # 0 = session cookie
    ]))
    jar = server._file_cookie_jar(str(p))
    names = {c.name for c in jar.jar}
    assert "OLD" not in names and "SESSIONONLY" in names


def test_json_export_is_read_too(tmp_path):
    p = _write(tmp_path, "c.json", json.dumps([
        {"domain": ".google.com", "name": "__Secure-1PSID", "value": "psid-value", "path": "/",
         "expirationDate": FUTURE},
        {"domain": ".google.com", "name": "HSID", "value": "hsid", "path": "/"},
        {"domain": "accounts.google.com", "name": "LSID", "value": "x", "path": "/"},
    ]))
    jar = server._file_cookie_jar(str(p))
    assert jar.get("__Secure-1PSID", domain=".google.com") == "psid-value"
    assert jar.get("HSID", domain=".google.com") == "hsid"
    assert "accounts.google.com" not in {c.domain for c in jar.jar}


def test_file_without_the_session_cookie_gives_a_clear_error(tmp_path):
    p = _write(tmp_path, "c.txt", _netscape([
        (".google.com", "TRUE", "/", "FALSE", FUTURE, "NID", "n"),
    ]))
    with pytest.raises(RuntimeError, match="__Secure-1PSID"):
        server._file_cookie_jar(str(p))


def test_missing_file_gives_a_clear_error(tmp_path):
    with pytest.raises(RuntimeError, match="not found"):
        server._file_cookie_jar(str(tmp_path / "nope.txt"))


def test_error_messages_never_contain_cookie_values(tmp_path):
    p = _write(tmp_path, "c.txt", "this is not a cookie file secret-value-123\n")
    with pytest.raises(RuntimeError) as err:
        server._file_cookie_jar(str(p))
    assert "secret-value-123" not in str(err.value)
