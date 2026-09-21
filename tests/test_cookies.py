"""_resolve_cookies must take __Secure-1PSID from the exact `.google.com` domain.

browser_cookie3 matches `domain_name` as a substring, so a jar holding cookies
for `.google.com.bd` (or any other ccTLD) also comes back — and a "last wins"
loop would hand Gemini a foreign-domain session (regression: 2026-09-21, every
request answered 1096 / "Are you signed in?").
"""
import os
import sys
from http.cookiejar import Cookie, CookieJar

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from gemini_webapi_mcp import server as S  # noqa: E402


def _cookie(name, value, domain):
    return Cookie(0, name, value, None, False, domain, True, domain.startswith("."),
                  "/", True, True, None, False, None, None, {})


def test_resolve_cookies_prefers_exact_google_com_domain(monkeypatch):
    import browser_cookie3

    jar = CookieJar()
    jar.set_cookie(_cookie("__Secure-1PSID", "good-psid", ".google.com"))
    jar.set_cookie(_cookie("__Secure-1PSIDTS", "good-ts", ".google.com"))
    jar.set_cookie(_cookie("__Secure-1PSID", "bd-psid", ".google.com.bd"))
    jar.set_cookie(_cookie("__Secure-1PSIDTS", "bd-ts", ".google.com.bd"))
    monkeypatch.setattr(browser_cookie3, "chrome", lambda **kw: jar)
    monkeypatch.delenv("GEMINI_PSID", raising=False)

    assert S._resolve_cookies() == ("good-psid", "good-ts")
