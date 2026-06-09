"""수집한 내용을 Gmail로 보냅니다."""

from __future__ import annotations

import os
import smtplib
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from src.briefing_page import render_news_html


def _send_html_email(*, subject: str, html_body: str) -> str:
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

    message = MIMEMultipart("alternative")
    message["Subject"] = subject
    message["From"] = email_from
    message["To"] = email_to
    message.attach(MIMEText(html_body, "html", "utf-8"))

    with smtplib.SMTP(smtp_host, smtp_port) as server:
        server.starttls()
        server.login(email_from, email_password)
        server.sendmail(email_from, [email_to], message.as_string())

    return email_to


def send_news_digest(company_news: dict[str, list[dict]]) -> str:
    """회계법인 뉴스 HTML 메일 발송."""
    today = datetime.now().strftime("%Y-%m-%d")
    subject = f"[회계법인 뉴스] {today}"
    return _send_html_email(subject=subject, html_body=render_news_html(company_news))


def send_digest(
    company_news: dict[str, list[dict]],
    saramin_jobs: dict[str, list[dict]],
) -> str:
    """레거시: 뉴스 + 채용 한 통 메일."""
    today = datetime.now().strftime("%Y-%m-%d")
    subject = f"[취업 브리핑] {today} Big4 뉴스 & 사람인 채용"
    from src.briefing_page import render_html

    return _send_html_email(subject=subject, html_body=render_html(company_news, saramin_jobs))
