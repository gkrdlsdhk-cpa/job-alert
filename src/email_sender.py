"""수집한 내용을 Gmail로 보냅니다."""

from __future__ import annotations

import os
import smtplib
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from src.briefing_page import render_html


def send_digest(
    company_news: dict[str, list[dict]],
    saramin_jobs: dict[str, list[dict]],
) -> str:
    """전체 브리핑 HTML 메일 발송. 받는 주소를 반환."""
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
    html_body = render_html(company_news, saramin_jobs)

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
