"""Estimates and invoices: detail reads, the answer shape, list rows and the nested-attribute bodies of writes.

A document is a Rails record with nested attributes (`../MAP.md`, "How every call looks"): lines in
`{kind}_items_attributes`, each with `{kind}_item_taxes_attributes`, the deposit in `payment_requests_attributes`.
A row with `id` updates, without `id` is added, `{"id": …, "_destroy": true}` removes it. Removed lines stay in
the answer with `deleted` set, so every reader drops them.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from joist_api_mcp.core.errors import ErrorCode, ToolError
from joist_api_mcp.joist.tools._api import (
    ID_SCHEMA,
    address_text,
    call,
    cents,
    due_date,
    end_of_day,
    local_date,
    money,
    now_iso,
    number,
    parse_day,
    today,
)

if TYPE_CHECKING:
    from joist_api_mcp.core.context import ToolContext

UNPAID = ("issued", "partial")
DUE_TTL_S = 7 * 24 * 3600

# Shared input pieces of create_estimate, update_estimate and create_invoice.
LINE_ITEMS_SCHEMA: dict[str, Any] = {
    "type": "array",
    "minItems": 1,
    "maxItems": 100,
    "items": {
        "type": "object",
        "properties": {
            "name": {"type": "string", "minLength": 1, "maxLength": 255},
            "description": {"type": "string", "maxLength": 5000},
            "quantity": {"type": "number", "exclusiveMinimum": 0, "default": 1},
            "rate": {"type": "number", "minimum": 0, "description": "Price per unit."},
            "item_id": {**ID_SCHEMA, "description": "Saved item from list_items, kept as the line's source."},
        },
        "required": ["name", "rate"],
        "additionalProperties": False,
    },
}
AMOUNT_TERM_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "type": {"type": "string", "enum": ["percent", "amount"]},
        "value": {"type": "number", "minimum": 0},
    },
    "required": ["type", "value"],
    "additionalProperties": False,
}
TERMS_PROPERTIES: dict[str, Any] = {
    "tax_rate": {
        "type": "number",
        "minimum": 0,
        "maximum": 100,
        "description": "Tax percent on every line, e.g. 7.25. Uses your tax rate with that percent, or adds one.",
    },
    "tax_id": {**ID_SCHEMA, "description": "A saved tax rate from list_items (taxes) instead of tax_rate."},
    "discount": {**AMOUNT_TERM_SCHEMA, "description": "Discount on the subtotal: percent or amount."},
    "deposit": {**AMOUNT_TERM_SCHEMA, "description": "Requested deposit, shown as Deposit Due: percent or amount."},
    "notes": {"type": "string", "maxLength": 5000, "description": "Notes shown on the document."},
    "po_number": {"type": "string", "maxLength": 100, "description": "PO number."},
}


def kind_of(value: Any) -> str:
    kind = str(value or "")
    if kind not in ("estimate", "invoice"):
        raise ToolError("type must be estimate or invoice.", ErrorCode.INVALID_INPUT)
    return kind


async def fetch(ctx: ToolContext, kind: str, doc_id: str) -> dict[str, Any]:
    body = await call(ctx, "GET", 6, f"{kind}s/{doc_id}/", what=kind.capitalize())
    found = (body or {}).get(kind)
    if not isinstance(found, dict) or found.get("deleted"):
        raise ToolError(f"{kind.capitalize()} not found in Joist.", ErrorCode.INVALID_INPUT)
    return found


async def payments(ctx: ToolContext, invoice_id: str) -> list[dict[str, Any]]:
    body = await call(ctx, "GET", 7, f"invoices/{invoice_id}/transactions", what="Invoice")
    rows = ((body or {}).get("invoice") or {}).get("transactions") or []
    return [
        {
            "payment_id": str(t.get("id")),
            "type": t.get("type"),
            "amount": cents(t.get("amount_cents")),
            "method": t.get("method"),
            "paid_on": local_date(ctx, t.get("paid_at")),
            "status": t.get("status"),
            "source": t.get("source"),
        }
        for t in rows
        if isinstance(t, dict)
    ]


def lines(doc: dict[str, Any], kind: str) -> list[dict[str, Any]]:
    rows = [r for r in doc.get(f"{kind}_items") or [] if isinstance(r, dict) and not r.get("deleted")]
    return sorted(rows, key=lambda r: int(r.get("index") or 0))


def _deposit(doc: dict[str, Any], total: float) -> dict[str, Any] | None:
    for request in doc.get("payment_requests") or []:
        if request.get("request_type") != "deposit":
            continue
        if request.get("percent") not in (None, ""):
            value = money(request.get("percent"))
            return {"type": "percent", "value": value, "due": round(total * value / 100, 2)}
        value = money(request.get("amount"))
        return {"type": "amount", "value": value, "due": value}
    return None


def shape(ctx: ToolContext, doc: dict[str, Any], kind: str, paid: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    """One estimate or invoice as the tools answer it."""
    rows = lines(doc, kind)
    items = [
        {
            "line_id": str(r.get("id")),
            "item_id": str(r["item_id"]) if r.get("item_id") else None,
            "name": r.get("name"),
            "description": r.get("notes") or "",
            "quantity": number(r.get("quantity")),
            "rate": number(r.get("price")),
            "amount": round(number(r.get("quantity")) * number(r.get("price")), 2),
            "taxes": [
                {"tax_id": str(t.get("tax_id")), "name": t.get("name"), "rate": number(t.get("amount"))}
                for t in r.get(f"{kind}_item_taxes") or []
                if not t.get("deleted")
            ],
        }
        for r in rows
    ]
    subtotal = round(sum(i["amount"] for i in items), 2)
    if doc.get("discount_percent") not in (None, ""):
        discount = round(subtotal * money(doc.get("discount_percent")) / 100, 2)
    else:
        discount = money(doc.get("discount_amount"))
    total = money(doc.get("total"))
    found: dict[str, Any] = {
        "document_id": str(doc.get("id")),
        "type": kind,
        "number": doc.get("doc_id"),
        "status": doc.get("status"),
        "email_status": doc.get("email_status"),
        "client": {
            "client_id": str(doc["contact_id"]) if doc.get("contact_id") else None,
            "name": doc.get("name"),
            "email": doc.get("email") or None,
            "phone": doc.get("phone1") or None,
            "address": address_text(doc.get("billing_address")),
        },
        "document_date": doc.get("document_date"),
        "po_number": doc.get("purchase_order_number") or None,
        "line_items": items,
        "subtotal": subtotal,
        "discount": discount,
        "tax": round(total - subtotal + discount - money(doc.get("applied_markup")), 2),
        "total": total,
        "currency": doc.get("currency_code"),
        "deposit": _deposit(doc, total),
        "notes": doc.get("notes") or "",
        "signed_on": local_date(ctx, doc.get("contact_signed_on")),
        "public_url": doc.get("public_url"),
    }
    if kind == "estimate":
        found["approval_status"] = doc.get("approval_status")
        found["expires_on"] = local_date(ctx, doc.get("expires_at"))
        return found
    due = due_date(doc)
    outstanding = money(doc.get("amount_outstanding"))
    found.update(
        {
            "payment_terms_days": int(doc.get("days_to_pay") or 0),
            "due_date": due,
            "amount_paid": money(doc.get("amount_paid")),
            "amount_refunded": money(doc.get("amount_refunded")),
            "balance_due": outstanding,
            "overdue": is_overdue(ctx, doc.get("status"), due, outstanding),
            "from_estimate_id": str(doc["src_resource_id"]) if doc.get("src_resource_type") == "Estimate" else None,
            "payments": paid or [],
        }
    )
    return found


def is_overdue(ctx: ToolContext, status: Any, due: str | None, outstanding: float) -> bool:
    return status in UNPAID and outstanding > 0 and due is not None and due < today(ctx).isoformat()


async def read(ctx: ToolContext, kind: str, doc_id: str) -> dict[str, Any]:
    """Detail with the payments (invoices), shaped."""
    doc = await fetch(ctx, kind, doc_id)
    paid = await payments(ctx, doc_id) if kind == "invoice" else None
    return shape(ctx, doc, kind, paid)


# Lists


def list_row(ctx: ToolContext, row: dict[str, Any], kind: str) -> dict[str, Any]:
    owner = row.get("homeowner") or {}
    found: dict[str, Any] = {
        f"{kind}_id": str(row.get("id")),
        "number": row.get("document_number"),
        "client": owner.get("name"),
        "document_date": row.get("document_date"),
        "total": cents(row.get("total_cents")),
        "currency": row.get("currency_code"),
        "status": row.get("status"),
        "email_status": row.get("email_status"),
        "signed": bool(owner.get("document_signed")),
        "po_number": row.get("purchase_order_number") or None,
    }
    if kind == "estimate":
        found["approval_status"] = row.get("approval_status")
        found["expires_on"] = local_date(ctx, row.get("expires_at"))
    return found


async def due_facts(ctx: ToolContext, row: dict[str, Any]) -> tuple[str | None, float, float]:
    """(due date, paid, balance) of a list row: paid and draft rows need no read, the rest one detail read,
    kept in the cache until the invoice changes (updated_at in the key)."""
    total = cents(row.get("total_cents"))
    status = row.get("status")
    if status == "paid":
        return None, total, 0.0
    if status not in UNPAID:
        return None, 0.0, total
    key = f"due:{row.get('id')}:{row.get('updated_at')}"
    cached = await ctx.cache_get(key)
    if cached:
        due, paid, balance = cached.split("|")
        return due or None, float(paid), float(balance)
    doc = await fetch(ctx, "invoice", str(row.get("id")))
    facts = (due_date(doc), money(doc.get("amount_paid")), money(doc.get("amount_outstanding")))
    await ctx.cache_set(key, f"{facts[0] or ''}|{facts[1]}|{facts[2]}", DUE_TTL_S)
    return facts


async def invoice_rows(ctx: ToolContext, rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    facts = [await due_facts(ctx, r) for r in rows]
    found = []
    for row, (due, paid, balance) in zip(rows, facts, strict=True):
        item = list_row(ctx, row, "invoice")
        item.update(
            {
                "due_date": due,
                "amount_paid": paid,
                "balance_due": balance,
                "overdue": is_overdue(ctx, row.get("status"), due, balance),
            }
        )
        found.append(item)
    return found


async def document_list(
    ctx: ToolContext, kind: str, args: dict[str, Any], filter_name: str, size: int
) -> tuple[list[dict[str, Any]], str | None]:
    params = {
        "query": args.get("search"),
        "next": args.get("cursor"),
        "limit": size,
        "filter_name": filter_name,
        "contact_id": args.get("client_id"),
    }
    body = await call(ctx, "GET", 8, f"{kind}s", params=params)
    rows = [r for r in (body or {}).get("data") or [] if isinstance(r, dict)]
    cursor = (((body or {}).get("paging") or {}).get("cursors") or {}).get("next")
    return rows, str(cursor) if cursor else None


# Writes


async def client_fields(ctx: ToolContext, client_id: str) -> dict[str, Any]:
    """What the panel copies from the client into a new document."""
    body = await call(ctx, "GET", 7, f"contacts/{client_id}", what="Client")
    contact = (body or {}).get("contact") or {}
    if not contact or contact.get("deleted"):
        raise ToolError("Client not found in Joist.", ErrorCode.INVALID_INPUT)
    emails = [e.get("value") for e in contact.get("emails") or [] if e.get("value")]
    phones = [p.get("value") for p in contact.get("phone_numbers") or [] if p.get("value")]
    address = contact.get("address") or {}
    return {
        "contact_id": int(client_id),
        "name": contact.get("name"),
        "email": emails[0] if emails else "",
        "phone1": phones[0] if phones else "",
        "phone2": phones[1] if len(phones) > 1 else "",
        "client_notes": contact.get("notes") or "",
        "billing_address": {
            "address1": address.get("street") or "",
            "address2": address.get("suite") or "",
            "city": address.get("city") or "",
            "state": address.get("state") or "",
            "zip": address.get("zip") or "",
        },
    }


async def resolve_tax(ctx: ToolContext, args: dict[str, Any]) -> dict[str, Any] | None:
    """The tax row for the lines: tax_id as given, or the saved rate with tax_rate's percent, or a new one."""
    if args.get("tax_id") is None and args.get("tax_rate") is None:
        return None
    body = await call(ctx, "GET", 6, "taxes", params={"fetch_all": "true"})
    taxes = [t for t in (body or {}).get("taxes") or [] if not t.get("deleted")]
    if args.get("tax_id") is not None:
        found = next((t for t in taxes if str(t.get("id")) == str(args["tax_id"])), None)
        if found is None:
            raise ToolError("No tax rate with that tax_id (list_items gives them).", ErrorCode.INVALID_INPUT)
        return found
    rate = round(float(args["tax_rate"]), 3)
    found = next((t for t in taxes if round(number(t.get("amount")), 3) == rate), None)
    if found is not None:
        return found
    label = f"{rate:g}"
    created = await call(ctx, "POST", 6, "taxes", body={"tax": {"name": f"Tax {label}%", "amount": f"{rate:.3f}"}})
    return (created or {}).get("tax") or {}


