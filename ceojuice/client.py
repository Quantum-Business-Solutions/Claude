"""Client for the CEO Juice Service Call Client API (e-automate data).

Auth is a two-step dance: POST /api/Auth/token with username+password to get a
JWT, then send it as `Authorization: Bearer <token>` on every other call. The
JWT carries the API key's identity (ApiKeyId, CustomerIds) and its permission
claims, so the `eaapikey` header documented in Swagger is not needed alongside
it.

The token is cached on the instance and refreshed automatically a minute before
it expires.
"""

from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone
from typing import Any, Iterator

DEFAULT_BASE_URL = "https://devclientsapi.ceojuice.com"

# Swagger advertises a /api/ListsAndCodes/* family for shared lookups, but that
# family is gated on a claim that ordinary API keys do not get -- it answers 403.
# Every list is duplicated under a domain route that is gated on the domain claim
# instead, and those do answer. get_list() resolves names through this map so
# callers never have to know which family works.
LIST_ROUTES = {
    "CallTypes": "/api/ServiceCall/CallTypes",
    "ProblemCodes": "/api/ServiceCall/ProblemCodes",
    "RepairCodes": "/api/ServiceCall/RepairCodes",
    "CancelCodes": "/api/ServiceCall/CancelCodes",
    "OnHoldCodes": "/api/ServiceCall/OnHoldCodes",
    "Priorities": "/api/ServiceCall/Priorities",
    "NoteTypes": "/api/ServiceCall/NoteTypes",
    "SLACodes": "/api/ServiceCall/SLACodes",
    "States": "/api/Customer/States",
    "Countries": "/api/Customer/Countries",
    "Terms": "/api/Customer/Terms",
    "PriceLevels": "/api/Customer/PriceLevels",
    "OrderTypes": "/api/SalesOrder/OrderTypes",
    "OrderStatuses": "/api/SalesOrder/OrderStatuses",
    "ShipMethods": "/api/SalesOrder/ShipMethods",
    "MeterTypes": "/api/MeterReadings/MeterTypes",
    "Makes": "/api/Item/Makes",
    "Models": "/api/Item/Models",
    "ModelCategories": "/api/Item/ModelCategories",
}

# The API rejects (or silently ignores) a sinceTime further back than this.
RECENT_CHANGES_MAX_AGE = timedelta(days=7)


class CeoJuiceError(RuntimeError):
    """An API call came back with a non-2xx status."""

    def __init__(self, status: int, method: str, path: str, body: str):
        self.status = status
        self.method = method
        self.path = path
        self.body = body
        super().__init__(f"{method} {path} -> HTTP {status}: {body[:400]}")


