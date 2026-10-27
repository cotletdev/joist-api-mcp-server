"""Example answers shared by the tools that return a whole estimate or invoice (`_documents.shape`)."""

from __future__ import annotations

from typing import Any

_LINE: dict[str, Any] = {
    "line_id": "175424909",
    "item_id": "105580562",
    "name": "Drywall repair (per sq ft)",
    "description": "Patch, tape, mud and sand",
    "quantity": 120.0,
    "rate": 4.5,
    "amount": 540.0,
    "taxes": [{"tax_id": "1371277", "name": "NC Sales Tax", "rate": 7.25}],
}

_COMMON: dict[str, Any] = {
    "number": "1",
    "email_status": "sent",
    "client": {
        "client_id": "56285802",
        "name": "Maple Street Dental",
        "email": "office@example.com",
        "phone": "9195550142",
        "address": "410 Fayetteville St, Raleigh, NC 27601",
    },
    "document_date": "2026-10-26",
    "po_number": "PO-2231",
    "line_items": [_LINE],
    "subtotal": 540.0,
    "discount": 54.0,
    "tax": 35.24,
    "total": 521.24,
    "currency": "USD",
    "deposit": {"type": "percent", "value": 25.0, "due": 130.31},
    "notes": "Work during weekend hours to keep the office open.",
    "signed_on": None,
    "public_url": "https://client.joistapp.com/estimates/85d8ef8769202da9ea434763",
}

ESTIMATE: dict[str, Any] = {
    "document_id": "52709714",
    "type": "estimate",
    "status": "issued",
    **_COMMON,
    "approval_status": "pending",
    "expires_on": "2026-11-26",
}

INVOICE: dict[str, Any] = {
    "document_id": "71977284",
    "type": "invoice",
    "status": "partial",
    **_COMMON,
    "public_url": "https://client.joistapp.com/invoices/3fd8c10876363166640bd020",
    "payment_terms_days": 0,
    "due_date": "2026-10-26",
    "amount_paid": 130.31,
    "amount_refunded": 0.0,
    "balance_due": 390.93,
    "overdue": False,
    "from_estimate_id": "52709714",
    "payments": [
        {
            "payment_id": "0ff33ac4-01f9-4955-9fa8-aba4a78602aa",
            "type": "payment",
            "amount": 130.31,
            "method": "cash",
            "paid_on": "2026-10-26",
            "status": "succeeded",
            "source": "manual",
        }
    ],
}
