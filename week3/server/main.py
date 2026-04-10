import logging
import sys

from .app import create_mcp_app
from .config import get_fmp_api_key
from .fmp_service import FMPService


def setup_logging() -> None:
    root = logging.getLogger()
    root.setLevel(logging.INFO)
    root.handlers.clear()

    handler = logging.StreamHandler(sys.stderr)
    handler.setLevel(logging.INFO)
    formatter = logging.Formatter(
        "%(asctime)s %(levelname)s [%(name)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    handler.setFormatter(formatter)
    root.addHandler(handler)


def main() -> None:
    setup_logging()
    logger = logging.getLogger(__name__)

    api_key = get_fmp_api_key()
    service = FMPService(api_key=api_key)
    mcp = create_mcp_app(service)

    logger.info("Starting Financial MCP server using stdio transport")
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()

