# AGENTS.md

You are an AI agent in a clone of this repo. It is a self-hosted Joist API and MCP server: 20 tools that work in the user's own Joist account, through the session of their own Google Chrome. Your usual job is one of three: set it up for the user, use its tools for them, or change its code. Human docs: `README.md`.

## Before you start

- The license allows noncommercial use only (PolyForm Noncommercial 1.0.0, `LICENSE`). Running a contracting business counts as business use. If the user is setting this up for their business, a team or clients, say so and point to the hosted version at https://cotlet.dev/integrations/joist-api-mcp-server. Do not continue the setup for that use.
- Every tool acts as the user in Joist. Tools with access `write` save, change or delete estimates, invoices, clients and items, record payments, and `send_estimate` and `send_invoice` email the user's clients.

## Set it up for the user

Do the steps yourself. Ask the user only for what needs their hands in Chrome.

1. Check Python: `python3 --version` must be 3.11 or newer.
2. Install in the repo root:

   ```bash
   python3 -m venv .venv && .venv/bin/pip install -e .
   .venv/bin/joist-mcp --version
   ```

   On Windows the path is `.venv\Scripts\joist-mcp`. With uv: `uv venv && uv pip install -e .`.
3. Ask the user to do two things in Chrome. You cannot open `chrome://` pages for them.
   - Open `chrome://inspect/#remote-debugging` and switch remote debugging on.
   - Be signed in at https://pro.joistapp.com.
4. Run `.venv/bin/joist-mcp connect`. Tell the user to click **Allow** when Chrome asks about the connection. Success prints `Signed in to Joist as <name>`.
5. Check: `.venv/bin/joist-mcp status`, then `.venv/bin/joist-mcp call list_clients`.
6. Add the MCP server to the user's client. Use the absolute path of `.venv/bin/joist-mcp`:
   - Claude Code: `claude mcp add joist -- <abs path>/.venv/bin/joist-mcp mcp`
   - Claude Desktop, Cursor, Codex: the config blocks in `README.md`, section "MCP server".
   - Add `--read-only` after `mcp` if the user only wants to read.
   The client loads new MCP servers on its next start. Tell the user.

If step 4 fails:

| Message | What to do |
|---|---|
| `Chrome remote debugging is off` | Step 3 is not done, or Chrome is Beta, Canary or a custom profile: pass `--profile-dir "<profile folder>"`. |
| `Could not connect to Chrome` | The user did not click Allow, or Chrome is closed. Run `connect` again. |
| `This Chrome is not signed in to Joist` | The user signs in at pro.joistapp.com in that Chrome, then run `connect` again. |
| No Chrome on this machine (a server) | The user copies the `auth%3Aproduction` cookie from Chrome DevTools (Application, Cookies, https://pro.joistapp.com) and runs `joist-mcp connect --token` themselves. Never ask them to paste the token into the chat. |

## Use the tools

- With the MCP server added, call its tools. Without it: `.venv/bin/joist-mcp call <tool> key=value ...`, or one JSON object as the argument.
- `.venv/bin/joist-mcp tools` lists every tool with access and route. `tools --json` adds the input schemas.
- Start with `list_clients`, `list_estimates` or `list_invoices`. Their `client_id`, `estimate_id` and `invoice_id` values are what the other tools take.
- Lists return `next_cursor`. Pass it back as `cursor` for the next page.
- Creating or converting a document emails no one. Before `send_estimate`, `send_invoice` or `record_payment`, show the user the document, the amount and the recipient, and get their OK.
- For a script or a cron job, use `joist_api_mcp.scripting` (`call`, `paginate`, `write_rows`) and the scripts in `examples/` as models.
- For a REST API (n8n, other languages): `.venv/bin/joist-mcp serve`, routes under `http://127.0.0.1:8787/api/v1/joist`, docs at `/docs`.

Errors come as `<code>: <message>`. `auth_expired` means Joist signed the session out: the user signs in again in Chrome and you run `connect`. `target_blocked` can mean Joist suspended the account: the user opens pro.joistapp.com to see why. More codes: `README.md`, section "Errors".

## Keep secrets out

- `~/.config/joist-api-mcp/session.json` and `JOIST_AUTH_TOKEN` give full access to the user's Joist account. Never print, log, commit or copy their content.
- `serve` listens on 127.0.0.1. Never start it on another address without `JOIST_MCP_TOKEN`.

## Change the code

| Path | What | Edit? |
|---|---|---|
| `joist_api_mcp/joist/` | the Joist tools, one file per tool in `tools/`, shared request code in `tools/_api.py` and `client.py` | Yes for a local fix, but the next `git pull` brings our version of these files. Report the bug at https://github.com/cotletdev/joist-api-mcp-server/issues |
| `joist_api_mcp/app.py` | app name, domains, session cookie, REST prefix | Rarely |
| `joist_api_mcp/core/` | `@tool` declaration, errors, the HTTP client with the session (`context.py`), the browser profile tools read (`profile.py`) | Yes |
| `joist_api_mcp/session.py` | reading cookies and the time zone from Chrome over CDP, the session file | Yes |
| `joist_api_mcp/runner.py`, `api.py`, `mcp_server.py`, `mcp_context.py`, `cli.py` | tool registry, REST API, MCP server, its prompts and resources, command line | Yes |
| `examples/` | scripts for common jobs | Yes |

A new tool is a new file in `joist_api_mcp/joist/tools/` with a `@tool(...)` declaration (name, access, input schema, `route`). The registry finds it, and the REST API, the MCP server and the CLI show it without other changes.

There is no test suite. After a change, run `.venv/bin/joist-mcp tools` and one read tool against the user's account.
