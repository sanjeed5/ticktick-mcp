# TickTick MCP Server – Codebase Explained

## 1. What is the Model Context Protocol (MCP)?
The **Model Context Protocol (MCP)** is an open-standard, JSON-RPC-based protocol introduced by Anthropic in late-2024.  It defines a common client↔server contract that allows language-model clients (e.g. Claude Desktop, Cursor, Copilot Studio) to discover and invoke **tools**, **resources** and **prompts** exposed by external systems.  In practice, an *MCP server* is a tiny process that:

* Announces an identifier (e.g. `"ticktick"`).
* Registers one or more `@mcp.tool()` functions.
* Listens on a transport (`stdio` for local CLI integrations or SSE/HTTP for remote services).

A matching *MCP client* (inside your editor/agent) serialises user requests → JSON-RPC, calls the server, then deserialises the reply back to the model.

This repository provides an **MCP server that connects Claude (or any MCP client) to the TickTick task-management REST API**.

---

## 2. Repository layout
```
ticktick-mcp/
├── README.md            – public docs & usage examples
├── requirements.txt     – minimal runtime deps (`mcp[cli]`, `requests`, `python-dotenv`)
├── setup.py             – packaging metadata, console-script entrypoints
├── test_server.py       – interactive smoke-test for local creds
├── ticktick_mcp/        – python package
│   ├── __init__.py
│   ├── authenticate.py  – friendly CLI wizard around `TickTickAuth`
│   ├── cli.py           – command dispatcher (`run` / `auth`)
│   └── src/
│       ├── __init__.py
│       ├── auth.py          – **TickTickAuth**: full OAuth2 flow
│       ├── server.py        – **FastMCP** server + tool definitions
│       └── ticktick_client.py – thin wrapper around TickTick REST API
└── ticktick-openapi.md  – upstream OpenAPI spec (for reference)
```

A high-level call-graph:
```
           +-----------+            +-----------------+
 `cli.py`  |  uv run   |  ->  runs  |  server.main()   |
           +-----------+            +--------+--------+
                                           |
                                           v
                            +-----------------------------+
                            |  FastMCP (from mcp.server)  |
                            +-----------------------------+
                                    |  registers
                                    v
                         many async @mcp.tool() functions
                                    |
                                    v
                          +---------------------------+
                          | TickTickClient (REST API) |
                          +---------------------------+
```

---

## 3. Important modules & their responsibilities

### 3.1 `ticktick_mcp/src/auth.py`
* Pure-Python implementation of TickTick's OAuth2 flow.
* Starts a temporary **HTTP callback server** on `http://localhost:8000/callback` and opens the browser.
* Exchanges the received code for access/refresh tokens via Basic-Auth.
* Persists credentials into a **`.env`** file (git-ignored) so subsequent runs don't prompt again.

### 3.2 `ticktick_mcp/src/ticktick_client.py`
* Lightweight REST client using `requests`.
* Handles token refresh transparently when a 401 is returned.
* Performs simple CRUD helpers around `/project` and `/task` endpoints.

### 3.3 `ticktick_mcp/src/server.py`
* Creates a **FastMCP** instance (`mcp.server.fastmcp.FastMCP`).
* On first tool invocation calls `initialize_client()` → `TickTickClient()`.
* Exposes 10+ tools (`get_projects`, `create_task`, `delete_project`, …) that wrap the REST client and pretty-print JSON → human-oriented text.

### 3.4 `ticktick_mcp/authenticate.py`
* User-friendly wrapper for the OAuth flow.  Provides nice ASCII UI, input validation, and re-uses existing `.env` credentials when possible.

### 3.5 `ticktick_mcp/cli.py`
* Provides two console scripts (declared in `setup.py`):
  * `ticktick-mcp run` – start the MCP server (default)
  * `ticktick-mcp auth` – trigger authentication wizard
* When `run` is executed without existing tokens it interactively offers to launch the auth flow.

---

## 4. Runtime behaviour
1. **Authentication** (one-off)
   ```bash
   uv run -m ticktick_mcp.cli auth
   ```
   • prompts for Client-ID/Secret → opens browser → writes tokens to `.env`.

2. **Start server**
   ```bash
   uv run -m ticktick_mcp.cli run --transport stdio
   ```
   • FastMCP reads/writes on STDIO so editors like Claude Desktop can spawn it as a subprocess.

3. **Tool invocation**
   • The client sends a JSON-RPC request `{ "method": "ticktick/create_task", …}`.
   • Corresponding async function inside `server.py` is awaited.
   • Result string is returned back to the model.

---

## 5. Security review
| Area | Observation | Risk | Recommendation |
|------|-------------|------|----------------|
| **Token storage** | Access / refresh tokens are written in plaintext to `.env` | Low (local dev) but anyone with disk access can read. | Ensure `.env` is `chmod 600`; avoid committing it. |
| **Callback server** | `socketserver.TCPServer(("", port))` binds **all interfaces** (0.0.0.0). | On a multi-user or network-exposed machine another process could hijack the callback & steal the OAuth *code*. | Change to `("127.0.0.1", port)` and/or verify `state` parameter on return. |
| **State verification** | A random `state` param is generated but **never checked** after redirect. | CSRF risk; attacker could inject their own code. | Persist generated `state` and confirm it inside `OAuthCallbackHandler`. |
| **Transport encryption** | All API calls use `https://` endpoints; `requests` default verifies SSL. | — | Consider `requests.Session(verify=True)` explicitness. |
| **Dependency pinning** | `requirements.txt` uses upper bounds (`<3.0.0`) but no exact versions. | Minor | Consider hash-pinned `requirements-lock.txt` for supply-chain safety. |
| **FastMCP stdio** | No obvious injection vector; tool args are typed & validated. | — | Keep validating parameters (e.g., `priority` range checks already in place). |

**Overall**: The project is *safe to run locally* provided you trust the TickTick API.  Harden the OAuth callback binding & state-check if you intend to deploy on a shared or remote host.

---

## 6. Extending the server
* Add new TickTick endpoints by writing wrappers in `ticktick_client.py` and registering new `@mcp.tool()` functions.
* To expose the server over the network instead of stdio, use `FastMCP(…, transport='sse', host='0.0.0.0', port=PORT)`.

---

## 7. Reference links
* MCP spec – https://modelcontextprotocol.io/
* Anthropic announcement – https://www.anthropic.com/news/model-context-protocol
* Wikipedia overview – https://en.wikipedia.org/wiki/Model_Context_Protocol

---

*Generated automatically on 2025-06-28 by o3-assistant.*