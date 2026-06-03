"""수집한 내용을 이메일로 보냅니다."""

from __future__ import annotations

import os
import smtplib
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from urllib.parse import quote_plus


def _saramin_search_url(keyword: str) -> str:
    return (
        "https://www.saramin.co.kr/zf_user/search/recruit"
        f"?searchword={quote_plus(keyword)}&recruitPageCount=20"
    )


def _build_html(
    company_news: dict[str, list[dict]],
    saramin_jobs: dict[str, list[dict]],
) -> str:
    today = datetime.now().strftime("%Y년 %m월 %d일")
    parts = [
        f"<h1>오늘의 취업 브리핑 ({today})</h1>",
        "<p>Big4·회계법인 뉴스 + 사람인 채용 공고입니다.</p>",
        "<hr>",
    ]

    parts.append("<h2>📰 기업 뉴스 (네이버)</h2>")
    for company, articles in company_news.items():
        parts.append(f"<h3>{company}</h3>")
        if not articles:
            parts.append("<p>새 기사가 없거나 API 설정을 확인해 주세요.</p>")
            continue
        parts.append("<ul>")
        for article in articles:
            parts.append(
                "<li>"
                f'<a href="{article["link"]}">{article["title"]}</a>'
                f' <small>({article["published"]})</small>'
                f"<br><small>{article['description']}</small>"
                "</li>"
            )
        parts.append("</ul>")

    parts.append("<hr><h2>💼 사람인 채용 공고</h2>")
    for keyword, jobs in saramin_jobs.items():
        parts.append(f"<h3>키워드: {keyword}</h3>")
        parts.append(f'<p><a href="{_saramin_search_url(keyword)}">사람인에서 더 보기</a></p>')
        if not jobs:
            parts.append("<p>공고를 가져오지 못했습니다. 위 링크에서 직접 확인해 주세요.</p>")
            continue
        parts.append("<ul>")
        for job in jobs:
            parts.append(
                "<li>"
                f'<a href="{job["link"]}">{job["title"]}</a>'
                f" — {job['company']}"
                f" <small>({job['date']})</small>"
                f"<br><small>{job['condition']}</small>"
                "</li>"
            )
        parts.append("</ul>")

    parts.append("<hr><p><small>job-alert 자동 발송</small></p>")
    return "\n".join(parts)


def send_digest(
    company_news: dict[str, list[dict]],
    saramin_jobs: dict[str, list[dict]],
) -> None:
    email_from = os.getenv("EMAIL_FROM", "").strip()
    email_password = os.getenv("EMAIL_PASSWORD", "").strip()
    email_to = os.getenv("EMAIL_TO", email_from).strip()
    smtp_host = os.getenv("SMTP_HOST", "smtp.gmail.com").strip()
    smtp_port = int(os.getenv("SMTP_PORT", "587"))

    if not email_from or not email_password:
        raise ValueError(
            "EMAIL_FROM, EMAIL_PASSWORD를 .env 파일에 설정해 주세요. "
            "Gmail은 '앱 비밀번호'를 사용해야 합니다."
        )

    today = datetime.now().strftime("%Y-%m-%d")
    subject = f"[취업 브리핑] {today} Big4 뉴스 & 사람인 채용"
    html_body = _build_html(company_news, saramin_jobs)

    message = MIMEMultipart("alternative")
    message["Subject"] = subject
    message["From"] = email_from
    message["To"] = email_to
    message.attach(MIMEText(html_body, "html", "utf-8"))

    with smtplib.SMTP(smtp_host, smtp_port) as server:
        server.starttls()
        server.login(email_from, email_password)
        server.sendmail(email_from, [email_to], message.as_string())
