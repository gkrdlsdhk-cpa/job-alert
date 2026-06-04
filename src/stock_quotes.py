"""Yahoo Finance API로 미국 주식 시세를 조회합니다."""

from __future__ import annotations

from dataclasses import dataclass

import requests

YAHOO_SPARK_URL = "https://query1.finance.yahoo.com/v7/finance/spark"
YAHOO_CHART_URLS = (
    "https://query1.finance.yahoo.com/v8/finance/chart/{symbol}",
    "https://query2.finance.yahoo.com/v8/finance/chart/{symbol}",
)
DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    ),
}


@dataclass(frozen=True)
class StockQuote:
    symbol: str
    name: str
    price: float
    change_pct: float
    currency: str


def _quote_from_meta(symbol: str, name: str, meta: dict) -> StockQuote:
    price = meta.get("regularMarketPrice")
    previous = meta.get("chartPreviousClose") or meta.get("previousClose")
    if price is None:
        raise ValueError(f"{symbol} 현재가를 찾을 수 없습니다.")

    change_pct = 0.0
    if previous:
        change_pct = (float(price) - float(previous)) / float(previous) * 100

    return StockQuote(
        symbol=symbol.upper(),
        name=name,
        price=float(price),
        change_pct=change_pct,
        currency=str(meta.get("currency", "USD")),
    )


def _fetch_spark_json(symbols: list[str]) -> dict:
    response = requests.get(
        YAHOO_SPARK_URL,
        params={
            "symbols": ",".join(symbols),
            "range": "2d",
            "interval": "1d",
        },
        headers=DEFAULT_HEADERS,
        timeout=15,
    )
    response.raise_for_status()
    return response.json()


def _fetch_chart_json(symbol: str) -> dict:
    """Yahoo chart API (spark 실패 시 종목별 폴백)."""
    params = {"interval": "1d", "range": "2d"}
    last_error: Exception | None = None
    for url_template in YAHOO_CHART_URLS:
        url = url_template.format(symbol=symbol.upper())
        try:
            response = requests.get(
                url,
                params=params,
                headers=DEFAULT_HEADERS,
                timeout=15,
            )
            response.raise_for_status()
            return response.json()
        except requests.RequestException as exc:
            last_error = exc
    if last_error:
        raise last_error
    raise RuntimeError(f"{symbol} 시세 조회에 실패했습니다.")


def _fetch_quote_fallback(symbol: str, name: str) -> StockQuote:
    payload = _fetch_chart_json(symbol)
    result = payload.get("chart", {}).get("result")
    if not result:
        raise ValueError(f"{symbol} 시세 데이터를 찾을 수 없습니다.")
    return _quote_from_meta(symbol, name, result[0].get("meta", {}))


def fetch_quotes(symbols: list[dict[str, str]]) -> list[StockQuote]:
    """config의 symbols 목록 순서대로 시세를 조회합니다 (한 번에 요청)."""
    if not symbols:
        return []

    names = {
        entry["symbol"].upper(): entry.get("name", entry["symbol"])
        for entry in symbols
    }
    ordered_symbols = [entry["symbol"].upper() for entry in symbols]

    try:
        payload = _fetch_spark_json(ordered_symbols)
        spark_result = payload.get("spark", {}).get("result") or []
        by_symbol: dict[str, StockQuote] = {}
        for item in spark_result:
            symbol = str(item.get("symbol", "")).upper()
            responses = item.get("response") or []
            if not symbol or not responses:
                continue
            meta = responses[0].get("meta", {})
            by_symbol[symbol] = _quote_from_meta(symbol, names[symbol], meta)

        quotes: list[StockQuote] = []
        for symbol in ordered_symbols:
            if symbol in by_symbol:
                quotes.append(by_symbol[symbol])
            else:
                quotes.append(_fetch_quote_fallback(symbol, names[symbol]))
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
