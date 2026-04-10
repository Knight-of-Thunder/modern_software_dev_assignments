import os


DEFAULT_BASE_URL = "https://financialmodelingprep.com"
DEFAULT_TIMEOUT_SECONDS = 10.0


def get_fmp_api_key() -> str:
    api_key = os.getenv("FMP_API_KEY", "").strip()
    if not api_key:
        raise ValueError("FMP_API_KEY is not set. Please export FMP_API_KEY first.")
    return api_key

