"""뉴스·채용 데이터를 공통 요약 텍스트로 만듭니다."""

from __future__ import annotations

from datetime import datetime
from urllib.parse import quote_plus

KAKAO_TEXT_MAX = 200


def saramin_search_url(keyword: str) -> str:
    return (
        "https://www.saramin.co.kr/zf_user/search/recruit"
        f"?searchword={quote_plus(keyword)}&recruitPageCount=20"
    )


def _truncate(text: str, max_len: int) -> str:
    if len(text) <= max_len:
        return text
    if max_len <= 1:
        return text[:max_len]
    return text[: max_len - 1] + "…"


def _article_lines(articles: list[dict], title_max: int) -> list[str]:
    lines: list[str] = []
    for article in articles:
        title = _truncate(article["title"], title_max)
        link = article.get("link", "").strip()
        lines.append(f"• {title}")
        if link:
            lines.append(f"  {link}")
    return lines


def _fit_body(header: str, content_lines: list[str], max_len: int) -> str:
    """max_len 이내로 본문을 맞춥니다."""
    empty = f"{header}\n\n새 기사 없음"
    if not content_lines:
        return empty if len(empty) <= max_len else _truncate(empty, max_len)

    body = "\n".join(content_lines)
    message = f"{header}\n\n{body}"
    if len(message) <= max_len:
        return message

    return _truncate(message, max_len)


def _fit_articles(header: str, articles: list[dict], max_len: int) -> str:
    if not articles:
        return _fit_body(header, [], max_len)

    for count in range(len(articles), 0, -1):
        subset = articles[:count]
        for title_max in range(60, 8, -4):
            lines = _article_lines(subset, title_max)
            message = f"{header}\n\n" + "\n".join(lines)
            if len(message) <= max_len:
                return message

    article = articles[0]
    link = article.get("link", "").strip()
    title = article["title"]
    while title:
        lines = [f"• {_truncate(title, 20)}"]
        if link:
            lines.append(f"  {link}")
        message = f"{header}\n\n" + "\n".join(lines)
        if len(message) <= max_len:
            return message
        title = title[:-1]

    return _truncate(header, max_len)


def _fit_jobs(header: str, jobs: list[dict], max_len: int) -> str:
    if not jobs:
        return _fit_body(header, ["공고 없음"], max_len)

    for count in range(len(jobs), 0, -1):
        subset = jobs[:count]
        for title_max in range(40, 8, -4):
            lines: list[str] = []
            for job in subset:
                title = _truncate(job["title"], title_max)
                company = job.get("company") or "회사명 미상"
                keyword = job.get("source_keyword", "")
                link = job.get("link", "").strip()
                lines.append(f"• [{keyword}] {company}")
                lines.append(f"  {title}")
                if link:
                    lines.append(f"  {link}")
            message = f"{header}\n\n" + "\n".join(lines)
            if len(message) <= max_len:
                return message

    return _fit_body(header, ["공고가 많아 일부만 표시됩니다.", saramin_search_url(jobs[0].get("source_keyword", "회계"))], max_len)


def build_kakao_messages(
    company_news: dict[str, list[dict]],
    saramin_jobs: dict[str, list[dict]],
    max_len: int = KAKAO_TEXT_MAX,
) -> list[str]:
    """카카오톡용: 기업별 1메시지 + 사람인 1메시지. 각 메시지에 [N/M] 붙임."""
    today = datetime.now().strftime("%m-%d")
    # [N/M] 접두사 여유 (예: [4/10] )
    body_max = max_len - 8

    bodies: list[str] = []

    for company, articles in company_news.items():
        header = f"📰 {company} ({today})"
        bodies.append(_fit_articles(header, articles, body_max))

    all_jobs: list[dict] = []
    for keyword, jobs in saramin_jobs.items():
        all_jobs.extend(jobs)

    bodies.append(_fit_jobs(f"💼 사람인 채용 ({today})", all_jobs, body_max))

    total = len(bodies)
    messages: list[str] = []
    for index, body in enumerate(bodies, start=1):
        prefix = f"[{index}/{total}] "
        limit = max_len - len(prefix)
        if len(body) > limit:
            body = _truncate(body, limit)
        messages.append(prefix + body)

    return messages


def build_text_lines(
    company_news: dict[str, list[dict]],
    saramin_jobs: dict[str, list[dict]],
) -> list[str]:
    """레거시 텍스트 줄 (테스트·디버그용)."""
    today = datetime.now().strftime("%Y-%m-%d")
    lines = [f"📋 취업 브리핑 ({today})", ""]

    lines.append("📰 Big4·회계법인 뉴스")
    for company, articles in company_news.items():
        if not articles:
            lines.append(f"• {company}: 새 기사 없음")
            continue
        for article in articles:
            lines.append(f"• {company}: {article['title']}")
            if article.get("link"):
                lines.append(f"  {article['link']}")

    lines.append("")
    lines.append("💼 사람인 채용")
    for keyword, jobs in saramin_jobs.items():
        if not jobs:
            lines.append(f"• [{keyword}] 공고 없음")
            continue
        for job in jobs:
            lines.append(f"• [{keyword}] {job.get('company', '')} - {job['title']}")
            if job.get("link"):
                lines.append(f"  {job['link']}")

    return lines