def tax_rows(kind: str, tax: dict[str, Any]) -> dict[str, Any]:
    return {
        f"{kind}_item_taxes_attributes": [
            {"tax_id": tax.get("id"), "name": tax.get("name"), "amount": str(tax.get("amount"))}
        ]
    }


def new_lines(kind: str, items: list[dict[str, Any]], tax: dict[str, Any] | None, start: int = 0) -> list[Any]:
    rows = []
    for index, line in enumerate(items, start=start):
        row: dict[str, Any] = {
            "name": line["name"],
            "notes": line.get("description") or "",
            "price": f"{float(line['rate']):g}",
            "quantity": f"{float(line.get('quantity') or 1):g}",
            "index": index,
        }
        if line.get("item_id"):
            row["item_id"] = int(line["item_id"])
        if tax:
            row.update(tax_rows(kind, tax))
        rows.append(row)
    return rows


def money_terms(args: dict[str, Any], existing: dict[str, Any] | None = None) -> dict[str, Any]:
    """Discount and deposit fields; on an update the old deposit row is removed first."""
    body: dict[str, Any] = {}
    if discount := args.get("discount"):
        percent = discount["type"] == "percent"
        if percent and discount["value"] > 100:
            raise ToolError("A percent discount is at most 100.", ErrorCode.INVALID_INPUT)
        body["discount_percent"] = discount["value"] if percent else None
        body["discount_amount"] = None if percent else f"{discount['value']:.2f}"
    if "deposit" in args:
        requests: list[dict[str, Any]] = [
            {"id": r.get("id"), "_destroy": True}
            for r in (existing or {}).get("payment_requests") or []
            if r.get("request_type") == "deposit"
        ]
        if deposit := args.get("deposit"):
            percent = deposit["type"] == "percent"
            if percent and deposit["value"] > 100:
                raise ToolError("A percent deposit is at most 100.", ErrorCode.INVALID_INPUT)
            requests.append(
                {
                    "request_type": "deposit",
                    "label": "Deposit",
                    "index": 0,
                    "percent": deposit["value"] if percent else None,
                    "amount": None if percent else deposit["value"],
                }
            )
        body["payment_requests_attributes"] = requests
    if "notes" in args:
        body["notes"] = args.get("notes") or ""
    if "po_number" in args:
        body["purchase_order_number"] = args.get("po_number") or ""
    return body


