"""CLI subcommand handlers for `sevolve brain`."""

from __future__ import annotations

import argparse
from pathlib import Path
from .db import BrainDB
from .graph import BrainGraph
from .parser import scan_directory
from .hebbian import HebbianEngine
from .vault import VaultSync


def cmd_brain_scan(args: argparse.Namespace) -> int:
    target_dir = getattr(args, "dir", ".") or "."
    db_path = getattr(args, "db", ".sevolve/brain.db") or ".sevolve/brain.db"
    
    print(f"Scanning Python AST in {target_dir} -> {db_path}...")
    symbols, edges = scan_directory(target_dir)
    
    db = BrainDB(db_path)
    graph = BrainGraph(db)
    
    for s in symbols:
        graph.upsert_node(
            node_id=s["id"],
            node_type=s["node_type"],
            name=s["name"],
            file_path=s.get("file_path"),
            line_start=s.get("line_start"),
            line_end=s.get("line_end"),
            signature=s.get("signature"),
            content=s.get("content"),
            metadata=s.get("metadata"),
        )
        
    for e in edges:
        target_id = e.get("target_id")
        if not target_id and e.get("target_name"):
            # Best effort link
            target_id = f"sym:ref:{e['target_name']}"
            if not graph.get_node(target_id):
                graph.upsert_node(target_id, "symbol", e["target_name"])
        if target_id:
            graph.upsert_edge(e["source_id"], target_id, e["edge_type"])
            
    print(f"Indexed {len(symbols)} symbols and {len(edges)} structural edges into {db_path}")
    return 0


def cmd_brain_query(args: argparse.Namespace) -> int:
    query = args.query
    limit = getattr(args, "limit", 10) or 10
    db_path = getattr(args, "db", ".sevolve/brain.db") or ".sevolve/brain.db"
    
    db = BrainDB(db_path)
    graph = BrainGraph(db)
    results = graph.query_fts(query, limit=limit)
    
    if not results:
        print(f"No results found for '{query}'")
        return 0
        
    print(f"Found {len(results)} matches for '{query}':\n")
    for r in results:
        print(f"[{r['node_type'].upper()}] {r['name']} ({r.get('file_path') or 'global'})")
        if r.get("signature"):
            print(f"  sig: {r['signature']}")
        if r.get("content"):
            print(f"  doc: {r['content'][:100]}")
        print()
    return 0


def cmd_brain_map(args: argparse.Namespace) -> int:
    file_path = args.file_path
    db_path = getattr(args, "db", ".sevolve/brain.db") or ".sevolve/brain.db"
    budget = getattr(args, "tokens", 1500) or 1500
    
    db = BrainDB(db_path)
    graph = BrainGraph(db)
    context_map = graph.get_context_map(seed_files=[file_path], token_budget=budget)
    print(context_map)
    return 0


def cmd_brain_sync(args: argparse.Namespace) -> int:
    vault_dir = getattr(args, "vault", ".sevolve/vault") or ".sevolve/vault"
    db_path = getattr(args, "db", ".sevolve/brain.db") or ".sevolve/brain.db"
    direction = getattr(args, "direction", "export") or "export"
    
    db = BrainDB(db_path)
    graph = BrainGraph(db)
    vault = VaultSync(graph)
    
    if direction == "import":
        count = vault.import_vault(vault_dir)
        print(f"Imported {count} nodes from Obsidian vault ({vault_dir}) into brain DB ({db_path})")
    else:
        count = vault.export_vault(vault_dir)
        print(f"Exported {count} nodes to Obsidian vault at {vault_dir}")
    return 0


def cmd_brain_prune(args: argparse.Namespace) -> int:
    db_path = getattr(args, "db", ".sevolve/brain.db") or ".sevolve/brain.db"
    half_life = getattr(args, "half_life", 7.0) or 7.0
    threshold = getattr(args, "threshold", 0.05) or 0.05
    
    db = BrainDB(db_path)
    graph = BrainGraph(db)
    hebbian = HebbianEngine(graph)
    
    res = hebbian.decay_and_prune(half_life_days=half_life, prune_threshold=threshold)
    print(f"Hebbian decay applied: {res['decayed']} edges decayed, {res['pruned']} edges pruned.")
    return 0
