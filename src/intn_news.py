"""일간NTN(intn.co.kr) — 유권해석·조세행정·오피니언 당일 기사 수집."""

from __future__ import annotations

import re
import time
from datetime import date, datetime
from urllib.parse import urljoin
from zoneinfo import ZoneInfo

import requests
from bs4 import BeautifulSoup

BASE_URL = "https://www.intn.co.kr"
KST = ZoneInfo("Asia/Seoul")
DATE_RE = re.compile(r"(\d{4})-(\d{2})-(\d{2})")
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "ko-KR,ko;q=0.9",
}

DEFAULT_FEEDS: list[dict[str, str]] = [
    {
        "section": "유권해석",
        "list_url": f"{BASE_URL}/news/articleList.html?sc_section_code=S1N5&view_type=sm",
    },
    {
        "section": "조세행정",
        "list_url": f"{BASE_URL}/news/articleList.html?sc_section_code=S1N6&view_type=sm",
    },
    {
        "section": "오피니언",
        "list_url": f"{BASE_URL}/news/articleList.html?sc_section_code=S1N8&view_type=sm",
    },
]


def _today_kst() -> date:
    return datetime.now(KST).date()


def _parse_display_date(raw: str) -> date | None:
    match = DATE_RE.search(raw or "")
    if not match:
        return None
    return date(int(match.group(1)), int(match.group(2)), int(match.group(3)))


def _split_meta(raw: str) -> tuple[str, str]:
    parts = [part.strip() for part in (raw or "").split("|") if part.strip()]
    if not parts:
        return "", ""
    if len(parts) == 1:
        return "", parts[0]
    return parts[-2], parts[-1]


def _page_url(list_url: str, page: int) -> str:
    if page <= 1:
        return list_url
    joiner = "&" if "?" in list_url else "?"
    return f"{list_url}{joiner}page={page}"


def _fetch_page(url: str) -> str:
    response = requests.get(url, headers=HEADERS, timeout=20)
    response.raise_for_status()
    response.encoding = "utf-8"
    return response.text


def parse_articles(html: str, *, section: str) -> list[dict]:
    """목록 HTML에서 기사를 파싱합니다."""
    soup = BeautifulSoup(html, "html.parser")
    articles: list[dict] = []

    for row in soup.select("section.article-list-content .list-block"):
        title_link = row.select_one(".list-titles a")
        if not title_link:
            continue

        summary_el = row.select_one(".list-summary a")
        date_el = row.select_one(".list-dated")
        meta_raw = date_el.get_text(strip=True) if date_el else ""
        author, display_time = _split_meta(meta_raw)

        articles.append(
            {
                "source": "intn",
                "section": section,
                "title": title_link.get_text(strip=True),
                "link": urljoin(BASE_URL, title_link["href"]),
                "published": display_time or meta_raw,
                "parsed_date": _parse_display_date(display_time or meta_raw),
                "author": author,
                "summary": summary_el.get_text(strip=True) if summary_el else "",
            }
        )

    return articles


def fetch_today_for_feed(
    feed: dict[str, str],
    *,
    max_pages: int = 30,
    seen_links: set[str] | None = None,
) -> list[dict]:
    """피드 하나에서 오늘(KST) 기사를 수집합니다."""
    target = _today_kst()
    section = feed["section"]
    list_url = feed["list_url"]
    seen = seen_links if seen_links is not None else set()
    results: list[dict] = []

    miss_streak = 0
    for page in range(1, max_pages + 1):
        items = parse_articles(_fetch_page(_page_url(list_url, page)), section=section)
        if not items:
            break

        found_today = False
        for item in items:
            parsed = item.get("parsed_date")
            if parsed == target:
                found_today = True
                link = item["link"]
                if link not in seen:
                    seen.add(link)
                    results.append(item)

        if found_today:
            miss_streak = 0
        else:
            miss_streak += 1
            if miss_streak >= 2:
                break
        if page < max_pages:
            time.sleep(0.5)

    return results


def fetch_today_by_section(
    feeds: list[dict[str, str]] | None = None,
    *,
    max_pages: int = 30,
) -> dict[str, list[dict]]:
    """유권해석·조세행정·오피니언 당일 기사를 섹션별로 반환합니다."""
    feed_list = feeds or DEFAULT_FEEDS
    seen_links: set[str] = set()
    by_section: dict[str, list[dict]] = {}

    for feed in feed_list:
        section = feed["section"]
        by_section[section] = fetch_today_for_feed(
            feed,
            max_pages=max_pages,
            seen_links=seen_links,
        )

    return by_section
