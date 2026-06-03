"""네이버 뉴스 검색 API로 기업 관련 기사를 가져옵니다."""

from __future__ import annotations

import os
from datetime import datetime
from html import unescape
import re

import requests


NAVER_NEWS_URL = "https://openapi.naver.com/v1/search/news.json"


def _strip_html(text: str) -> str:
    clean = re.sub(r"<[^>]+>", "", text or "")
    return unescape(clean).strip()


def fetch_news(keyword: str, display: int = 3) -> list[dict]:
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
        "display": display,
        "sort": "date",
    }

    response = requests.get(NAVER_NEWS_URL, headers=headers, params=params, timeout=15)
    response.raise_for_status()
    items = response.json().get("items", [])

    results = []
    for item in items:
        pub_date = item.get("pubDate", "")
        try:
            published = datetime.strptime(pub_date, "%a, %d %b %Y %H:%M:%S %z")
            published_str = published.strftime("%Y-%m-%d")
        except ValueError:
            published_str = pub_date

        results.append(
            {
                "title": _strip_html(item.get("title", "")),
                "link": item.get("link", ""),
                "description": _strip_html(item.get("description", "")),
                "published": published_str,
                "source_keyword": keyword,
            }
        )
    return results


def fetch_company_news(companies: list[dict], news_per_keyword: int) -> dict[str, list[dict]]:
    """기업별 뉴스 수집. 같은 링크는 한 번만 포함."""
    by_company: dict[str, list[dict]] = {}
    seen_links: set[str] = set()

    for company in companies:
        name = company["name"]
        keywords = company.get("news_keywords", [name])
        articles: list[dict] = []

        for keyword in keywords:
            for article in fetch_news(keyword, display=news_per_keyword):
                link = article["link"]
                if link in seen_links:
                    continue
                seen_links.add(link)
                articles.append(article)

        by_company[name] = articles

    return by_company
