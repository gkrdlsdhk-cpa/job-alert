"""뉴스·채용 데이터를 공통 요약 텍스트로 만듭니다."""

from __future__ import annotations

from datetime import datetime
from urllib.parse import quote_plus


def saramin_search_url(keyword: str) -> str:
    return (
        "https://www.saramin.co.kr/zf_user/search/recruit"
        f"?searchword={quote_plus(keyword)}&recruitPageCount=20"
    )


def build_text_lines(
    company_news: dict[str, list[dict]],
    saramin_jobs: dict[str, list[dict]],
) -> list[str]:
    today = datetime.now().strftime("%Y-%m-%d")
    lines = [f"📋 취업 브리핑 ({today})", ""]

    lines.append("📰 Big4·회계법인 뉴스")
    for company, articles in company_news.items():
        if not articles:
            lines.append(f"• {company}: 새 기사 없음")
            continue
        for article in articles[:2]:
            title = article["title"]
            if len(title) > 35:
                title = title[:35] + "…"
            lines.append(f"• {company}: {title}")

    lines.append("")
    lines.append("💼 사람인 채용")
    for keyword, jobs in saramin_jobs.items():
        if not jobs:
            lines.append(f"• [{keyword}] 공고 없음")
            continue
        for job in jobs[:2]:
            title = job["title"]
            if len(title) > 30:
                title = title[:30] + "…"
            company = job["company"] or "회사명 미상"
            lines.append(f"• [{keyword}] {company} - {title}")

    lines.append("")
    lines.append("job-alert 자동 발송")
    return lines


def chunk_lines(lines: list[str], max_len: int = 180) -> list[str]:
    """카카오톡 텍스트 메시지 한 건당 글자 수 제한(200자)에 맞게 나눕니다."""
    chunks: list[str] = []
    current = ""

    for line in lines:
        candidate = f"{current}\n{line}".strip() if current else line
        if len(candidate) <= max_len:
            current = candidate
            continue

        if current:
            chunks.append(current)
        if len(line) <= max_len:
            current = line
        else:
            start = 0
            while start < len(line):
                chunks.append(line[start : start + max_len])
                start += max_len
            current = ""

    if current:
        chunks.append(current)

    if len(chunks) > 1:
        total = len(chunks)
        chunks = [f"[{idx}/{total}] {body}" for idx, body in enumerate(chunks, start=1)]

    return chunks
