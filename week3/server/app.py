import logging
from typing import Any

from mcp.server.fastmcp import FastMCP

from .errors import ServiceError
from .fmp_service import FMPService

LOGGER = logging.getLogger(__name__)


def create_mcp_app(service: FMPService) -> FastMCP:
    mcp = FastMCP("financial-mcp-server")

    @mcp.tool()
    async def get_stock_quote(ticker: str) -> dict[str, Any]:
        """Get real-time stock quote by ticker."""
        LOGGER.info("Tool get_stock_quote called for ticker=%s", ticker)
        try:
            result = await service.get_stock_quote(ticker)
            return {"success": True, "data": result}
        except ServiceError as exc:
            LOGGER.warning("Tool get_stock_quote failed: %s", str(exc))
            return {"success": False, "error": str(exc)}

    @mcp.tool()
    async def get_financial_metrics(ticker: str) -> dict[str, Any]:
        """Get key financial metrics (market cap, PE ratio, EPS, etc.)."""
        LOGGER.info("Tool get_financial_metrics called for ticker=%s", ticker)
        try:
            result = await service.get_financial_metrics(ticker)
            return {"success": True, "data": result}
        except ServiceError as exc:
            LOGGER.warning("Tool get_financial_metrics failed: %s", str(exc))
            return {"success": False, "error": str(exc)}

    return mcp


def create_fastapi_app(mcp: FastMCP):
    """
    Optional FastAPI mount point for future HTTP transport.
    This keeps stdio and HTTP entrypoints sharing the same MCP app.
    """
    from fastapi import FastAPI

    app = FastAPI(title="Financial MCP Server")

    # Different MCP package versions expose different adapter names.
    for attr in ("asgi_app", "http_app", "sse_app"):
        if hasattr(mcp, attr):
            candidate = getattr(mcp, attr)
            mounted = candidate() if callable(candidate) else candidate
            app.mount("/mcp", mounted)
            return app

    @app.get("/health")
    async def health() -> dict[str, str]:
        return {"status": "ok", "note": "MCP HTTP adapter not available in this version"}

    return app

