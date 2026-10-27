"""Get client: one client card (`/v7/{user}/contacts/{id}`)."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from joist_api_mcp.core.errors import ErrorCode, ToolError
from joist_api_mcp.core.tools import tool
from joist_api_mcp.joist.tools._api import ID_SCHEMA, call
from joist_api_mcp.joist.tools._clients import client_row

if TYPE_CHECKING:
    from joist_api_mcp.core.context import ToolContext

INPUT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {"client_id": {**ID_SCHEMA, "description": "From list_clients."}},
    "required": ["client_id"],
    "additionalProperties": False,
}

EXAMPLE_RESPONSE: dict[str, Any] = {
    "client_id": "56285802",
    "name": "Maple Street Dental",
    "email": "office@example.com",
    "phone": "9195550142",
    "address": "410 Fayetteville St, Raleigh, NC 27601",
    "notes": "Front office remodel",
    "tags": [],
    "last_payment_on": "2026-10-26",
    "emails": ["office@example.com"],
    "phones": [{"type": "mobile", "number": "9195550142"}],
    "billing_address": {"street": "410 Fayetteville St", "suite": "", "city": "Raleigh", "state": "NC", "zip": "27601"},
    "service_address": None,
    "created_on": "2026-10-26",
}


def _address(value: dict[str, Any] | None) -> dict[str, Any] | None:
    found = {k: (value or {}).get(k) or "" for k in ("street", "suite", "city", "state", "zip")}
    return found if any(found.values()) else None


@tool(
    name="get_client",
    title="Get client",
    access="read",
    description="One client card: every email and phone, billing and service address, notes and tags.",
    details="Returns one client with all emails and phones, the billing and service address, notes and tags.",
    input_schema=INPUT_SCHEMA,
    route="GET /clients/{client_id}",
    example_response=EXAMPLE_RESPONSE,
)
async def get_client(ctx: ToolContext, args: dict[str, Any]) -> Any:
    body = await call(ctx, "GET", 7, f"contacts/{args['client_id']}", what="Client")
    contact = (body or {}).get("contact") or {}
    if not contact or contact.get("deleted"):
        raise ToolError("Client not found in Joist.", ErrorCode.INVALID_INPUT)
    return {
        **client_row(ctx, contact),
        "emails": [e.get("value") for e in contact.get("emails") or [] if e.get("value")],
        "phones": [
            {"type": p.get("type"), "number": p.get("value")}
            for p in contact.get("phone_numbers") or []
            if p.get("value")
        ],
        "billing_address": _address(contact.get("address")),
        "service_address": _address(contact.get("service_address")),
        "created_on": str(contact.get("created_at") or "")[:10] or None,
    }
