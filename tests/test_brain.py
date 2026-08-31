"""Hermetic tests for engine/brain (AST parser, Graph, Hebbian, Vault, and MCP)."""

import json
from pathlib import Path
from engine.brain.db import BrainDB
from engine.brain.graph import BrainGraph
from engine.brain.parser import parse_python_file, scan_directory
from engine.brain.hebbian import HebbianEngine
from engine.brain.vault import VaultSync
from engine.brain.mcp import MCPServer


def test_brain_ast_parser(tmp_path: Path) -> None:
    code = '''"""Sample module docstring."""
import os
from engine.trace import Trace

class Calculator:
    """A math helper."""
    def add(self, a: int, b: int) -> int:
        """Add two numbers."""
        return a + b

def run_calc():
    c = Calculator()
    return c.add(1, 2)
'''
    py_file = tmp_path / "sample.py"
    py_file.write_text(code, encoding="utf-8")

    symbols, edges = parse_python_file(py_file, root_dir=tmp_path)
    sym_names = [s["name"] for s in symbols]
    assert "sample.py" in sym_names
    assert "Calculator" in sym_names
    assert "Calculator.add" in sym_names
    assert "run_calc" in sym_names

    edge_types = [e["edge_type"] for e in edges]
    assert "imports" in edge_types
    assert "defined_in" in edge_types
    assert "calls" in edge_types


def test_brain_db_and_graph(tmp_path: Path) -> None:
    db_file = tmp_path / "brain.db"
    db = BrainDB(db_file)
    graph = BrainGraph(db)

    # Upsert nodes
    graph.upsert_node("sym:func:foo", "symbol", "foo", signature="def foo() -> None", content="Do foo stuff")
    graph.upsert_node("sym:func:bar", "symbol", "bar", signature="def bar() -> None", content="Do bar stuff")
    graph.upsert_node("rule:no-bloat", "rule", "No Bloat", content="Keep code minimal and stdlib only")

    # Upsert edges
    graph.upsert_edge("sym:func:foo", "sym:func:bar", "calls", weight=0.9)
    graph.upsert_edge("rule:no-bloat", "sym:func:foo", "applies_to", weight=1.0)

    # Test node retrieval
    n = graph.get_node("sym:func:foo")
    assert n is not None
    assert n["name"] == "foo"
    assert n["signature"] == "def foo() -> None"

    # Test FTS query
    res = graph.query_fts("minimal", limit=5)
    assert len(res) >= 1
    assert res[0]["id"] == "rule:no-bloat"

    # Test graph walk (multi-hop CTE)
    walk_res = graph.graph_walk(["rule:no-bloat"], max_depth=2)
    walk_ids = [r["id"] for r in walk_res]
    assert "rule:no-bloat" in walk_ids
    assert "sym:func:foo" in walk_ids
    assert "sym:func:bar" in walk_ids

    # Test context map
    cmap = graph.get_context_map(seed_symbols=["sym:func:foo"], token_budget=1000)
    assert "sevolve Code Graph Context Map" in cmap
    assert "foo" in cmap


def test_brain_hebbian_dynamics(tmp_path: Path) -> None:
    db_file = tmp_path / "hebbian.db"
    db = BrainDB(db_file)
    graph = BrainGraph(db)
    hebbian = HebbianEngine(graph)

    # Reinforce edge
    w1 = hebbian.reinforce_edge("sym:file:a.py", "sym:file:b.py", "co_modified_with", alpha=0.15)
    assert w1 > 0.5

    # Reinforce again
    w2 = hebbian.reinforce_edge("sym:file:a.py", "sym:file:b.py", "co_modified_with", alpha=0.15)
    assert w2 > w1

    # Attenuate edge
    w3 = hebbian.attenuate_edge("sym:file:a.py", "sym:file:b.py", "co_modified_with", beta=0.20)
    assert w3 < w2

    # Ingest trace
    t_id = hebbian.record_trace(
        session_id="sess_001",
        prompt="Fix mutex deadlock",
        events=[{"tool": "edit", "file": "a.py"}],
        output="Deadlock resolved",
        ok=True,
        changed_files=["a.py", "b.py"],
    )
    assert t_id.startswith("trace:")
    t_node = graph.get_node(t_id)
    assert t_node is not None


def test_brain_vault_sync(tmp_path: Path) -> None:
    db_file = tmp_path / "vault.db"
    vault_dir = tmp_path / "vault"
    db = BrainDB(db_file)
    graph = BrainGraph(db)
    vault = VaultSync(graph)

    graph.upsert_node("sym:class:Engine", "symbol", "Engine", signature="class Engine", content="Core runner")
    graph.upsert_node("rule:hermetic", "rule", "Hermetic Rule", content="All tests must run offline")
    graph.upsert_edge("rule:hermetic", "sym:class:Engine", "applies_to", weight=0.95)

    # Export
    exported = vault.export_vault(vault_dir)
    assert exported == 2
    assert (vault_dir / "sym_class_Engine.md").exists()
    assert (vault_dir / "rule_hermetic.md").exists()

    # Import into fresh DB
    db2 = BrainDB(tmp_path / "vault2.db")
    graph2 = BrainGraph(db2)
    vault2 = VaultSync(graph2)
    imported = vault2.import_vault(vault_dir)
    assert imported == 2
    assert graph2.get_node("sym:class:Engine") is not None


def test_brain_mcp_server(tmp_path: Path) -> None:
    db_file = tmp_path / "mcp.db"
    server = MCPServer(str(db_file))
    server.graph.upsert_node("sym:func:solve", "symbol", "solve", signature="def solve()", content="Solve task")

    # 1. Initialize
    init_res = server.handle_request({"id": 1, "method": "initialize"})
    assert init_res["result"]["serverInfo"]["name"] == "sevolve-brain"

    # 2. List tools
    tools_res = server.handle_request({"id": 2, "method": "tools/list"})
    tool_names = [t["name"] for t in tools_res["result"]["tools"]]
    assert "search_brain" in tool_names
    assert "get_context_map" in tool_names
    assert "query_codegraph" in tool_names
    assert "record_trace" in tool_names
    assert "suggest_fixes" in tool_names

    # 3. Call search_brain
    call_res = server.handle_request({
        "id": 3,
        "method": "tools/call",
        "params": {
            "name": "search_brain",
            "arguments": {"query": "solve"},
        },
    })
    assert "sym:func:solve" in call_res["result"]["content"][0]["text"]

    # 4. Call record_trace
    call_rec = server.handle_request({
        "id": 4,
        "method": "tools/call",
        "params": {
            "name": "record_trace",
            "arguments": {
                "session_id": "s_123",
                "prompt": "Test prompt",
                "ok": True,
                "changed_files": ["engine/test.py"],
            },
        },
    })
    assert "trace:" in call_rec["result"]["content"][0]["text"]
