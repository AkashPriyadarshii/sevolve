"""Stdio JSON-RPC 2.0 MCP Server for sevolve brain.

Connects to Claude Code, Cursor, OpenClaw, Codex, Windsurf, and Antigravity.
"""

from __future__ import annotations

import json
import sys
from typing import Any, Dict, List, Optional
from .db import BrainDB
from .graph import BrainGraph
from .hebbian import HebbianEngine


TOOLS = [
    {
        "name": "search_brain",
        "description": "Fast hybrid FTS5 + graph search across AST code symbols, rules, and past bug fixes.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "The search query, symbol name, or error text."},
                "limit": {"type": "integer", "description": "Maximum number of results to return (default: 10)."},
                "node_types": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Optional filter by node type: symbol, rule, trace, failure, fix, task.",
                },
            },
            "required": ["query"],
        },
    },
    {
        "name": "get_context_map",
        "description": "Get a token-budgeted Personalized PageRank code map of functions, classes, and dependencies.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "files": {"type": "array", "items": {"type": "string"}, "description": "Active file paths to seed PageRank."},
                "token_budget": {"type": "integer", "description": "Maximum token budget (default: 1500 tokens)."},
            },
        },
    },
    {
        "name": "query_codegraph",
        "description": "Inspect symbol details, incoming/outgoing calls, class inheritance, and co-modified files.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "node_id": {"type": "string", "description": "The node ID (e.g. sym:func:engine/trace.py:Trace.add)."},
                "direction": {"type": "string", "enum": ["in", "out", "both"], "description": "Edge traversal direction."},
            },
            "required": ["node_id"],
        },
    },
    {
        "name": "record_trace",
        "description": "Record an agent session trace, updating Hebbian co-modification and failure edges.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "session_id": {"type": "string", "description": "Unique session identifier."},
                "prompt": {"type": "string", "description": "The user task or goal."},
                "output": {"type": "string", "description": "Final agent output or status."},
                "ok": {"type": "boolean", "description": "Whether execution succeeded without errors."},
                "changed_files": {"type": "array", "items": {"type": "string"}, "description": "Files edited in this session."},
                "error_message": {"type": "string", "description": "Optional failure error message."},
            },
            "required": ["session_id", "prompt", "ok"],
        },
    },
    {
        "name": "suggest_fixes",
        "description": "Look up known past fixes and rules for a given error or stack trace.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "error_text": {"type": "string", "description": "The error message or stack trace."},
            },
            "required": ["error_text"],
        },
    },
]


class MCPServer:
    def __init__(self, db_path: str = ".sevolve/brain.db"):
        self.db = BrainDB(db_path)
        self.graph = BrainGraph(self.db)
        self.hebbian = HebbianEngine(self.graph)

    def handle_request(self, req: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        req_id = req.get("id")
        method = req.get("method")
        params = req.get("params", {})

        if method == "initialize":
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {"tools": {}},
                    "serverInfo": {"name": "sevolve-brain", "version": "0.2.0"},
                },
            }

        elif method == "notifications/initialized":
            return None

        elif method == "tools/list":
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {"tools": TOOLS},
            }

        elif method == "tools/call":
            tool_name = params.get("name")
            args = params.get("arguments", {})
            try:
                content = self.call_tool(tool_name, args)
                return {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "result": {"content": [{"type": "text", "text": content}]},
                }
            except Exception as e:
                return {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "error": {"code": -32603, "message": str(e)},
                }

        elif method == "ping":
            return {"jsonrpc": "2.0", "id": req_id, "result": {}}

        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "error": {"code": -32601, "message": f"Method {method} not found"},
        }

    def call_tool(self, name: str, args: Dict[str, Any]) -> str:
        if name == "search_brain":
            query = args["query"]
            limit = args.get("limit", 10)
            types = args.get("node_types")
            results = self.graph.query_fts(query, limit=limit, node_types=types)
            if not results:
                return f"No brain matches found for '{query}'."
            out = [f"Found {len(results)} matches:\n"]
            for r in results:
                out.append(f"- [{r['node_type'].upper()}] `{r['id']}`")
                if r.get("signature"):
                    out.append(f"  Signature: `{r['signature']}`")
                if r.get("content"):
                    out.append(f"  Doc: {r['content'][:120]}")
            return "\n".join(out)

        elif name == "get_context_map":
            files = args.get("files")
            budget = args.get("token_budget", 1500)
            return self.graph.get_context_map(seed_files=files, token_budget=budget)

        elif name == "query_codegraph":
            node_id = args["node_id"]
            direction = args.get("direction", "both")
            node = self.graph.get_node(node_id)
            if not node:
                return f"Node `{node_id}` not found in brain."
            neighbors = self.graph.get_neighbors(node_id, direction=direction)
            out = [
                f"# Node: {node['name']} ({node['node_type']})",
                f"ID: `{node['id']}`",
                f"Signature: `{node.get('signature', '')}`",
                f"File: `{node.get('file_path', '')}`",
                f"\n## Connected Relationships ({len(neighbors)}):",
            ]
            for n in neighbors:
                out.append(f"- [{n['direction']}: {n['edge_type']}] `{n['id']}` (w={n['weight']:.2f})")
            return "\n".join(out)

        elif name == "record_trace":
            trace_id = self.hebbian.record_trace(
                session_id=args["session_id"],
                prompt=args["prompt"],
                events=[],
                output=args.get("output", ""),
                ok=args["ok"],
                changed_files=args.get("changed_files", []),
                error_message=args.get("error_message"),
            )
            return f"Trace recorded and brain Hebbian weights updated: `{trace_id}`"

        elif name == "suggest_fixes":
            err = args["error_text"]
            results = self.graph.query_fts(err, limit=5, node_types=["failure", "fix", "rule"])
            if not results:
                return "No past fixes or rules matched this error."
            out = [f"Found {len(results)} relevant failure/fix/rule patterns:\n"]
            for r in results:
                out.append(f"### [{r['node_type'].upper()}] {r['name']}")
                out.append(r.get("content", ""))
            return "\n".join(out)

        raise ValueError(f"Unknown tool: {name}")

    def run_stdio(self) -> None:
        """Run stdio loop reading JSON-RPC lines."""
        for line in sys.stdin:
            line = line.strip()
            if not line:
                continue
            try:
                req = json.loads(line)
                resp = self.handle_request(req)
                if resp is not None:
                    sys.stdout.write(json.dumps(resp) + "\n")
                    sys.stdout.flush()
            except Exception as e:
                err_resp = {
                    "jsonrpc": "2.0",
                    "id": None,
                    "error": {"code": -32700, "message": f"Parse error: {e}"},
                }
                sys.stdout.write(json.dumps(err_resp) + "\n")
                sys.stdout.flush()


if __name__ == "__main__":
    server = MCPServer()
    server.run_stdio()
