"""웹 브리핑 HTML 페이지를 생성합니다."""

from __future__ import annotations

from datetime import datetime
from html import escape
from pathlib import Path
from urllib.parse import quote_plus


def saramin_search_url(keyword: str) -> str:
    return (
        "https://www.saramin.co.kr/zf_user/search/recruit"
        f"?searchword={quote_plus(keyword)}&recruitPageCount=20"
    )


def render_html(
    company_news: dict[str, list[dict]],
    saramin_jobs: dict[str, list[dict]],
) -> str:
    today = datetime.now()
    title_date = today.strftime("%Y년 %m월 %d일")
    updated = today.strftime("%Y-%m-%d %H:%M")

    sections: list[str] = []

    sections.append(
        f"""
        <section>
          <h2>📰 Big4·회계법인 뉴스</h2>
        """
    )
    for company, articles in company_news.items():
        sections.append(f'<div class="company"><h3>{escape(company)}</h3>')
        if not articles:
            sections.append('<p class="empty">새 기사가 없습니다.</p>')
        else:
            sections.append("<ul>")
            for article in articles:
                sections.append(
                    "<li>"
                    f'<a href="{escape(article["link"])}" target="_blank" rel="noopener">'
                    f'{escape(article["title"])}</a>'
                    f'<span class="meta">{escape(article["published"])}</span>'
                    f'<p class="desc">{escape(article["description"])}</p>'
                    "</li>"
                )
            sections.append("</ul>")
        sections.append("</div>")
    sections.append("</section>")

    sections.append(
        """
        <section>
          <h2>💼 사람인 채용</h2>
        """
    )
    for keyword, jobs in saramin_jobs.items():
        sections.append(f'<div class="company"><h3>키워드: {escape(keyword)}</h3>')
        sections.append(
            f'<p class="more"><a href="{escape(saramin_search_url(keyword))}" '
            f'target="_blank" rel="noopener">사람인에서 더 보기</a></p>'
        )
        if not jobs:
            sections.append('<p class="empty">공고를 가져오지 못했습니다.</p>')
        else:
            sections.append("<ul>")
            for job in jobs:
                sections.append(
                    "<li>"
                    f'<a href="{escape(job["link"])}" target="_blank" rel="noopener">'
                    f'{escape(job["title"])}</a>'
                    f'<span class="meta">{escape(job.get("company", ""))} · {escape(job.get("date", ""))}</span>'
                    f'<p class="desc">{escape(job.get("condition", ""))}</p>'
                    "</li>"
                )
            sections.append("</ul>")
        sections.append("</div>")
    sections.append("</section>")

    body = "\n".join(sections)

    return f"""<!DOCTYPE html>
<html lang="ko">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>취업 브리핑 {title_date}</title>
  <style>
    * {{ box-sizing: border-box; }}
    body {{
      font-family: -apple-system, BlinkMacSystemFont, "Apple SD Gothic Neo", sans-serif;
      margin: 0;
      padding: 16px;
      background: #f5f6f8;
      color: #222;
      line-height: 1.5;
    }}
    .wrap {{
      max-width: 720px;
      margin: 0 auto;
      background: #fff;
      border-radius: 12px;
      padding: 20px;
      box-shadow: 0 2px 8px rgba(0,0,0,.06);
    }}
    h1 {{ font-size: 1.35rem; margin: 0 0 4px; }}
    .sub {{ color: #666; font-size: .9rem; margin-bottom: 20px; }}
    h2 {{ font-size: 1.1rem; margin: 24px 0 12px; border-bottom: 2px solid #fee500; padding-bottom: 6px; }}
    h3 {{ font-size: 1rem; margin: 16px 0 8px; color: #333; }}
    ul {{ list-style: none; padding: 0; margin: 0; }}
    li {{
      padding: 12px 0;
      border-bottom: 1px solid #eee;
    }}
    li:last-child {{ border-bottom: none; }}
    a {{ color: #1a1a1a; text-decoration: none; font-weight: 600; }}
    a:hover {{ text-decoration: underline; }}
    .meta {{ display: block; font-size: .82rem; color: #888; margin-top: 4px; font-weight: 400; }}
    .desc {{ font-size: .88rem; color: #555; margin: 6px 0 0; }}
    .empty {{ color: #888; font-size: .9rem; }}
    .more {{ margin: 0 0 8px; font-size: .88rem; }}
    .footer {{ margin-top: 24px; font-size: .78rem; color: #999; text-align: center; }}
  </style>
</head>
<body>
  <div class="wrap">
    <h1>📋 오늘의 취업 브리핑</h1>
    <p class="sub">{title_date} · 업데이트 {updated}</p>
    {body}
    <p class="footer">job-alert 자동 생성</p>
  </div>
</body>
</html>
"""


def write_briefing(
    output_path: Path,
    company_news: dict[str, list[dict]],
    saramin_jobs: dict[str, list[dict]],
) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        render_html(company_news, saramin_jobs),
        encoding="utf-8",
    )
    return output_path
