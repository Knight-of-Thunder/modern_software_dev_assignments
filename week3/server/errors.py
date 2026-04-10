class ServiceError(Exception):
    """Base error for upstream API and validation failures."""


class InvalidTickerError(ServiceError):
    """Raised when ticker format is invalid."""


class NotFoundError(ServiceError):
    """Raised when requested symbol has no data."""


class UpstreamTimeoutError(ServiceError):
    """Raised when upstream API request times out."""


class UpstreamAPIError(ServiceError):
    """Raised when upstream API returns an error."""

