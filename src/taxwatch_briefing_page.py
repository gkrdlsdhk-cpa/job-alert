"""세금 뉴스 브리핑 HTML (TaxWatch + 이택스뉴스 + 한국경제 + 택스타임스)."""

from __future__ import annotations

from datetime import datetime
from html import escape
from zoneinfo import ZoneInfo

KST = ZoneInfo("Asia/Seoul")


def _render_section(title: str, articles: list[dict]) -> str:
    if not articles:
        return f"<section><h2>{escape(title)}</h2><p class=\"empty\">오늘 새 기사 없음</p></section>"

    items_html = ["<ul>"]
    for article in articles:
        meta = escape(article.get("published", ""))
        if article.get("author"):
            meta += f" · {escape(article['author'])}"
        items_html.append(
            "<li>"
            f'<a href="{escape(article["link"])}" target="_blank" rel="noopener">'
            f'{escape(article["title"])}</a>'
            f'<span class="meta">{meta}</span>'
        )
        summary = article.get("summary", "").strip()
        if summary:
            items_html.append(f'<p class="desc">{escape(summary)}</p>')
        items_html.append("</li>")
    items_html.append("</ul>")
    return f"<section><h2>{escape(title)}</h2>\n" + "\n".join(items_html) + "\n</section>"


def render_html(sections: dict[str, list[dict]]) -> str:
    today = datetime.now(KST)
    title_date = today.strftime("%Y년 %m월 %d일")
    updated = today.strftime("%Y-%m-%d %H:%M")
    total = sum(len(articles) for articles in sections.values())

    if total:
        count_line = f'<p class="count">오늘 기사 {total}건</p>'
        body = "\n".join(_render_section(title, articles) for title, articles in sections.items())
    else:
        count_line = ""
        body = '<p class="empty">오늘 올라온 세금 뉴스 기사가 없습니다.</p>'

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
    h2 {{ font-size: 1.1rem; margin: 24px 0 12px; border-bottom: 2px solid #2f6fed; padding-bottom: 6px; }}
    section:first-of-type h2 {{ margin-top: 0; }}
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
    <h1>📰 세금 뉴스 브리핑</h1>
    <p class="sub">{title_date} · 업데이트 {updated}</p>
    {count_line}
    {body}
    <p class="footer">job-alert · TaxWatch · 이택스뉴스 · 한국경제 · 택스타임스</p>
  </div>
</body>
</html>
"""
