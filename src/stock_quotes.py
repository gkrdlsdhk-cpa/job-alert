"""네이버 증권 해외주식 페이지에서 미국 주식 시세를 조회합니다."""

from __future__ import annotations

import json
import re
import time
from dataclasses import dataclass
from typing import Any

import requests

NAVER_WORLD_STOCK_URL = "https://m.stock.naver.com/worldstock/stock/{code}/total"
DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "ko-KR,ko;q=0.9",
}


@dataclass(frozen=True)
class StockQuote:
    symbol: str
    name: str
    price: float
    change_pct: float
    currency: str
    link: str


def _find_stock_payload(data: Any) -> dict[str, Any] | None:
    """__NEXT_DATA__ 안에서 closePrice·fluctuationsRatio가 있는 객체를 찾습니다."""
    if isinstance(data, dict):
        if "closePrice" in data and "fluctuationsRatio" in data:
            return data
        for value in data.values():
            found = _find_stock_payload(value)
            if found:
                return found
    elif isinstance(data, list):
        for item in data:
            found = _find_stock_payload(item)
            if found:
                return found
    return None


def _parse_naver_code(entry: dict[str, str]) -> str:
    code = entry.get("naver_code", "").strip().upper()
    if code:
        return code
    symbol = entry.get("symbol", "").strip().upper()
    if not symbol:
        raise ValueError("stock_alert 항목에 naver_code 또는 symbol이 필요합니다.")
    return f"{symbol}.O" if "." not in symbol else symbol


def _display_symbol(entry: dict[str, str], naver_code: str) -> str:
    symbol = entry.get("symbol", "").strip().upper()
    if symbol:
        return symbol
    return naver_code.split(".", 1)[0]


def fetch_quote(entry: dict[str, str]) -> StockQuote:
    """네이버 증권 해외주식 1종목 시세."""
    naver_code = _parse_naver_code(entry)
    name = entry.get("name", _display_symbol(entry, naver_code))
    url = NAVER_WORLD_STOCK_URL.format(code=naver_code)

    last_error: Exception | None = None
    for attempt in range(3):
        try:
            response = requests.get(url, headers=DEFAULT_HEADERS, timeout=20)
            response.raise_for_status()
            match = re.search(
                r'<script id="__NEXT_DATA__"[^>]*>(.+?)</script>',
                response.text,
                re.DOTALL,
            )
            if not match:
                raise ValueError(f"{naver_code}: 시세 데이터(JSON)를 찾을 수 없습니다.")

            page_data = json.loads(match.group(1))
            stock = _find_stock_payload(page_data.get("props", {}).get("pageProps", {}))
            if not stock:
                raise ValueError(f"{naver_code}: 종목 시세 필드를 찾을 수 없습니다.")

            price = float(str(stock["closePrice"]).replace(",", ""))
            change_pct = float(str(stock["fluctuationsRatio"]).replace(",", ""))
            currency = str(stock.get("currencyType", {}).get("code", "USD"))

            page_link = str(stock.get("newPcUrl") or stock.get("endUrl") or url)
            return StockQuote(
                symbol=_display_symbol(entry, naver_code),
                name=str(stock.get("stockName") or name),
                price=price,
                change_pct=change_pct,
                currency=currency,
                link=page_link,
            )
        except (requests.RequestException, ValueError, json.JSONDecodeError, KeyError) as exc:
            last_error = exc
            if attempt < 2:
                time.sleep(1.5 * (attempt + 1))

    if last_error:
        raise last_error
    raise RuntimeError(f"{naver_code} 시세 조회에 실패했습니다.")


def fetch_quotes(symbols: list[dict[str, str]]) -> list[StockQuote]:
    """config의 symbols 목록 순서대로 시세를 조회합니다."""
    quotes: list[StockQuote] = []
    for index, entry in enumerate(symbols):
        if index:
            time.sleep(0.5)
        quotes.append(fetch_quote(entry))
    return quotes


def format_kakao_body(quotes: list[StockQuote], *, as_of: str) -> str:
    """카카오 텍스트 메시지 본문 (200자 제한 고려)."""
    lines = [as_of]
    for q in quotes:
        sign = "+" if q.change_pct >= 0 else ""
        lines.append(
            f"{q.name}({q.symbol}) ${q.price:,.2f} {sign}{q.change_pct:.2f}%"
        )
    return "\n".join(lines)
