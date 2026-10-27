"""Shared pieces of every Joist tool (recorded 26.10.2026).

Calls go to `https://gateway.prd.joistapp.com/api/v{6,7,8}/{user_id}/...` with the token header of
`client.headers`. The version is per resource: v6 documents and taxes, v7 clients, items and payments, v8
document lists, deliveries and reports. Money is a decimal string on documents and cents in lists and payments.
"""

from __future__ import annotations

from datetime import UTC, date, datetime, time, timedelta
from typing import TYPE_CHECKING, Any

from joist_api_mcp.core.errors import ErrorCode, ToolError
from joist_api_mcp.joist.client import API, headers, user_id

if TYPE_CHECKING:
    from joist_api_mcp.core.context import ToolContext

DOC_TYPES = ("estimate", "invoice")
ID_SCHEMA: dict[str, Any] = {"type": "string", "pattern": "^[0-9]+$"}


def _message(body: Any) -> str:
    """Joist's own words from an error answer (`errors` list or `error.message`), without technical detail."""
    if isinstance(body, dict):
        errors = body.get("errors")
        if isinstance(errors, list) and errors:
            return "; ".join(str(e) for e in errors[:3])
        if isinstance(errors, dict) and errors:
            return "; ".join(f"{k} {', '.join(map(str, v)) if isinstance(v, list) else v}" for k, v in errors.items())
        error = body.get("error")
        if isinstance(error, dict) and (error.get("message") or error.get("detail")):
            return str(error.get("message") or error.get("detail"))
    return ""


async def call(
    ctx: ToolContext,
    method: str,
    version: int | None,
    path: str,
    *,
    params: dict[str, Any] | None = None,
    body: Any = None,
    what: str = "Record",
) -> Any:
    """One gateway call under the signed-in user's id; JSON back (None for 204), app errors as ToolError."""
    prefix = f"{API}/v{version}" if version else API
    url = f"{prefix}/{user_id(ctx)}/{path}"
    clean = {k: v for k, v in (params or {}).items() if v not in (None, "")}
    response = await ctx.call(method, url, params=clean or None, json=body, headers=headers(ctx))
    if response.status == 404:
        raise ToolError(f"{what} not found in Joist.", ErrorCode.INVALID_INPUT)
    if response.status >= 400:
        try:
            said = _message(response.json())
        except ToolError:
            said = ""
        code = ErrorCode.INVALID_INPUT if response.status in (400, 422) else ErrorCode.TARGET_ERROR
        raise ToolError(f"Joist refused it: {said}" if said else "Joist answered with an error.", code)
    if response.status == 204 or not response.text.strip():
        return None
    if path.endswith(".csv"):
        return response.text
    return response.json()


def money(value: Any) -> float:
    try:
        return round(float(value or 0), 2)
    except (TypeError, ValueError):
        return 0.0


def cents(value: Any) -> float:
    try:
        return round(int(float(value or 0)) / 100, 2)
    except (TypeError, ValueError):
        return 0.0


def number(value: Any) -> float:
    """Quantity or price as Joist stores it ("120.0", "4.5")."""
    try:
        return float(value or 0)
    except (TypeError, ValueError):
        return 0.0


def today(ctx: ToolContext) -> date:
    return datetime.now(ctx.user_zone).date()


def now_iso(ctx: ToolContext) -> str:
    """The panel's issued_at: local time with the offset."""
    return datetime.now(ctx.user_zone).replace(microsecond=0).isoformat()


def end_of_day(ctx: ToolContext, day: date) -> str:
    """The panel's expires_at: the last second of that day in the user's zone, in UTC."""
    moment = datetime.combine(day, time(23, 59, 59), tzinfo=ctx.user_zone)
    return moment.astimezone(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def local_date(ctx: ToolContext, value: Any) -> str | None:
    """An ISO timestamp from Joist as a date in the user's zone."""
    text = str(value or "")
    if not text:
        return None
    try:
        return datetime.fromisoformat(text.replace("Z", "+00:00")).astimezone(ctx.user_zone).date().isoformat()
    except ValueError:
        return text[:10] or None


def parse_day(value: Any, field: str) -> date:
    try:
        return date.fromisoformat(str(value))
    except ValueError as exc:
        raise ToolError(f"{field} must be a date as YYYY-MM-DD.", ErrorCode.INVALID_INPUT) from exc


def due_date(document: dict[str, Any]) -> str | None:
    """Invoice date plus its payment terms (days_to_pay), as the panel shows Due."""
    start = str(document.get("document_date") or "")[:10]
    if not start:
        return None
    try:
        return (date.fromisoformat(start) + timedelta(days=int(document.get("days_to_pay") or 0))).isoformat()
    except ValueError:
        return None


def address_text(address: dict[str, Any] | None) -> str:
    """One line from a Joist address (street/suite or address1/address2, city, state, zip)."""
    a = address or {}
    street = " ".join(str(p) for p in (a.get("street") or a.get("address1"), a.get("suite") or a.get("address2")) if p)
    region = " ".join(str(p) for p in (a.get("state"), a.get("zip")) if p)
    return ", ".join(p for p in (street, str(a.get("city") or ""), region) if p)