async def create(ctx: ToolContext, kind: str, args: dict[str, Any], extra: dict[str, Any]) -> dict[str, Any]:
    """A new draft estimate or invoice for a client, as the panel saves it; nothing is sent."""
    client = await client_fields(ctx, str(args["client_id"]))
    tax = await resolve_tax(ctx, args)
    numbered = await call(ctx, "GET", 6, f"{kind}s/next_doc_id")
    day = parse_day(args["document_date"], "document_date") if args.get("document_date") else today(ctx)
    fields: dict[str, Any] = {
        **client,
        "doc_id": str((numbered or {}).get("doc_id") or ""),
        "document_date": day.isoformat(),
        "issued_at": now_iso(ctx),
        "service_address": {},
        f"{kind}_items_attributes": new_lines(kind, args["line_items"], tax),
        **money_terms(args),
        **extra,
    }
    body = await call(ctx, "POST", 6, f"{kind}s", body={kind: fields})
    created = (body or {}).get(kind) or {}
    if not created.get("id"):
        raise ToolError(f"Joist did not save the {kind}.", ErrorCode.TARGET_ERROR)
    return shape(ctx, created, kind, [] if kind == "invoice" else None)


def expiry(ctx: ToolContext, value: Any) -> str:
    day = parse_day(value, "expires_on")
    if day < today(ctx):
        raise ToolError("expires_on cannot be in the past.", ErrorCode.INVALID_INPUT)
    return end_of_day(ctx, day)
