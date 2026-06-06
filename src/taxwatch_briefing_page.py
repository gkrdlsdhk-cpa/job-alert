"""TaxWatch 세금 뉴스 브리핑 HTML."""

from __future__ import annotations

from datetime import datetime
from html import escape
from zoneinfo import ZoneInfo

KST = ZoneInfo("Asia/Seoul")


def render_html(articles: list[dict]) -> str:
    today = datetime.now(KST)
    title_date = today.strftime("%Y년 %m월 %d일")
    updated = today.strftime("%Y-%m-%d %H:%M")

    if articles:
        items_html = ["<ul>"]
        for article in articles:
            items_html.append(
                "<li>"
                f'<a href="{escape(article["link"])}" target="_blank" rel="noopener">'
                f'{escape(article["title"])}</a>'
                f'<span class="meta">{escape(article.get("published", ""))}'
                f'{(" · " + escape(article["author"])) if article.get("author") else ""}</span>'
                f'<p class="desc">{escape(article.get("summary", ""))}</p>'
                "</li>"
            )
        items_html.append("</ul>")
        body = "\n".join(items_html)
        count_line = f'<p class="count">오늘 기사 {len(articles)}건</p>'
    else:
        body = '<p class="empty">오늘 올라온 TaxWatch 기사가 없습니다.</p>'
        count_line = ""

    return f"""<!DOCTYPE html>
<html lang="ko">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>세금 뉴스 {title_date}</title>
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
    .sub {{ color: #666; font-size: .9rem; margin-bottom: 12px; }}
    .count {{ color: #444; font-size: .92rem; margin: 0 0 16px; }}
    h2 {{ font-size: 1.1rem; margin: 0 0 12px; border-bottom: 2px solid #2f6fed; padding-bottom: 6px; }}
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
    .footer {{ margin-top: 24px; font-size: .78rem; color: #999; text-align: center; }}
  </style>
</head>
<body>
  <div class="wrap">
    <h1>📰 TaxWatch 세금 뉴스</h1>
    <p class="sub">{title_date} · 업데이트 {updated}</p>
    {count_line}
    <section>
      <h2>최신뉴스</h2>
      {body}
    </section>
    <p class="footer">job-alert · <a href="https://www.taxwatch.co.kr/search">taxwatch.co.kr</a></p>
  </div>
</body>
</html>
"""
