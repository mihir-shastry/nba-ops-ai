"""
NBA API Compatibility Layer
Patches nba_api to use curl_cffi instead of requests, bypassing
Akamai Bot Manager TLS fingerprinting on stats.nba.com.

Import this module before any nba_api usage:

    import nba_api_compat  # noqa: F401 — patches nba_api internally
    from nba_api.stats.endpoints import leagueleaders  # now works reliably
"""

from curl_cffi import requests as cffi_requests


class CurlCffiSession:
    """
    Drop-in replacement for requests.Session that uses curl_cffi
    to impersonate Chrome's TLS fingerprint.
    """

    def __init__(self):
        self._session = cffi_requests.Session(impersonate="chrome")
        self.cookies = self._session.cookies

    def get(self, url, params=None, headers=None, proxies=None, timeout=None, **kwargs):
        # Merge params into URL manually (curl_cffi handles them differently)
        resp = self._session.get(
            url,
            params=params,
            headers=headers or {},
            timeout=timeout or 30,
        )
        # Return an object that looks like a requests.Response
        return _FakeResponse(resp)


class _FakeResponse:
    """Wraps curl_cffi response to match requests.Response interface."""

    def __init__(self, resp):
        self._resp = resp
        self.url = str(resp.url)
        self.status_code = resp.status_code
        self.text = resp.text

    @property
    def content(self):
        return self._resp.content

    def json(self):
        return self._resp.json()


def patch_nba_api():
    """Monkey-patch nba_api's NBAHTTP to use curl_cffi sessions."""
    try:
        from nba_api.library import http as nba_http

        _original_get_session = nba_http.NBAHTTP.get_session

        @classmethod
        def patched_get_session(cls):
            session = cls._session
            if session is None or not isinstance(session, CurlCffiSession):
                session = CurlCffiSession()
                cls._session = session
            return session

        nba_http.NBAHTTP.get_session = patched_get_session
        print("nba_api patched: using curl_cffi for TLS bypass")
    except ImportError:
        print("WARNING: nba_api not found, skipping patch")


# Auto-patch on import
patch_nba_api()
