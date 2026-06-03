"""삼일PwC 정기채용 페이지 — 모집 오픈 여부 확인."""

from __future__ import annotations

import hashlib
import json
import re
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

DEFAULT_WATCH_URL = "https://pwc.to/2xLHIx4"
DEFAULT_PAGE_URL = "https://www.pwc.com/kr/ko/career/graduate-opportunities.html"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "ko-KR,ko;q=0.9",
}

APPLY_CTA_RE = re.compile(
    r"^(지원하기|지원\s*바로가기|입사\s*지원|지원서\s*작성|지원\s*하기|Apply\s*now|Apply)$",
    re.IGNORECASE,
)
OPEN_PHRASES = (
    "모집 중",
    "모집중",
    "접수 중",
    "접수중",
    "지원 가능",
    "지원 받",
    "채용 진행",
    "모집 시작",
    "모집이 시작",
)
EXTERNAL_JOB_HOSTS = (
    "workday",
    "myworkdayjobs",
    "taleo",
    "greenhouse",
    "lever.co",
    "icims",
    "successfactors",
    "recruiting",
    "job",
)
NAV_SKIP_IN_TEXT = ("지원센터", "FAQ", "M&A 지원", "밸류업", "남북투자")


def _is_nav_noise(link_text: str) -> bool:
    return any(skip in link_text for skip in NAV_SKIP_IN_TEXT)


def _is_external_apply_href(href: str, page_url: str) -> bool:
    if not href or href.startswith("#") or href.startswith("javascript:"):
        return False
    full = urljoin(page_url, href)
    host = urlparse(full).netloc.lower()
    path = urlparse(full).path.lower()
    if any(h in host for h in EXTERNAL_JOB_HOSTS):
        return True
    if "apply" in path or "job" in path or "recruitment" in path:
        return "pwc.com" not in host
    return False


def _extract_graduate_block(soup: BeautifulSoup) -> tuple[str, list[tuple[str, str]]]:
    h1 = None
    for tag in soup.find_all("h1"):
        if "정기" in tag.get_text(strip=True):
            h1 = tag
            break
    if not h1:
        return "", []

    lines: list[str] = []
    links: list[tuple[str, str]] = []

    for el in h1.find_all_next():
        if el.name == "h2" and "수시" in el.get_text(strip=True):
            break
        if el.name == "a" and el.get("href"):
            text = el.get_text(strip=True)
            href = el["href"].strip()
            if text and not _is_nav_noise(text):
                links.append((text, href))
        if el.name in ("p", "h2", "h3"):
            text = el.get_text(" ", strip=True)
            if text and len(text) < 500:
                lines.append(text)

    return "\n".join(lines), links


def _scan_json_for_apply_urls(obj: object, found: list[str]) -> None:
    if isinstance(obj, dict):
        for value in obj.values():
            _scan_json_for_apply_urls(value, found)
    elif isinstance(obj, list):
        for item in obj:
            _scan_json_for_apply_urls(item, found)
    elif isinstance(obj, str):
        for match in re.finditer(r"https?://[^\s\"'<>]+", obj):
            url = match.group(0)
            if _is_external_apply_href(url, DEFAULT_PAGE_URL):
                found.append(url)


def _fetch_model_json(page_url: str) -> dict | None:
    if ".html" in page_url:
        model_url = page_url.replace(".html", ".model.json")
    else:
        model_url = page_url.rstrip("/") + ".model.json"
    try:
        response = requests.get(model_url, headers=HEADERS, timeout=20)
        response.raise_for_status()
        return response.json()
    except (requests.RequestException, json.JSONDecodeError):
        return None


def check_graduate_recruitment(watch_url: str = DEFAULT_WATCH_URL) -> dict:
    """
    정기채용 모집 오픈 여부를 판별합니다.

    반환: is_open, title, link, summary, fingerprint, page_url
    """
    try:
        response = requests.get(watch_url, headers=HEADERS, timeout=25, allow_redirects=True)
        response.raise_for_status()
    except requests.RequestException as exc:
        return {
            "is_open": False,
            "title": "삼일PwC 정기채용",
            "link": watch_url,
            "summary": f"페이지 확인 실패: {exc}",
            "fingerprint": "",
            "page_url": watch_url,
            "error": str(exc),
        }

    page_url = response.url
    soup = BeautifulSoup(response.text, "html.parser")
    block, links = _extract_graduate_block(soup)

    signals: list[tuple[str, str, str]] = []

    for text, href in links:
        full = urljoin(page_url, href)
        if APPLY_CTA_RE.match(text) and not _is_nav_noise(text):
            signals.append(("cta", text, full))
        elif _is_external_apply_href(href, page_url):
            label = text or "삼일PwC 정기채용 지원"
            signals.append(("external", label, full))

    for phrase in OPEN_PHRASES:
        if phrase in block:
            signals.append(("phrase", f"삼일PwC 정기채용 ({phrase})", page_url))
            break

    json_urls: list[str] = []
    model = _fetch_model_json(page_url)
    if model:
        _scan_json_for_apply_urls(model, json_urls)
    for url in json_urls:
        signals.append(("json", "삼일PwC 정기채용 지원", url))

    is_open = len(signals) > 0

    if is_open:
        _, title, link = signals[0]
        summary = title
    else:
        title = "삼일PwC 정기채용 (모집 대기 중)"
        link = watch_url
        summary = "아직 지원 링크·모집 중 문구가 없습니다."

    fingerprint = hashlib.sha256(
        (block + "|" + "|".join(f"{a}:{b}" for a, b in links)).encode("utf-8")
    ).hexdigest()[:16]

    return {
        "is_open": is_open,
        "title": title if is_open else "삼일PwC 정기채용 모집 시작",
        "link": link,
        "summary": summary,
        "fingerprint": fingerprint,
        "page_url": page_url,
    }
