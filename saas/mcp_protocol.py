"""A small MCP server (Streamable HTTP transport, JSON responses, no sessions) for Flask apps.

Lets Claude (claude.ai custom connectors, Claude Desktop, Claude Code) call the app's tools.
The same file lives in saas/mcp_protocol.py: keep the two copies identical.

A tool is a dict: {"name", "description", "input_schema", "fn", optional "title", "read_only", "destructive"}.
fn(arguments: dict) returns anything JSON-serialisable; raising ToolError (or any exception) reports an error to Claude.

Optional prompts (ready-made requests the user picks in Claude): {"name", "title", "description",
"arguments": [{"name", "description", "required"}], "render"(arguments: dict) -> str}.
"""
import json

SUPPORTED_VERSIONS = ("2025-11-25", "2025-06-18", "2025-03-26", "2024-11-05")


class ToolError(Exception):
    """A problem to show to the user (bad input, Instagram refused, ...)."""


def _error(msg_id, code, message):
    return {"jsonrpc": "2.0", "id": msg_id, "error": {"code": code, "message": message}}


def _result(msg_id, result):
    return {"jsonrpc": "2.0", "id": msg_id, "result": result}


def tool_list(tools):
    out = []
    for t in tools:
        entry = {"name": t["name"], "description": t["description"], "inputSchema": t["input_schema"]}
        if t.get("title"):
            entry["title"] = t["title"]
        hints = {}
        if t.get("read_only"):
            hints["readOnlyHint"] = True
        if t.get("destructive"):
            hints["destructiveHint"] = True
        if hints:
            entry["annotations"] = {"title": t.get("title", t["name"]), **hints}
        out.append(entry)
    return out


def call_tool(tools, params):
    by_name = {t["name"]: t for t in tools}
    tool = by_name.get(params.get("name"))
    if not tool:
        raise LookupError(f"Unknown tool: {params.get('name')}")
    try:
        value = tool["fn"](params.get("arguments") or {})
    except ToolError as e:
        return {"content": [{"type": "text", "text": str(e)}], "isError": True}
    except Exception as e:  # report, don't crash the connection
        return {"content": [{"type": "text", "text": f"Something went wrong: {e}"}], "isError": True}
    text = value if isinstance(value, str) else json.dumps(value, ensure_ascii=False, indent=1)
    result = {"content": [{"type": "text", "text": text}], "isError": False}
    if isinstance(value, dict):
        result["structuredContent"] = value
    return result


def prompt_list(prompts):
    return [{k: p[k] for k in ("name", "title", "description", "arguments") if p.get(k) is not None} for p in prompts]


def get_prompt(prompts, params):
    prompt = next((p for p in prompts if p["name"] == params.get("name")), None)
    if not prompt:
        raise LookupError(f"Unknown prompt: {params.get('name')}")
    args = {k: str(v) for k, v in (params.get("arguments") or {}).items()}
    missing = [a["name"] for a in prompt.get("arguments") or [] if a.get("required") and not args.get(a["name"])]
    if missing:
        raise LookupError(f"Missing argument: {', '.join(missing)}")
    return {"description": prompt.get("description", ""),
            "messages": [{"role": "user", "content": {"type": "text", "text": prompt["render"](args)}}]}


def handle_message(msg, tools, server_name, instructions="", prompts=None):
    """One JSON-RPC message in, one response dict out (None for notifications)."""
    if not isinstance(msg, dict) or msg.get("jsonrpc") != "2.0" or "method" not in msg:
        return _error(msg.get("id") if isinstance(msg, dict) else None, -32600, "Invalid request")
    msg_id, method, params = msg.get("id"), msg["method"], msg.get("params") or {}
    if "id" not in msg:
        return None  # notification (e.g. notifications/initialized): nothing to answer
    if method == "initialize":
        asked = params.get("protocolVersion")
        return _result(msg_id, {
            "protocolVersion": asked if asked in SUPPORTED_VERSIONS else SUPPORTED_VERSIONS[0],
            "capabilities": {"tools": {"listChanged": False}, **({"prompts": {"listChanged": False}} if prompts else {})},
            "serverInfo": {"name": server_name, "version": "1.0.0"},
            "instructions": instructions,
        })
    if method == "ping":
        return _result(msg_id, {})
    if method == "tools/list":
        return _result(msg_id, {"tools": tool_list(tools)})
    if method == "tools/call":
        try:
            return _result(msg_id, call_tool(tools, params))
        except LookupError as e:
            return _error(msg_id, -32602, str(e))
    if method == "prompts/list":
        return _result(msg_id, {"prompts": prompt_list(prompts or [])})
    if method == "prompts/get":
        try:
            return _result(msg_id, get_prompt(prompts or [], params))
        except LookupError as e:
            return _error(msg_id, -32602, str(e))
    if method == "resources/list":
        return _result(msg_id, {"resources": []})
    return _error(msg_id, -32601, f"Method not found: {method}")


def handle_http(body_bytes, tools, server_name, instructions="", prompts=None):
    """Returns (status, json_body_or_None) for a POST to the MCP endpoint."""
    try:
        payload = json.loads(body_bytes or b"null")
    except ValueError:
        return 400, _error(None, -32700, "Parse error")
    if isinstance(payload, list):  # batches (older protocol versions)
        replies = [r for r in (handle_message(m, tools, server_name, instructions, prompts) for m in payload) if r]
        return (200, replies) if replies else (202, None)
    reply = handle_message(payload, tools, server_name, instructions, prompts)
    return (200, reply) if reply else (202, None)
