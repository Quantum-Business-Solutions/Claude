"""Python client for the CEO Juice Service Call Client API (e-automate)."""

from .client import (
    DEFAULT_BASE_URL,
    LIST_ROUTES,
    RECENT_CHANGES_MAX_AGE,
    CeoJuiceClient,
    CeoJuiceError,
)

__all__ = [
    "CeoJuiceClient",
    "CeoJuiceError",
    "DEFAULT_BASE_URL",
    "LIST_ROUTES",
    "RECENT_CHANGES_MAX_AGE",
]
