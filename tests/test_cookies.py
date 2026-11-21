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


def test_browser_cookie_jar_carries_full_google_session(monkeypatch):
    """Since Google's 2026-11-12 web build, PSID + PSIDTS alone get every
    batchexecute / StreamGenerate request rejected with HTTP 400. The client
    needs the browser's whole google.com session (SID, HSID, OSID, ...), kept
    domain-tagged and without foreign ccTLD cookies."""
    import browser_cookie3

    jar = CookieJar()
    jar.set_cookie(_cookie("__Secure-1PSID", "good-psid", ".google.com"))
    jar.set_cookie(_cookie("__Secure-1PSIDTS", "good-ts", ".google.com"))
    jar.set_cookie(_cookie("SID", "good-sid", ".google.com"))
    jar.set_cookie(_cookie("OSID", "good-osid", "gemini.google.com"))
    jar.set_cookie(_cookie("SID", "bd-sid", ".google.com.bd"))
    jar.set_cookie(_cookie("NID", "ads-nid", "ads.google.com"))
    monkeypatch.setattr(browser_cookie3, "chrome", lambda **kw: jar)
    monkeypatch.delenv("GEMINI_PSID", raising=False)

    cookies = S._browser_cookie_jar()

    assert cookies is not None
    assert cookies.get("__Secure-1PSID", domain=".google.com") == "good-psid"
    assert cookies.get("SID", domain=".google.com") == "good-sid"
    assert cookies.get("OSID", domain="gemini.google.com") == "good-osid"
    values = {c.value for c in cookies.jar}
    assert "bd-sid" not in values
    assert "ads-nid" not in values
    assert all(c.domain in S._GEMINI_COOKIE_DOMAINS for c in cookies.jar)


def test_browser_cookie_jar_skipped_when_env_override_set(monkeypatch):
    monkeypatch.setenv("GEMINI_PSID", "env-psid")
    assert S._browser_cookie_jar() is None


def test_gg_dl_links_get_alr_param():
    """Since 2026-11-12, lh3 gg-dl links answer 403 unless ?alr=yes follows
    the size suffix (the web app fetches `...=s1024-rw?alr=yes`)."""
    base = "https://lh3.googleusercontent.com/gg-dl/AbC123"
    assert S._with_alr(base + "=s0") == base + "=s0?alr=yes"
    assert S._with_alr(base + "=s0?authuser=1") == base + "=s0?authuser=1&alr=yes"
    assert S._with_alr(base + "=s0?alr=yes") == base + "=s0?alr=yes"
    other = "https://lh3.googleusercontent.com/rd-gg/XyZ=s0"
    assert S._with_alr(other) == other


def test_image_download_cookies_keep_domains():
    """GeneratedImage's pydantic field coerces the client's jar to a plain dict,
    losing domains; the work.fife.usercontent.google.com hop then hands out a
    final lh3 link that answers 403. Downloads must get the domain-tagged jar."""
    from types import SimpleNamespace

    from curl_cffi.requests import Cookies

    jar = Cookies()
    jar.set("SID", "x", domain=".google.com")
    jar.set("OSID", "y", domain="gemini.google.com")

    got = S._image_download_cookies(SimpleNamespace(cookies=jar))

    assert {c.domain for c in got.jar} == {".google.com", "gemini.google.com"}
    assert S._image_download_cookies(SimpleNamespace(cookies={"SID": "x"})) is None
