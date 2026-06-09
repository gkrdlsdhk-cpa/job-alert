"""네이버 뉴스 검색 API로 기업 관련 기사를 가져옵니다."""

from __future__ import annotations

import os
import re
from datetime import date, datetime
from html import unescape
from zoneinfo import ZoneInfo

import requests

NAVER_NEWS_URL = "https://openapi.naver.com/v1/search/news.json"
KST = ZoneInfo("Asia/Seoul")
TITLE_PREFIX_RE = re.compile(r"^\s*(?:\[[^\]]+\]|【[^】]+】|<[^>]+>)\s*")
TITLE_WORD_RE = re.compile(r"[가-힣A-Za-z0-9]+")
TITLE_STOPWORDS = {
    "집중",
    "역량",
    "지원",
    "프로필",
    "시그널",
}


def _strip_html(text: str) -> str:
    clean = re.sub(r"<[^>]+>", "", text or "")
    return unescape(clean).strip()


def _normalize_title_for_dedupe(title: str) -> str:
    text = _strip_html(title).lower()
    while True:
        new_text = TITLE_PREFIX_RE.sub("", text).strip()
        if new_text == text:
            break
        text = new_text
    text = re.sub(r"[\"'“”‘’…·ㆍ,.:;!?()\[\]{}<>~_\-]+", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def _title_tokens(title: str) -> set[str]:
    normalized = _normalize_title_for_dedupe(title)
    compact = normalized.replace(" ", "")
    tokens = set()
    for token in TITLE_WORD_RE.findall(normalized):
        if token.endswith("에") and len(token) > 3:
            token = token[:-1]
        if token.startswith("한국") and len(token) > 4:
            tokens.add(token[2:])
        if token == "대표이사":
            token = "대표"
        if len(token) < 2 or token in TITLE_STOPWORDS:
            continue
        tokens.add(token)
    if "생산적금융" in compact:
        tokens.add("생산적금융")
    if "활성화" in compact:
        tokens.add("활성화")
    return tokens


def _is_similar_title(title: str, seen_title: str) -> bool:
    normalized = _normalize_title_for_dedupe(title)
    seen_normalized = _normalize_title_for_dedupe(seen_title)
    if not normalized or not seen_normalized:
        return False
    if normalized == seen_normalized:
        return True

    tokens = _title_tokens(normalized)
    seen_tokens = _title_tokens(seen_normalized)
    if len(tokens) < 3 or len(seen_tokens) < 3:
        overlap = len(tokens & seen_tokens)
        return overlap >= 2 and min(len(tokens), len(seen_tokens)) <= 3
    overlap = len(tokens & seen_tokens)
    ratio = overlap / min(len(tokens), len(seen_tokens))
    return overlap >= 4 and ratio >= 0.55


def _is_duplicate_title(article: dict, seen_titles: list[str]) -> bool:
    title = article.get("title", "")
    return any(_is_similar_title(title, seen_title) for seen_title in seen_titles)


def _today_kst() -> date:
    return datetime.now(KST).date()


def _parse_pub_date(pub_date: str) -> datetime | None:
    try:
        return datetime.strptime(pub_date, "%a, %d %b %Y %H:%M:%S %z")
    except ValueError:
        return None


def fetch_news(keyword: str, *, display: int = 50, sort: str = "date") -> list[dict]:
    """키워드로 네이버 뉴스 검색. API 키가 없으면 빈 목록 반환."""
    client_id = os.getenv("NAVER_CLIENT_ID", "").strip()
    client_secret = os.getenv("NAVER_CLIENT_SECRET", "").strip()
    if not client_id or not client_secret:
        return []

    headers = {
        "X-Naver-Client-Id": client_id,
        "X-Naver-Client-Secret": client_secret,
    }
    params = {
        "query": keyword,
        "display": min(max(display, 1), 100),
        "sort": sort,
    }

    response = requests.get(NAVER_NEWS_URL, headers=headers, params=params, timeout=15)
    response.raise_for_status()
    items = response.json().get("items", [])

    results = []
    for item in items:
        pub_date = item.get("pubDate", "")
        published_dt = _parse_pub_date(pub_date)
        if published_dt:
            published_str = published_dt.astimezone(KST).strftime("%Y-%m-%d")
            published_date = published_dt.astimezone(KST).date()
        else:
            published_str = pub_date
            published_date = None

        results.append(
            {
                "title": _strip_html(item.get("title", "")),
                "link": item.get("link", ""),
                "description": _strip_html(item.get("description", "")),
                "published": published_str,
                "published_date": published_date,
                "source_keyword": keyword,
            }
        )
    return results


def fetch_company_news(
    companies: list[dict],
    *,
    max_fetch_per_keyword: int = 50,
    today_only: bool = True,
    sort: str = "date",
) -> dict[str, list[dict]]:
    """기업별 뉴스 수집. 같은 링크 또는 같은 내용으로 보이는 제목은 한 번만 포함."""
    by_company: dict[str, list[dict]] = {}
    seen_links: set[str] = set()
    today = _today_kst()

    for company in companies:
        name = company["name"]
        keywords = company.get("news_keywords", [name])
        articles: list[dict] = []
        seen_titles: list[str] = []

        for keyword in keywords:
            for article in fetch_news(
                keyword, display=max_fetch_per_keyword, sort=sort
            ):
                if today_only:
                    pub_date = article.get("published_date")
                    if pub_date is None or pub_date != today:
                        continue

                link = article["link"]
                if not link or link in seen_links:
                    continue
                if _is_duplicate_title(article, seen_titles):
                    continue
                seen_links.add(link)
                seen_titles.append(article["title"])
                articles.append(article)

        by_company[name] = articles

    return by_company
