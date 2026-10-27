"""Add client: a new client card (`POST /v7/{user}/contacts`), as the panel's New Client form saves it."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from joist_api_mcp.core.errors import ErrorCode, ToolError
from joist_api_mcp.core.tools import tool
from joist_api_mcp.joist.tools._api import call
from joist_api_mcp.joist.tools._clients import client_row

if TYPE_CHECKING:
    from joist_api_mcp.core.context import ToolContext

ADDRESS_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "street": {"type": "string", "maxLength": 255},
        "suite": {"type": "string", "maxLength": 100},
        "city": {"type": "string", "maxLength": 100},
        "state": {"type": "string", "maxLength": 100},
        "zip": {"type": "string", "maxLength": 20},
    },
    "additionalProperties": False,
}

INPUT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "name": {"type": "string", "minLength": 1, "maxLength": 255, "description": "Client or company name."},
        "email": {"type": "string", "format": "email", "description": "Where documents are emailed."},
        "phone": {"type": "string", "maxLength": 30},
        "address": {**ADDRESS_SCHEMA, "description": "Billing address."},
        "notes": {"type": "string", "maxLength": 5000, "description": "Notes on the client card."},
    },
    "required": ["name"],
    "additionalProperties": False,
}

EXAMPLE_RESPONSE: dict[str, Any] = {
    "client_id": "56290114",
    "name": "Priya Nair",
    "email": "priya@example.com",
    "phone": "9195550178",
    "address": "22 Oak Ave, Cary, NC 27511",
    "notes": "",
    "tags": [],
    "last_payment_on": None,
}


@tool(
    name="add_client",
    title="Add client",
    access="write",
    description="New client in your Clients list, ready for estimates and invoices.",
    details=(
        "Creates a client card in Joist with name and optional email, phone, billing address and notes. It "
        "reaches no one. Joist does not refuse a duplicate name, so check list_clients first."
    ),
    input_schema=INPUT_SCHEMA,
    route="POST /clients",
    example_response=EXAMPLE_RESPONSE,
)
async def add_client(ctx: ToolContext, args: dict[str, Any]) -> Any:
    address = args.get("address") or {}
    contact: dict[str, Any] = {
        "name": args["name"].strip(),
        "notes": args.get("notes") or "",
        "deleted": False,
        "emails": [{"type": "home", "value": args["email"]}] if args.get("email") else [],
        "phone_numbers": [{"type": "mobile", "value": args["phone"]}] if args.get("phone") else [],
        "address": {k: address.get(k) or "" for k in ("street", "suite", "city", "state", "zip")},
        "tag_list": [],
        "source_list": [],
        "contact_preferences": {"allow_phone": True, "allow_email": True, "allow_sms": True},
    }
    body = await call(ctx, "POST", 7, "contacts", body={"contact": contact})
    created = (body or {}).get("contact") or {}
    if not created.get("id"):
        raise ToolError("Joist did not save the client.", ErrorCode.TARGET_ERROR)
    return client_row(ctx, created)
