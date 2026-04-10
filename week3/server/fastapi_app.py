from .app import create_fastapi_app, create_mcp_app
from .config import get_fmp_api_key
from .fmp_service import FMPService

service = FMPService(api_key=get_fmp_api_key())
mcp = create_mcp_app(service)
app = create_fastapi_app(mcp)

