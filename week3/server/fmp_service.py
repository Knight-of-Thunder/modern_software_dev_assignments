import logging
import re
from typing import Any

import httpx

from .config import DEFAULT_BASE_URL, DEFAULT_TIMEOUT_SECONDS
from .errors import (
    InvalidTickerError,
    NotFoundError,
    UpstreamAPIError,
    UpstreamTimeoutError,
)

LOGGER = logging.getLogger(__name__)
TICKER_PATTERN = re.compile(r"^[A-Za-z.\-]{1,10}$")


class FMPService:
    def __init__(
        self,
        api_key: str,
        base_url: str = DEFAULT_BASE_URL,
        timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS,
    ) -> None:
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.timeout_seconds = timeout_seconds

    @staticmethod
    def _validate_ticker(ticker: str) -> str:
        symbol = ticker.strip().upper()
        if not symbol or not TICKER_PATTERN.match(symbol):
            raise InvalidTickerError(
                "Invalid ticker format. Use letters, dot or dash, up to 10 chars."
            )
        return symbol

    async def _get(
        self, path: str, extra_params: dict[str, str] | None = None
    ) -> list[dict[str, Any]]:
        url = f"{self.base_url}{path}"
        params = {"apikey": self.api_key}
        if extra_params:
            params.update(extra_params)
        try:
            async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
                response = await client.get(url, params=params)
            response.raise_for_status()
        except httpx.TimeoutException as exc:
            LOGGER.exception("Upstream timeout for path=%s", path)
            raise UpstreamTimeoutError("Upstream request timed out.") from exc
        except httpx.HTTPStatusError as exc:
            status = exc.response.status_code
            LOGGER.exception("Upstream HTTP error status=%s path=%s", status, path)
            response_text = exc.response.text
            if status == 403 and "Legacy Endpoint" in response_text:
                raise UpstreamAPIError(
                    "Endpoint is marked as legacy by FMP. Please use /stable endpoints."
                ) from exc
            if status == 403:
                raise UpstreamAPIError(
                    "Upstream API denied access (HTTP 403). Check FMP API key and plan access."
                ) from exc
            if status == 429:
                raise UpstreamAPIError(
                    "API rate limit exceeded. Please retry later."
                ) from exc
            raise UpstreamAPIError(f"Upstream API returned HTTP {status}.") from exc
        except httpx.HTTPError as exc:
            LOGGER.exception("Unexpected upstream HTTP error path=%s", path)
            raise UpstreamAPIError("Failed to call upstream API.") from exc

        payload = response.json()
        if not isinstance(payload, list):
            LOGGER.error("Unexpected payload type for path=%s: %s", path, type(payload))
            raise UpstreamAPIError("Unexpected upstream payload format.")
        return payload

    async def get_stock_quote(self, ticker: str) -> dict[str, Any]:
        symbol = self._validate_ticker(ticker)
        data = await self._get("/stable/quote", {"symbol": symbol})
        if not data:
            raise NotFoundError(f"No quote data found for ticker '{symbol}'.")

        quote = data[0]
        return {
            "ticker": symbol,
            "price": quote.get("price"),
            "day_high": quote.get("dayHigh"),
            "day_low": quote.get("dayLow"),
            "change_percent": quote.get("changesPercentage"),
            "timestamp": quote.get("timestamp"),
        }

    async def get_financial_metrics(self, ticker: str) -> dict[str, Any]:
        symbol = self._validate_ticker(ticker)
        data = await self._get("/stable/profile", {"symbol": symbol})
        if not data:
            raise NotFoundError(f"No financial metrics found for ticker '{symbol}'.")

        profile = data[0]
        return {
            "ticker": symbol,
            "company_name": profile.get("companyName"),
            "market_cap": profile.get("mktCap"),
            "pe_ratio": profile.get("pe"),
            "eps": profile.get("eps"),
            "industry": profile.get("industry"),
            "sector": profile.get("sector"),
            "exchange": profile.get("exchangeShortName"),
        }

