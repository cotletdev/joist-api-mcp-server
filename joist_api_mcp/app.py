"""Everything the server knows about Joist outside `joist/`: names, domains and the session cookie.

The rest of the package reads these values and never names the app itself.
"""

from __future__ import annotations

NAME = "Joist"
SLUG = "joist"
# The command and the prefix of every environment variable (JOIST_AUTH_TOKEN, JOIST_MCP_TOKEN ...).
CLI = "joist-mcp"
ENV = "JOIST"
# Requests may reach only these hosts and their subdomains. Their cookies are read from Chrome.
DOMAINS = ("joistapp.com",)
# Present only while signed in: `auth:production` (URL-encoded in the name), value `<user_id>:<token>`.
# The first is the cookie a pasted token sets.
SESSION_COOKIES = ("auth%3Aproduction",)
COOKIE_DOMAIN = ".joistapp.com"
LOGIN_URL = "https://pro.joistapp.com/login"
# A final URL with one of these means the app signed the session out.
LOGGED_OUT_MARKERS = ("/login", "/signup")
# An answer with one of these asks you to sign in again before a sensitive action. Joist has none.
RELOGIN_MARKERS: tuple[str, ...] = ()
# Paths of your Joist account that tools may read but never write. Common password, email and sign-in
# paths are refused for every app (core/account_guard.py); Joist adds none.
ACCOUNT_PATHS: tuple[str, ...] = ()
# REST routes live under this path, the same as on cotlet.dev.
API_PREFIX = "/api/v1/joist"
# Prepended to the MCP server's instructions: where an agent starts.
AGENT_START = "Start with list_clients or list_invoices: their ids are what the other tools take."
