"""Graph operations, multi-hop traversals, and token-budgeted PageRank."""

from __future__ import annotations

import json
import re
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple
from .db import BrainDB


def _sanitize_fts5_query(query: str) -> str:
    terms = re.findall(r'[a-zA-Z0-9_\-]+', query)
    if not terms:
        return '""'
    return " OR ".join(f'"{t}"' for t in terms[:10])


class BrainGraph:
    def __init__(self, db: Optional[BrainDB] = None):
        self.db = db or BrainDB()

    def upsert_node(
        self,
        node_id: str,
        node_type: str,
        name: str,
        file_path: Optional[str] = None,
        line_start: Optional[int] = None,
        line_end: Optional[int] = None,
        signature: Optional[str] = None,
        content: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        now = time.time()
        conn = self.db.get_connection()
        meta_str = json.dumps(metadata or {})
        
        conn.execute(
            """
            INSERT INTO nodes (id, node_type, name, file_path, line_start, line_end, signature, content, metadata_json, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                node_type = excluded.node_type,
                name = excluded.name,
                file_path = excluded.file_path,
                line_start = excluded.line_start,
                line_end = excluded.line_end,
                signature = excluded.signature,
                content = excluded.content,
                metadata_json = excluded.metadata_json,
                updated_at = excluded.updated_at
            """,
            (node_id, node_type, name, file_path, line_start, line_end, signature or "", content or "", meta_str, now, now),
        )
        
        # Update FTS index
        conn.execute("DELETE FROM node_fts WHERE id = ?", (node_id,))
        conn.execute(
            "INSERT INTO node_fts (id, name, file_path, signature, content) VALUES (?, ?, ?, ?, ?)",
            (node_id, name, file_path or "", signature or "", content or ""),
        )
        conn.commit()

    def upsert_edge(
        self,
        source_id: str,
        target_id: str,
        edge_type: str,
        weight: float = 1.0,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        now = time.time()
        conn = self.db.get_connection()
        meta_str = json.dumps(metadata or {})
        weight = max(0.0, min(1.0, float(weight)))
        
        # Ensure source and target nodes exist (placeholder if needed)
        for nid in (source_id, target_id):
            conn.execute(
                """
                INSERT INTO nodes (id, node_type, name, file_path, line_start, line_end, signature, content, metadata_json, created_at, updated_at)
                VALUES (?, 'symbol', ?, '', 0, 0, '', '', '{}', ?, ?)
                ON CONFLICT(id) DO NOTHING
                """,
                (nid, nid.split(":")[-1], now, now),
            )
        
        conn.execute(
            """
            INSERT INTO edges (source_id, target_id, edge_type, weight, activation_count, last_active_at, metadata_json)
            VALUES (?, ?, ?, ?, 1, ?, ?)
            ON CONFLICT(source_id, target_id, edge_type) DO UPDATE SET
                weight = excluded.weight,
                activation_count = edges.activation_count + 1,
                last_active_at = excluded.last_active_at,
                metadata_json = excluded.metadata_json
            """,
            (source_id, target_id, edge_type, weight, now, meta_str),
        )
        conn.commit()

    def get_node(self, node_id: str) -> Optional[Dict[str, Any]]:
        conn = self.db.get_connection()
        row = conn.execute("SELECT * FROM nodes WHERE id = ?", (node_id,)).fetchone()
        if not row:
            return None
        d = dict(row)
        d["metadata"] = json.loads(d.get("metadata_json") or "{}")
        return d

    def query_fts(self, query_str: str, limit: int = 20, node_types: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        conn = self.db.get_connection()
        sanitized = _sanitize_fts5_query(query_str)
        type_filter = ""
        params: List[Any] = [sanitized]
        
        if node_types:
            placeholders = ",".join("?" for _ in node_types)
            type_filter = f"AND n.node_type IN ({placeholders})"
            params.extend(node_types)
            
        params.append(limit)
        sql = f"""
            SELECT n.*, fts.rank as fts_rank
            FROM node_fts fts
            JOIN nodes n ON fts.id = n.id
            WHERE node_fts MATCH ? {type_filter}
            ORDER BY fts.rank
            LIMIT ?
        """
        try:
            rows = conn.execute(sql, params).fetchall()
        except Exception:
            return []
            
        results = []
        for r in rows:
            d = dict(r)
            d["metadata"] = json.loads(d.get("metadata_json") or "{}")
            results.append(d)
        return results

    def get_neighbors(self, node_id: str, direction: str = "both", edge_types: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        conn = self.db.get_connection()
        results = []
        type_clause = ""
        params: List[Any] = []
        
        if edge_types:
            placeholders = ",".join("?" for _ in edge_types)
            type_clause = f"AND e.edge_type IN ({placeholders})"
            params.extend(edge_types)

        if direction in ("out", "both"):
            p = [node_id] + params
            sql = f"""
                SELECT n.*, e.edge_type, e.weight, 'outgoing' as direction
                FROM edges e
                JOIN nodes n ON e.target_id = n.id
                WHERE e.source_id = ? {type_clause}
                ORDER BY e.weight DESC
            """
            for r in conn.execute(sql, p).fetchall():
                d = dict(r)
                d["metadata"] = json.loads(d.get("metadata_json") or "{}")
                results.append(d)

        if direction in ("in", "both"):
            p = [node_id] + params
            sql = f"""
                SELECT n.*, e.edge_type, e.weight, 'incoming' as direction
                FROM edges e
                JOIN nodes n ON e.source_id = n.id
                WHERE e.target_id = ? {type_clause}
                ORDER BY e.weight DESC
            """
            for r in conn.execute(sql, p).fetchall():
                d = dict(r)
                d["metadata"] = json.loads(d.get("metadata_json") or "{}")
                results.append(d)

        return results

    def graph_walk(
        self,
        seed_node_ids: List[str],
        max_depth: int = 2,
        attenuation: float = 0.85,
        min_weight: float = 0.10,
        limit: int = 50,
    ) -> List[Dict[str, Any]]:
        """Multi-hop recursive SQL CTE traversal with distance/weight attenuation."""
        if not seed_node_ids:
            return []
        
        conn = self.db.get_connection()
        placeholders = ",".join("?" for _ in seed_node_ids)
        
        sql = f"""
        WITH RECURSIVE graph_walk(node_id, depth, score, path) AS (
            SELECT id, 0, 1.0, id
            FROM nodes
            WHERE id IN ({placeholders})
            
            UNION ALL
            
            SELECT 
                e.target_id,
                gw.depth + 1,
                gw.score * e.weight * ?,
                gw.path || ' -> ' || e.target_id
            FROM edges e
            JOIN graph_walk gw ON e.source_id = gw.node_id
            WHERE gw.depth < ?
              AND (gw.score * e.weight * ?) >= ?
              AND instr(gw.path, e.target_id) = 0
        )
        SELECT n.*, MAX(gw.score) as walk_score, MIN(gw.depth) as min_depth
        FROM graph_walk gw
        JOIN nodes n ON gw.node_id = n.id
        GROUP BY n.id
        ORDER BY walk_score DESC
        LIMIT ?;
        """
        
        params = list(seed_node_ids) + [attenuation, max_depth, attenuation, min_weight, limit]
        rows = conn.execute(sql, params).fetchall()
        results = []
        for r in rows:
            d = dict(r)
            d["metadata"] = json.loads(d.get("metadata_json") or "{}")
            results.append(d)
        return results

    def get_context_map(
        self,
        seed_files: Optional[List[str]] = None,
        seed_symbols: Optional[List[str]] = None,
        token_budget: int = 1500,
    ) -> str:
        """Token-budgeted PageRank code map formatted for LLM agent context."""
        seeds = []
        if seed_files:
            for f in seed_files:
                seeds.append(f"sym:file:{f.replace('\\\\', '/')}")
        if seed_symbols:
            seeds.extend(seed_symbols)

        if not seeds:
            # Fallback: get top files by degree
            conn = self.db.get_connection()
            rows = conn.execute(
                """
                SELECT id FROM nodes WHERE node_type = 'symbol'
                ORDER BY updated_at DESC LIMIT 5
                """
            ).fetchall()
            seeds = [r["id"] for r in rows]

        nodes = self.graph_walk(seeds, max_depth=2, limit=40)
        if not nodes:
            return "# sevolve Context Map: (empty graph - run `sevolve brain scan`)"

        # Format into concise Markdown signature skeleton
        lines = ["# sevolve Code Graph Context Map\n\n"]
        by_file: Dict[str, List[Dict[str, Any]]] = {}
        for n in nodes:
            fp = n.get("file_path") or "global"
            by_file.setdefault(fp, []).append(n)

        char_budget = token_budget * 4  # rough ~4 chars per token
        current_len = 0

        for fp, syms in by_file.items():
            file_header = f"## `{fp}`\n"
            if current_len + len(file_header) > char_budget:
                break
            lines.append(file_header)
            current_len += len(file_header)

            for s in syms:
                sig = s.get("signature") or s.get("name")
                doc = s.get("content", "").split("\n")[0] if s.get("content") else ""
                doc_str = f" # {doc[:60]}" if doc else ""
                entry = f"- `{sig}`{doc_str}\n"
                if current_len + len(entry) > char_budget:
                    lines.append("- ... [truncated to fit token budget]\n")
                    return "".join(lines)
                lines.append(entry)
                current_len += len(entry)

        return "".join(lines)
