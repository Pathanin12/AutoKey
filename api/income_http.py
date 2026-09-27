from __future__ import annotations

import json
import ssl
import urllib.error
import urllib.parse
import urllib.request
from http.cookiejar import Cookie, CookieJar
from typing import Any

from constants.routes import EKO_HTTP_URL

_UA = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36"
)


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def ssl_context(url: str) -> ssl.SSLContext:
    if url.startswith(EKO_HTTP_URL):
        return ssl._create_unverified_context()
    return ssl.create_default_context()


def request(
    cookies: CookieJar,
    method: str,
    url: str,
    *,
    payload: Any | None = None,
    origin: str,
    follow: bool = True,
) -> tuple[int, dict[str, str], bytes, str | None]:
    data = None if payload is None else json.dumps(payload).encode()
    req = urllib.request.Request(url, data=data, method=method)
    if payload is not None:
        req.add_header("Content-Type", "application/json")
    req.add_header("Accept", "application/json,application/pdf,*/*")
    req.add_header("User-Agent", _UA)
    req.add_header("Origin", origin)
    req.add_header("Referer", origin.rstrip("/") + "/")
    handlers: list[urllib.request.BaseHandler] = [
        urllib.request.HTTPSHandler(context=ssl_context(url)),
        urllib.request.HTTPCookieProcessor(cookies),
    ]
    if not follow:
        handlers.insert(0, NoRedirect())
    try:
        with urllib.request.build_opener(*handlers).open(req, timeout=60) as resp:
            return resp.status, dict(resp.headers), resp.read(), resp.geturl()
    except urllib.error.HTTPError as exc:
        return exc.code, dict(exc.headers), exc.read(), exc.headers.get("Location")


def copy_cookie(cookies: CookieJar, name: str, domains: tuple[str, ...]) -> None:
    source = next((item for item in cookies if item.name == name), None)
    if source is None:
        return
    for domain in domains:
        cookies.set_cookie(
            Cookie(
                0,
                source.name,
                source.value,
                None,
                False,
                domain,
                True,
                domain.startswith("."),
                "/",
                True,
                True,
                None,
                True,
                None,
                None,
                {},
            )
        )


def query(url: str, params: dict[str, str]) -> str:
    return url + "?" + urllib.parse.urlencode(params)


def join(url: str, location: str) -> str:
    return urllib.parse.urljoin(url, location)
