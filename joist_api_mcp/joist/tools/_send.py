"""Email an estimate or invoice from Joist (`POST /v8/{user}/{kind}s/{id}/deliveries`, 204), as the Send dialog does.

The dialog's defaults: subject "Your Estimate #1 from <company>", message from user_settings
(`default_estimate_email_message`, `default_invoice_email_message`), recipient the email on the document.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from joist_api_mcp.core.errors import ErrorCode, ToolError
from joist_api_mcp.joist.tools._api import ID_SCHEMA, call
from joist_api_mcp.joist.tools._documents import fetch

if TYPE_CHECKING:
    from joist_api_mcp.core.context import ToolContext


def input_schema(kind: str) -> dict[str, Any]:
    return {
        "type": "object",
        "properties": {
            f"{kind}_id": {**ID_SCHEMA, "description": f"From list_{kind}s."},
            "to": {
                "type": "array",
                "minItems": 1,
                "maxItems": 10,
                "items": {"type": "string", "format": "email"},
                "description": "Recipients. Default: the client email on the document.",
            },
            "subject": {"type": "string", "maxLength": 200, "description": "Default: Joist's subject."},
            "message": {"type": "string", "maxLength": 5000, "description": f"Default: your {kind} email message."},
        },
        "required": [f"{kind}_id"],
        "additionalProperties": False,
    }


async def send(ctx: ToolContext, kind: str, args: dict[str, Any]) -> dict[str, Any]:
    doc_id = str(args[f"{kind}_id"])
    doc = await fetch(ctx, kind, doc_id)
    to = list(args.get("to") or ([doc["email"]] if doc.get("email") else []))
    if not to:
        raise ToolError("The client has no email on this document; pass to.", ErrorCode.INVALID_INPUT)
    subject, message = args.get("subject"), args.get("message")
    if not subject:
        company = ((await call(ctx, "GET", 6, "companies")) or {}).get("company") or {}
        subject = f"Your {kind.capitalize()} #{doc.get('doc_id')} from {company.get('name') or 'us'}"
    if message is None:
        settings = ((await call(ctx, "GET", 6, "user_settings")) or {}).get("user_setting") or {}
        message = settings.get(f"default_{kind}_email_message") or ""
    body: dict[str, Any] = {"data": {"channel": "email", "emails": {"to": to}, "subject": subject, "message": message}}
    if kind == "invoice":
        body["use_v2_email_template"] = True
    await call(ctx, "POST", 8, f"{kind}s/{doc_id}/deliveries", body=body, what=kind.capitalize())
    after = await fetch(ctx, kind, doc_id)
    return {
        f"{kind}_id": doc_id,
        "number": after.get("doc_id"),
        "emailed_to": to,
        "subject": subject,
        "status": after.get("status"),
        "email_status": after.get("email_status"),
        "public_url": after.get("public_url"),
    }