class CeoJuiceClient:
    def __init__(
        self,
        username: str | None = None,
        password: str | None = None,
        base_url: str | None = None,
        timeout: int = 60,
        max_retries: int = 4,
    ):
        self.username = username or os.environ.get("CEOJUICE_USERNAME") or ""
        self.password = password or os.environ.get("CEOJUICE_PASSWORD") or ""
        self.base_url = (
            base_url or os.environ.get("CEOJUICE_BASE_URL") or DEFAULT_BASE_URL
        ).rstrip("/")
        self.timeout = timeout
        self.max_retries = max_retries
        if not self.username or not self.password:
            raise ValueError(
                "Set CEOJUICE_USERNAME and CEOJUICE_PASSWORD (or pass them in)."
            )
        self._token: str | None = None
        self._expires: datetime | None = None

    # -- auth ---------------------------------------------------------------

    def authenticate(self) -> str:
        """Trade username/password for a JWT and cache it."""
        payload = {"username": self.username, "password": self.password}
        data = self._raw_request(
            "POST", "/api/Auth/token", body=payload, authenticated=False
        )
        self._token = data["token"]
        # "expires" is UTC; refresh a minute early so a call never races expiry.
        self._expires = _parse_utc(data["expires"]) - timedelta(minutes=1)
        return self._token

    @property
    def token(self) -> str:
        if self._token is None or (
            self._expires and datetime.now(timezone.utc) >= self._expires
        ):
            self.authenticate()
        assert self._token is not None
        return self._token

    def claims(self) -> dict[str, str]:
        """Flatten /api/Test into {claim: value} -- the permissions this key has."""
        return {c["type"]: c["value"] for c in self.get("/api/Test")}

    # -- transport ----------------------------------------------------------

    def _raw_request(
        self,
        method: str,
        path: str,
        params: dict[str, Any] | None = None,
        body: Any = None,
        authenticated: bool = True,
    ) -> Any:
        url = self.base_url + path
        if params:
            clean = {k: v for k, v in params.items() if v is not None}
            if clean:
                url += "?" + urllib.parse.urlencode(clean)

        headers = {"Accept": "application/json"}
        if authenticated:
            headers["Authorization"] = "Bearer " + self.token

        encoded = None
        if body is not None:
            encoded = json.dumps(body).encode("utf-8")
            headers["Content-Type"] = "application/json"

        req = urllib.request.Request(url, data=encoded, headers=headers, method=method)

        # The host resets connections under sustained sequential load, and a
        # bulk pull walks hundreds of pages, so transient faults are expected
        # rather than exceptional. 5xx and 429 are retried the same way; 4xx is
        # a real answer about the request and surfaces immediately.
        text = None
        for attempt in range(self.max_retries + 1):
            try:
                with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                    text = resp.read().decode("utf-8", "replace")
                break
            except urllib.error.HTTPError as exc:
                detail = exc.read().decode("utf-8", "replace")
                retryable = exc.code == 429 or exc.code >= 500
                if not retryable or attempt == self.max_retries:
                    raise CeoJuiceError(exc.code, method, path, detail) from None
            except (urllib.error.URLError, ConnectionError, TimeoutError) as exc:
                if attempt == self.max_retries:
                    raise CeoJuiceError(0, method, path, f"network error: {exc}") from None
            time.sleep(2**attempt)

        assert text is not None
        if not text.strip():
            return None
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            return text

    def get(self, path: str, **params: Any) -> Any:
        return self._raw_request("GET", path, params=params)

    def post(self, path: str, body: Any = None, **params: Any) -> Any:
        return self._raw_request("POST", path, params=params, body=body)

    def put(self, path: str, body: Any = None, **params: Any) -> Any:
        return self._raw_request("PUT", path, params=params, body=body)

    # -- paging -------------------------------------------------------------

    def paginate(
        self, path: str, page_size: int = 100, max_pages: int | None = None, **params: Any
    ) -> Iterator[dict]:
        """Yield every item across a paged endpoint's pages.

        Paged endpoints answer {page, pageSize, totalCount, totalPages, items}.
        """
        page = 1
        while True:
            payload = self.get(path, page=page, pageSize=page_size, **params)
            if not isinstance(payload, dict) or "items" not in payload:
                # Some routes ignore paging and return a bare list.
                if isinstance(payload, list):
                    yield from payload
                return
            yield from payload["items"]
            total_pages = payload.get("totalPages") or 0
            if page >= total_pages:
                return
            if max_pages and page >= max_pages:
                return
            page += 1

    # -- lookups ------------------------------------------------------------

    def get_list(self, name: str) -> list[dict]:
        """Fetch a lookup list by friendly name, routed around the 403 family."""
        try:
            path = LIST_ROUTES[name]
        except KeyError:
            raise KeyError(
                f"Unknown list {name!r}. Known: {', '.join(sorted(LIST_ROUTES))}"
            ) from None
        return self.get(path)

    # -- reads --------------------------------------------------------------

    def customers(self, **kw: Any) -> Iterator[dict]:
        return self.paginate("/api/Customer", **kw)

    def customer(self, customer_number: str) -> dict:
        return self.get(f"/api/Customer/{_seg(customer_number)}")

    def contacts(self, **kw: Any) -> Iterator[dict]:
        return self.paginate("/api/Contact", **kw)

    def contacts_for_customer(self, customer_number: str) -> Any:
        return self.get(f"/api/Contact/byCustomerNumber/{_seg(customer_number)}")

    def active_equipment(self, **kw: Any) -> Iterator[dict]:
        return self.paginate("/api/Equipment/AllActive", **kw)

    def equipment_by_serial(self, serial: str) -> dict:
        return self.get(f"/api/Equipment/bySerialNumber/{_seg(serial)}")

    def equipment_by_number(self, equipment_number: str) -> dict:
        return self.get(f"/api/Equipment/byEquipmentNumber/{_seg(equipment_number)}")

    def open_service_calls(self, **kw: Any) -> Iterator[dict]:
        return self.paginate("/api/ServiceCall/AllOpen", **kw)

    def service_call(self, call_number: str) -> dict:
        return self.get(f"/api/ServiceCall/ByCallNumber/{_seg(call_number)}")

    def open_sales_orders(self, **kw: Any) -> Iterator[dict]:
        return self.paginate("/api/SalesOrder/AllOpen", **kw)

    def sales_order(self, order_number: str) -> dict:
        return self.get(f"/api/SalesOrder/ByOrderNumber/{_seg(order_number)}")

    def active_contracts(self, **kw: Any) -> Iterator[dict]:
        return self.paginate("/api/Contract/active", **kw)

    def invoice(self, invoice_number: str) -> dict:
        return self.get(f"/api/Invoice/byInvoiceNumber/{_seg(invoice_number)}")

    # -- volumes ------------------------------------------------------------

    def equipment_meters(
        self, equipment_number: str | None = None, serial_number: str | None = None
    ) -> list[dict]:
        """Meter definitions for one machine, including its average volumes.

        Each meter carries avgMonthlyVolume3Mo / 6Mo / 12Mo / Install plus
        targetMonthlyVolume and mfgSuggestedMonthlyVolume, so e-automate
        computes the rolling averages for you -- but only where reading history
        exists to compute them from. Where it does not, they are 0.0, and this
        API exposes no reading-history route to derive them yourself.
        """
        if equipment_number:
            return self.get(
                f"/api/MeterReadings/EquipmentMetersByEqNo/{_seg(equipment_number)}"
            )
        if serial_number:
            return self.get(
                f"/api/MeterReadings/EquipmentMetersBySerial/{_seg(serial_number)}"
            )
        raise ValueError("Pass equipment_number or serial_number.")

    def printreleaf_customers(self) -> list[dict]:
        return self.get("/api/PrintReleaf/customers")

    def page_volumes(
        self, customer_id: int, start: datetime, end: datetime, is_billed: bool | None = None
    ) -> list[dict]:
        """Paper consumption for a customer over a window.

        Returns blackAndWhitePages / colorPages / duplexCount / totalPages.
        The window genuinely filters -- it reports pages produced within the
        range, not a lifetime counter -- which makes this the one route that
        yields real period volume. Periods with no data come back as an empty
        list rather than zeros.
        """
        params = {
            "startDate": start.strftime("%Y-%m-%d"),
            "endDate": end.strftime("%Y-%m-%d"),
        }
        if is_billed is not None:
            params["isBilled"] = str(is_billed).lower()
        return self.get(f"/api/PrintReleaf/customers/{_seg(customer_id)}", **params)

    # -- delta sync ---------------------------------------------------------

    def recent_changes(self, entity: str, since: datetime, **kw: Any) -> Iterator[dict]:
        """Rows of `entity` modified at/after `since`.

        `entity` is one of Customer, Contact, Contract, Equipment, Invoice,
        SalesOrder, ServiceCall.

        The window is capped server-side at 7 days. An older `since` is not an
        error -- it just comes back empty -- so we refuse it loudly instead of
        letting a sync quietly believe nothing changed.
        """
        if since.tzinfo is None:
            since = since.replace(tzinfo=timezone.utc)
        age = datetime.now(timezone.utc) - since
        if age > RECENT_CHANGES_MAX_AGE:
            raise ValueError(
                f"since={since.isoformat()} is {age.days}d old; the API only honors "
                f"{RECENT_CHANGES_MAX_AGE.days} days and returns an empty list "
                "(not an error) beyond that. Poll more often or do a full pull."
            )
        stamp = since.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")
        return self.paginate(f"/api/{entity}/Recentchanges/{stamp}", **kw)

    # -- writes -------------------------------------------------------------

    def add_service_call(
        self,
        description: str,
        call_date: datetime | None = None,
        serial_number: str | None = None,
        equipment_number: str | None = None,
        customer_number: str | None = None,
        reference_call_identifier: str | None = None,
        contact_name: str | None = None,
        contact_phone: str | None = None,
        contact_email: str | None = None,
        notes: str | None = None,
        call_type: str | None = None,
        tracking_key: str | None = None,
    ) -> Any:
        """Create a service call (the ID136 ticketing-sync path).

        One of `serial_number` or `equipment_number` is required -- that is what
        binds the call to a machine. Pass `reference_call_identifier` with the
        ticket ID from your own system so the call can be matched back later.
        """
        if not serial_number and not equipment_number:
            raise ValueError(
                "Pass serial_number or equipment_number; the API requires one."
            )
        stamp = (call_date or datetime.now(timezone.utc)).strftime("%Y-%m-%dT%H:%M:%S")
        body = {
            "description": description,
            "callDate": stamp,
            "serialNumber": serial_number,
            "equipmentNumber": equipment_number,
            "customerNumber": customer_number,
            "referenceCallIdentifier": reference_call_identifier,
            "contactName": contact_name,
            "contactPhone": contact_phone,
            "contactEmail": contact_email,
            "notes": notes,
            "callType": call_type,
            "trackingKey": tracking_key,
        }
        return self.put(
            "/api/ServiceCall/AddCall",
            {k: v for k, v in body.items() if v is not None},
        )

    def add_service_call_note(self, call_number: str, note: str) -> Any:
        return self.post(
            f"/api/ServiceCall/{_seg(call_number)}/AddNote/{_seg(note)}"
        )

    def cancel_service_call(self, call_number: str, **params: Any) -> Any:
        """Cancel a call. Only works before a technician is dispatched."""
        return self.post(f"/api/ServiceCall/{_seg(call_number)}/CancelCall", **params)

    def add_meter_reading(self, body: dict) -> Any:
        return self.put("/api/MeterReadings/AddMeterReading", body)

    def add_sales_order(self, lines: list[dict]) -> Any:
        """Create a sales order through the ID634 import pipeline.

        `lines` is one dict per order line. The server stages them all into
        ZCJ_ImpSOOrderDetails under a shared SourceID, then runs the ID634
        procedure, which derives the header from the first line and writes the
        new SOID back onto the staged rows. So header-level values
        (impCustomerNumber, poNumber, soDate, shipTo*, mailTo*, termsCode ...)
        must be consistent across every line -- ID634 reads them off the batch,
        not off each line independently.
        """
        if not lines:
            raise ValueError("Pass at least one order line.")
        return self.put("/api/SalesOrder/AddOrder", lines)

    def create_customer(self, body: dict) -> Any:
        return self.put("/api/Customer", body)

    def create_contact(self, body: dict) -> Any:
        return self.put("/api/Contact/Create", body)


def _seg(value: Any) -> str:
    """Percent-encode a value used as a URL path segment."""
    return urllib.parse.quote(str(value), safe="")


def _parse_utc(stamp: str) -> datetime:
    """Parse an API timestamp into an aware UTC datetime."""
    text = stamp.replace("Z", "+00:00")
    # .NET emits 7 fractional digits; fromisoformat accepts at most 6.
    if "." in text:
        head, _, tail = text.partition(".")
        digits = ""
        while tail and tail[0].isdigit():
            digits, tail = digits + tail[0], tail[1:]
        text = f"{head}.{digits[:6]}{tail}"
    parsed = datetime.fromisoformat(text)
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)
