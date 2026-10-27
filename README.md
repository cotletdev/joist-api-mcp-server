# Joist API and MCP server, self-hosted

<!-- mcp-name: dev.cotlet/joist -->

A **Joist API** and a **Joist MCP server** you run on your own computer, in Python, on the session of your own Google Chrome. All 20 Joist tools we run in production at [Cotlet](https://cotlet.dev/integrations/joist-api-mcp-server): clients, saved items and tax rates, estimates, invoices from estimates, estimate and invoice email, recorded payments, the monthly CSV export and the Reports page.

Joist has no public API, no webhooks and no official MCP server. Its only link out is QuickBooks Sync on Joist Pro, which copies estimates and invoices one way, once a night, without payments. This repo gives you:

- **MCP server** for Claude Code, Claude Desktop, Cursor, Codex and any MCP client, over stdio or HTTP. [Setup](#mcp-server)
- **REST API** on `http://127.0.0.1:8787/api/v1/joist`, with OpenAPI docs at `/docs`. [Setup](#rest-api)
- **Python**: `call("list_invoices", view="overdue")`, plus 9 ready scripts in [`examples/`](https://github.com/cotletdev/joist-api-mcp-server/blob/main/examples/).

It is for technical people who want to run it themselves, **for noncommercial use only** ([license](#license)). If you want it running 24/7 on a server, kept working when Joist changes its web app, for a team or a business, use the [hosted version at cotlet.dev](https://cotlet.dev/integrations/joist-api-mcp-server).

[![Joist MCP server](https://img.shields.io/badge/Joist%20MCP-20%20tools-6d4aef)](#all-20-tools)
[![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-141318)](#requirements)
[![License: PolyForm Noncommercial 1.0.0](https://img.shields.io/badge/license-PolyForm%20Noncommercial-141318)](https://github.com/cotletdev/joist-api-mcp-server/blob/main/LICENSE)

```bash
uv tool install joist-api-mcp                  # or: pip install joist-api-mcp
joist-mcp connect                                  # reads your Joist session from Chrome
joist-mcp call list_invoices view=overdue
claude mcp add joist -- uvx joist-api-mcp mcp
```

## Contents

- [How it works](#how-it-works)
- [Requirements](#requirements)
- [Install](#install)
- [Connect your Chrome](#connect-your-chrome)
- [MCP server](#mcp-server)
- [REST API](#rest-api)
- [Python and the example scripts](#python-and-the-example-scripts)
- [All 20 tools](#all-20-tools)
- [Configuration](#configuration)
- [Security and your Joist account](#security-and-your-joist-account)
- [Errors](#errors)
- [Self-hosted or hosted](#self-hosted-or-hosted)
- [FAQ](#faq)
- [License](#license)

## How it works

```text
AI agent (MCP) / script (REST, Python) ──▶ joist-mcp on your computer ──your Joist session──▶ joistapp.com
                                                  ▲
                         joist-mcp connect ───────┘ reads it once from your Chrome (DevTools Protocol)
```

1. You sign in to Joist on the web at pro.joistapp.com in your own Chrome, the way you always do.
2. `joist-mcp connect` attaches to that Chrome through the Chrome DevTools Protocol, reads the joistapp.com cookies and your browser's time zone, and saves them to `~/.config/joist-api-mcp/session.json`, readable by your user only. It never sees or stores your password.
3. Every tool call is a request to the endpoints the Joist web app calls (`gateway.prd.joistapp.com`), with the token from the `auth:production` cookie, sent with [curl_cffi](https://github.com/lexiforest/curl_cffi), which copies Chrome's TLS fingerprint. No headless browser runs.

Dates such as "today" and an estimate's last valid day follow the time zone of the Chrome you connected.

## Requirements

- Python 3.11 or newer.
- Google Chrome 144 or newer, signed in at pro.joistapp.com. Any Chrome or Chromium works with a [debugging port](#option-b-a-chrome-with-a-debugging-port).
- macOS, Linux or Windows.
- A Joist account. A Joist company has one user, so the tools act as that user. `get_report` reads the Reports page, which Joist sells on Elite and opens during the 14-day trial. Everything else works on Pro.

## Install

From [PyPI](https://pypi.org/project/joist-api-mcp/):

```bash
uv tool install joist-api-mcp       # or: pipx install joist-api-mcp, or: pip install joist-api-mcp
joist-mcp --version
```

MCP clients can also run it with no install: `uvx joist-api-mcp mcp`.

From source:

```bash
git clone https://github.com/cotletdev/joist-api-mcp-server.git
cd joist-api-mcp-server
python3 -m venv .venv
. .venv/bin/activate              # Windows: .venv\Scripts\activate
pip install -e .
joist-mcp --version
```

With [uv](https://docs.astral.sh/uv/): `uv venv && uv pip install -e .`, then `uv run joist-mcp ...`.

Setting it up with an AI agent (Claude Code, Codex, Cursor)? Open it in this folder and ask it to set up the repo: [`AGENTS.md`](https://github.com/cotletdev/joist-api-mcp-server/blob/main/AGENTS.md) tells it every step, and it asks you only for the steps in Chrome.

To update: `uv tool upgrade joist-api-mcp` (or `pip install -U joist-api-mcp`), from source `git pull && pip install -e .`. We copy every change of the hosted Joist tools into this repo.

## Connect your Chrome

### Option A: your everyday Chrome (recommended)

1. Open `chrome://inspect/#remote-debugging` in Chrome and switch **remote debugging** on. Chrome then accepts DevTools connections from programs on this computer, and asks you before each one.
2. Make sure you are signed in at [pro.joistapp.com](https://pro.joistapp.com).
3. Run:

   ```bash
   joist-mcp connect
   ```

4. Chrome asks whether to allow the connection. Click **Allow**.

```text
Saved 35 Joist cookies to /Users/you/.config/joist-api-mcp/session.json
Signed in to Joist as Sam Rivera
```

You can switch remote debugging off again afterwards. Leave it on if you want the server to pick up a new session by itself after Joist signs you out.

`connect` looks for Chrome's `DevToolsActivePort` file in the default profile folder. For Chrome Beta, Canary or a custom profile folder, pass `--profile-dir "<folder>"`.

### Option B: a Chrome with a debugging port

Chrome does not open a debugging port on your default profile, so start a separate one, sign in to Joist there once, and connect to it:

```bash
# macOS
"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" --remote-debugging-port=9222 --user-data-dir="$HOME/.chrome-joist"
# Linux
google-chrome --remote-debugging-port=9222 --user-data-dir="$HOME/.chrome-joist"
# Windows
"C:\Program Files\Google\Chrome\Application\chrome.exe" --remote-debugging-port=9222 --user-data-dir="%USERPROFILE%\.chrome-joist"

joist-mcp connect --cdp http://127.0.0.1:9222
```

`--cdp` also takes a `ws://` DevTools URL, for example of a Chrome on another machine reached over an SSH tunnel.

### Option C: paste the cookie by hand

For a server with no Chrome: in Chrome open DevTools on pro.joistapp.com, **Application > Cookies > https://pro.joistapp.com**, copy the value of `auth%3Aproduction` (it looks like `1234567%3Aabc...`), then:

```bash
joist-mcp connect --token          # paste it, input is hidden
# or, without a session file:
export JOIST_AUTH_TOKEN=...
```

A pasted token is not refreshed on its own, and dates then use this computer's time zone. Paste a new one when Joist signs you out.

Check the session at any time:

```bash
joist-mcp status
```

## MCP server

The MCP server lists every tool with its input schema, a description written for agents, and hints: read tools are marked read-only, and tools that email a client, record a payment or delete are marked so your client asks before running them.

### Claude Code

```bash
claude mcp add joist -- uvx joist-api-mcp mcp
# read only:
claude mcp add joist -- uvx joist-api-mcp mcp --read-only
```

### Claude Desktop

`~/Library/Application Support/Claude/claude_desktop_config.json` (macOS) or `%APPDATA%\Claude\claude_desktop_config.json` (Windows):

```json
{
  "mcpServers": {
    "joist": {
      "command": "uvx",
      "args": ["joist-api-mcp", "mcp"]
    }
  }
}
```

### Cursor

`~/.cursor/mcp.json`, the same block as Claude Desktop. A ready copy is in [`mcp.json`](https://github.com/cotletdev/joist-api-mcp-server/blob/main/mcp.json).

### Codex

`~/.codex/config.toml`:

```toml
[mcp_servers.joist]
command = "uvx"
args = ["joist-api-mcp", "mcp"]
```

### Over HTTP

`joist-mcp serve` also serves MCP over streamable HTTP at `http://127.0.0.1:8787/mcp`, for clients that take a URL:

```bash
joist-mcp serve
claude mcp add --transport http joist http://127.0.0.1:8787/mcp
```

Then ask your agent things like:

> *Write an estimate for Maple Street Dental: 120 sq ft of drywall repair at $4.50 and two coats of paint for $380, 7.25% tax, valid 30 days.*
>
> *Which approved estimates have no invoice yet? Generate the invoices and show me before you send any.*
>
> *Record the $390.93 check from Maple Street Dental on invoice 1042, dated yesterday.*
>
> *List overdue invoices, oldest first, and draft a short reminder for each.*
>
> *What did I take in last month, and how much sales tax did I collect?*

## REST API

```bash
joist-mcp serve                    # http://127.0.0.1:8787, MCP at /mcp, docs at /docs
```

Each tool has its own route under `/api/v1/joist`, the same paths as the hosted API at cotlet.dev, so code written against one works with the other. Path parts and the query string are arguments, and a JSON body adds the rest.

```bash
curl 'http://127.0.0.1:8787/api/v1/joist/clients?search=dental'
curl 'http://127.0.0.1:8787/api/v1/joist/invoices?view=overdue'
curl -X POST http://127.0.0.1:8787/api/v1/joist/clients/56285802/estimates \
  -H 'Content-Type: application/json' \
  -d '{"line_items": [{"name": "Drywall repair (per sq ft)", "quantity": 120, "rate": 4.5}], "tax_rate": 7.25}'
```

Any tool by name, body as its arguments:

```bash
curl -X POST http://127.0.0.1:8787/api/v1/joist/tools/get_report -d '{"report": "revenue", "from": "2026-10-01", "to": "2026-10-31"}'
```

- `GET /api/v1/joist/tools`: every tool with its route, input schema and an example answer.
- `GET /docs`: interactive OpenAPI docs, `GET /openapi.json` the schema, for n8n, Postman or a generated client.
- Answers are JSON. Lists return `next_cursor`; pass it back as `cursor` for the next page.

The server listens on `127.0.0.1` only. To reach it from another device of yours, set a token, and every request then needs `Authorization: Bearer <token>`:

```bash
JOIST_MCP_TOKEN=$(openssl rand -hex 24) joist-mcp serve --host 0.0.0.0
```

## Python and the example scripts

Straight from Python, no server needed:

```python
from joist_api_mcp import call
from joist_api_mcp.scripting import paginate, write_rows

overdue = list(paginate("list_invoices", {"view": "overdue"}, "invoices"))
write_rows(overdue, "overdue.csv")
client = call("list_clients", search="Maple Street")["clients"][0]
call("create_estimate", client_id=client["client_id"], line_items=[{"name": "Deck stain", "rate": 650}])
```

Or one tool from the shell: `joist-mcp call list_estimates approval=pending`, or with a JSON object.

Ready scripts in [`examples/`](https://github.com/cotletdev/joist-api-mcp-server/blob/main/examples/). Each prints JSON, takes `--out file.csv` or `--out file.json` where it makes sense, and `--help`. The ones that write show what they would do first:

| Script | What it does |
|---|---|
| [`export_clients.py`](https://github.com/cotletdev/joist-api-mcp-server/blob/main/examples/export_clients.py) | Clients to CSV or JSON: name, email, phone, address, notes, last payment. `--search`. |
| [`estimate_from_job.py`](https://github.com/cotletdev/joist-api-mcp-server/blob/main/examples/estimate_from_job.py) | An estimate from a job description: finds the client by name or adds it, lines as `name:quantity:rate`, saved items matched by name. `--dry-run`. |
| [`list_estimates.py`](https://github.com/cotletdev/joist-api-mcp-server/blob/main/examples/list_estimates.py) | Estimates by approval: pending, approved, declined or all. |
| [`invoice_approved_estimates.py`](https://github.com/cotletdev/joist-api-mcp-server/blob/main/examples/invoice_approved_estimates.py) | Approved estimates without an invoice. `--convert` makes the invoices, `--send` emails them. |
| [`record_payment.py`](https://github.com/cotletdev/joist-api-mcp-server/blob/main/examples/record_payment.py) | A check, cash, card or bank transfer payment on an invoice found by its number. |
| [`overdue_invoices.py`](https://github.com/cotletdev/joist-api-mcp-server/blob/main/examples/overdue_invoices.py) | Overdue invoices with balance due, oldest first. |
| [`remind_overdue.py`](https://github.com/cotletdev/joist-api-mcp-server/blob/main/examples/remind_overdue.py) | Lists overdue invoices; `--send` emails each one again with your message. `--days`. |
| [`export_month.py`](https://github.com/cotletdev/joist-api-mcp-server/blob/main/examples/export_month.py) | Joist's monthly invoice or estimate CSV, the file for your accountant. |
| [`monthly_report.py`](https://github.com/cotletdev/joist-api-mcp-server/blob/main/examples/monthly_report.py) | Revenue, invoices, estimates or sales tax for one month, with the total. |

```bash
python examples/overdue_invoices.py --out overdue.csv
python examples/export_month.py --month 2026-10 --out invoices-2026-10.csv
```

On a schedule, cron on your own computer works while it is on: `0 8 * * 1 cd ~/joist-api-mcp-server && .venv/bin/python examples/overdue_invoices.py --out ~/overdue.csv`.

## All 20 tools

Ids come from the list tools: `client_id` from `list_clients`, `estimate_id` from `list_estimates`, `invoice_id` from `list_invoices`. `joist-mcp tools` prints this list, `joist-mcp tools --json` adds the input schemas.

### Clients

| Tool | Access | REST route | What it does |
|---|---|---|---|
| `list_clients` | read | `GET /clients` | Clients in your account with name, email, phone and address. |
| `get_client` | read | `GET /clients/{client_id}` | One client card: every email and phone, billing and service address, notes and tags. |
| `add_client` | write | `POST /clients` | New client in your Clients list, ready for estimates and invoices. |

### Items and tax rates

| Tool | Access | REST route | What it does |
|---|---|---|---|
| `list_items` | read | `GET /items` | Saved items from your Items list with rate and description, plus your tax rates. |
| `add_item` | write | `POST /items` | Save a service or material to your Items list. |

### Estimates

| Tool | Access | REST route | What it does |
|---|---|---|---|
| `list_estimates` | read | `GET /estimates` | Estimates with number, client, total, expiry, status, approval, and whether it was emailed or signed. |
| `get_estimate` | read | `GET /estimates/{estimate_id}` | Full estimate: client, line items, tax, discount, deposit, expiry, approval and signature. |
| `create_estimate` | write | `POST /clients/{client_id}/estimates` | New saved estimate with line items, tax, discount, deposit and expiry. Nothing is sent to the client. |
| `update_estimate` | write | `PATCH /estimates/{estimate_id}` | Change an estimate's lines, tax, discount, deposit, expiry, notes or PO number. Nothing is sent. |
| `delete_estimate` | write | `DELETE /estimates/{estimate_id}` | Delete an estimate for good. |
| `send_estimate` | write | `POST /estimates/{estimate_id}/send` | Email the estimate to the client from Joist with its link and PDF. |
| `convert_estimate_to_invoice` | write | `POST /estimates/{estimate_id}/convert` | Generate an invoice with everything from the estimate. Nothing is sent to the client. |

### Invoices and payments

| Tool | Access | REST route | What it does |
|---|---|---|---|
| `list_invoices` | read | `GET /invoices` | Invoices with client, total, amount paid, balance due, due date and overdue. Active, paid or all. |
| `get_invoice` | read | `GET /invoices/{invoice_id}` | Full invoice: client, line items, tax, discount, deposit, due date, balance and every payment. |
| `create_invoice` | write | `POST /clients/{client_id}/invoices` | New saved invoice for a client without an estimate. Nothing is sent to the client. |
| `delete_invoice` | write | `DELETE /invoices/{invoice_id}` | Delete an invoice that has no payments, for good. |
| `send_invoice` | write | `POST /invoices/{invoice_id}/send` | Email the invoice to the client from Joist with its link and PDF. |
| `record_payment` | write | `POST /invoices/{invoice_id}/payments` | Record a cash, check, credit card or bank transfer payment on an invoice; paid in full moves to Paid. |

### Export and reports

| Tool | Access | REST route | What it does |
|---|---|---|---|
| `export_documents` | read | `GET /documents/export` | Joist's monthly CSV of estimates or invoices: number, client, subtotal, tax, total, dates, payments. |
| `get_report` | read | `GET /reports/{report}` | A Joist report for a date range: revenue, invoices, estimates or sales tax, with the period total. |

Nothing reaches your client until `send_estimate` or `send_invoice`. Creating, converting and changing a document saves it in Joist only. `record_payment` writes down money you already received and charges no card.

Not in this version: editing an invoice after it is made, editing or deleting clients and items, Joist Payments (online card payments), change orders, work orders, jobs and attachments.

Never built, on purpose: your Joist sign-in, email and password, and your Joist plan and billing. Every request passes a guard that refuses changes to sign-in, password and account paths.

## Configuration

| Variable | Default | What it does |
|---|---|---|
| `JOIST_MCP_HOME` | `~/.config/joist-api-mcp` | Folder of `session.json`. |
| `JOIST_AUTH_TOKEN` | | The `auth%3Aproduction` cookie value, instead of `joist-mcp connect`. |
| `JOIST_PROXY` | | Proxy for every request to Joist, e.g. `http://user:pass@host:port`. |
| `JOIST_MCP_READ_ONLY` | | `1` hides and refuses every tool that changes Joist (same as `--read-only`). |
| `JOIST_MCP_TOKEN` | | Bearer token required by `serve`; needed to listen beyond `127.0.0.1`. |
| `JOIST_MCP_HOST`, `JOIST_MCP_PORT` | `127.0.0.1`, `8787` | Address of `serve`. |

## Security and your Joist account

- **Your password never reaches this code.** Only cookies are read, and only those of joistapp.com.
- **The session file is yours.** `session.json` is created with mode 0600. Anyone who has it can act as you in Joist, so keep it out of git and shared folders.
- **Local by default.** `serve` binds to `127.0.0.1` and refuses another address without `JOIST_MCP_TOKEN`.
- **joistapp.com only.** Requests and redirects outside joistapp.com are refused.
- **Read-only mode.** `--read-only` or `JOIST_MCP_READ_ONLY=1` exposes the 9 read tools only.
- **Emails reach real clients.** `send_estimate` and `send_invoice` email your client from Joist under your company name. MCP clients ask before running them. A script does not, so run it without `--send` first.
- **Deletes are for good.** Joist has no trash for a deleted estimate or invoice.

## Errors

The REST API answers `{"error": "<code>", "message": "..."}`. The MCP server returns the same code and message as a tool error.

| Status | Code | What to do |
|---|---|---|
| 401 | `auth_required`, `auth_expired` | No session, or Joist signed you out. Sign in at pro.joistapp.com in Chrome and run `joist-mcp connect`. |
| 403 | `scope_denied` | The server runs read-only. |
| 403 | `target_blocked` | Joist refused the request, or says the account is suspended. Open pro.joistapp.com in Chrome to see why. |
| 422 | `invalid_input` | An argument is missing or wrong, or the id is not in your account; the message says which. |
| 429 | `rate_limited` | Joist is limiting the account. Wait a few minutes. |
| 502 | `target_error` | Joist answered with an error (a report on a plan without Reports, too), or changed its web app. `git pull` for the latest tools, or [open an issue](https://github.com/cotletdev/joist-api-mcp-server/issues). |

## Self-hosted or hosted

| | This repo | [Cotlet, hosted](https://cotlet.dev/integrations/joist-api-mcp-server) |
|---|---|---|
| Tools | the same 20 | the same 20 |
| Runs | on your computer, while it is on | in the cloud, 24/7 |
| Joist session | your Chrome, saved in a local file | your own Cloud Browser in the EU, profile encrypted with AES-256-GCM |
| When Joist changes its web app | `git pull` once we have fixed it | fixed for you, every tool tested daily |
| Approvals | your MCP client asks per call | estimate and invoice email and recorded payments wait for your OK, switchable per tool |
| Works with | MCP clients on your machine, local scripts | Claude.ai and ChatGPT connectors, n8n, Make, Zapier, any HTTP client |
| Who may use it | you, for noncommercial use | teams, businesses, agencies |
| Price | free | free 7-day trial with 2,000 credits, no card; then one-time packs from $29 for 5,000 credits |

On the hosted version a successful call uses 10 credits, failed calls are free, and the Cloud Browser uses 50 credits a day while it has an app enabled for agents. [Full pricing](https://cotlet.dev/pricing).

## FAQ

**Does Joist have an official API?**
No. Joist publishes no API, developer docs or webhooks (checked 26 Oct 2026). QuickBooks Sync on Joist Pro copies issued estimates and invoices to QuickBooks Online once a night, one way and without payments, and the web app exports a monthly CSV without line items. Details: [cotlet.dev/integrations/joist-api-mcp-server](https://cotlet.dev/integrations/joist-api-mcp-server).

**Is there a Joist MCP server for Claude, ChatGPT or Cursor?**
Yes, this one runs on your machine: `joist-mcp mcp` for Claude Code, Claude Desktop, Cursor and Codex. ChatGPT and Claude.ai connectors need a public HTTPS URL, which the [hosted Joist MCP server](https://cotlet.dev/integrations/joist-api-mcp-server) gives you.

**Does my client get an email when a tool makes an estimate or invoice?**
No. `create_estimate`, `create_invoice`, `update_estimate` and `convert_estimate_to_invoice` save the document in Joist. Your client gets mail only from `send_estimate` or `send_invoice`, with the subject and message from your Joist settings unless you pass your own.

**Can I export my Joist invoices with line items?**
`get_invoice` and `get_estimate` return every line, tax, discount, deposit and payment of one document. `export_documents` gives Joist's own monthly CSV, which has totals but no lines.

**Which Joist plan do I need?**
The tools do what your plan lets you do in Joist. Pro covers estimates, invoices, clients and payments. Reports (`get_report`) need Elite or the 14-day trial. Joist updates report numbers once a day, so today's payments show up tomorrow.

**Why does it need my Chrome?**
To read your Joist session without your password. Chrome is used once per sign-in, not for each call.

**What happens when Joist signs me out?**
Calls fail with `auth_expired`. With Chrome remote debugging on, the server reads the new session on the next call (click Allow when Chrome asks). Otherwise run `joist-mcp connect` again.

**Can it run on a VPS or in Docker?**
Technically yes, with `JOIST_AUTH_TOKEN` or a `session.json` copied from your computer. Joist then sees your session from a datacenter IP, and in our experience it suspends accounts it does not trust fast. For an always-on setup the hosted version keeps your session in your own Cloud Browser on a fixed IP.

**Will my Joist account get banned?**
Requests carry Chrome's fingerprint and go out one at a time, as you would click. Nobody can promise a platform never acts. Keep to your normal use.

**Can I use it for my contracting business or for my clients?**
No. The license allows noncommercial use only, and running your own business counts as business use. For a business, a team or client work, use [Cotlet](https://cotlet.dev) or write to [contact@cotlet.dev](mailto:contact@cotlet.dev).

**Can I use the code for anything I like?**
No. The source is public, but the license allows noncommercial use only: no business use.

**A tool broke or I need another one.**
[Open an issue](https://github.com/cotletdev/joist-api-mcp-server/issues) with the tool name and the error message.

## License

[PolyForm Noncommercial License 1.0.0](https://github.com/cotletdev/joist-api-mcp-server/blob/main/LICENSE). In short:

- **Allowed:** noncommercial use: you, for your own personal purposes with your own Joist account, or a charity, school, public research or government body. Changing the code, and sharing it under the same license.
- **Not allowed:** any commercial use, your own business included; client work; selling or offering it, or a service built on it.

---

<p>
  <a href="https://cotlet.dev">
    <picture>
      <source media="(prefers-color-scheme: dark)" srcset="assets/logo-white.svg">
      <img src="https://raw.githubusercontent.com/cotletdev/joist-api-mcp-server/main/assets/logo.svg" alt="Cotlet" width="120">
    </picture>
  </a>
</p>

Maintained by [Cotlet](https://cotlet.dev) ([@cotletdev](https://x.com/cotletdev)). Joist is a trademark of its owner. This project is unofficial and not affiliated with, endorsed or sponsored by Joist.
