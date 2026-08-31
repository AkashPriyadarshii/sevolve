"""Hebbian reinforcement, attenuation, half-life decay, and pruning."""

from __future__ import annotations

import json
import math
import time
from typing import Any, Dict, List, Optional
from .db import BrainDB
from .graph import BrainGraph


class HebbianEngine:
    def __init__(self, graph: Optional[BrainGraph] = None):
        self.graph = graph or BrainGraph()
        self.db = self.graph.db

    def reinforce_edge(self, source_id: str, target_id: str, edge_type: str, alpha: float = 0.15) -> float:
        """Strengthen edge weight on success: W(t+1) = W(t) + alpha * (1.0 - W(t))."""
        conn = self.db.get_connection()
        row = conn.execute(
            "SELECT weight, activation_count FROM edges WHERE source_id = ? AND target_id = ? AND edge_type = ?",
            (source_id, target_id, edge_type),
        ).fetchone()

        now = time.time()
        if row:
            curr_w = float(row["weight"])
            new_w = min(1.0, curr_w + alpha * (1.0 - curr_w))
            conn.execute(
                """
                UPDATE edges SET weight = ?, activation_count = activation_count + 1, last_active_at = ?
                WHERE source_id = ? AND target_id = ? AND edge_type = ?
                """,
                (new_w, now, source_id, target_id, edge_type),
            )
        else:
            new_w = min(1.0, 0.5 + alpha)
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
                INSERT INTO edges (source_id, target_id, edge_type, weight, activation_count, last_active_at)
                VALUES (?, ?, ?, ?, 1, ?)
                """,
                (source_id, target_id, edge_type, new_w, now),
            )
        conn.commit()
        return new_w

    def attenuate_edge(self, source_id: str, target_id: str, edge_type: str, beta: float = 0.20) -> float:
        """Decrease edge weight on failure: W(t+1) = max(0.0, W(t) - beta * W(t))."""
        conn = self.db.get_connection()
        row = conn.execute(
            "SELECT weight FROM edges WHERE source_id = ? AND target_id = ? AND edge_type = ?",
            (source_id, target_id, edge_type),
        ).fetchone()

        now = time.time()
        if row:
            curr_w = float(row["weight"])
            new_w = max(0.0, curr_w - beta * curr_w)
            conn.execute(
                """
                UPDATE edges SET weight = ?, last_active_at = ?
                WHERE source_id = ? AND target_id = ? AND edge_type = ?
                """,
                (new_w, now, source_id, target_id, edge_type),
            )
            conn.commit()
            return new_w
        return 0.0

    def record_trace(
        self,
        session_id: str,
        prompt: str,
        events: List[Dict[str, Any]],
        output: str,
        ok: bool,
        changed_files: Optional[List[str]] = None,
        error_type: Optional[str] = None,
        error_message: Optional[str] = None,
    ) -> str:
        """Ingest an execution trace into the cognitive layer and update Hebbian weights."""
        trace_node_id = f"trace:{session_id}"
        self.graph.upsert_node(
            node_id=trace_node_id,
            node_type="trace",
            name=f"Session {session_id[:12]}",
            content=prompt,
            signature=f"Trace ok={ok} events={len(events)}",
            metadata={"output": output[:500], "ok": ok, "event_count": len(events)},
        )

        files = changed_files or []
        # Co-modification edges between changed files
        for i, f1 in enumerate(files):
            id1 = f"sym:file:{f1.replace('\\\\', '/')}"
            # Ensure file node exists
            if not self.graph.get_node(id1):
                self.graph.upsert_node(id1, "symbol", f1, file_path=f1)
            
            # Connect trace to file
            self.graph.upsert_edge(trace_node_id, id1, "touched")

            for f2 in files[i + 1:]:
                id2 = f"sym:file:{f2.replace('\\\\', '/')}"
                if not self.graph.get_node(id2):
                    self.graph.upsert_node(id2, "symbol", f2, file_path=f2)
                
                if ok:
                    self.reinforce_edge(id1, id2, "co_modified_with", alpha=0.15)
                    self.reinforce_edge(id2, id1, "co_modified_with", alpha=0.15)
                else:
                    self.attenuate_edge(id1, id2, "co_modified_with", beta=0.10)

        # Failure & Fix recording
        if not ok and (error_type or error_message):
            fail_id = f"fail:{hashlib_short(f'{error_type}:{error_message}')}"
            self.graph.upsert_node(
                node_id=fail_id,
                node_type="failure",
                name=error_type or "RuntimeError",
                content=error_message or "",
                signature=f"Failure: {error_type}",
            )
            self.graph.upsert_edge(trace_node_id, fail_id, "failed_with")
            for f in files:
                fid = f"sym:file:{f.replace('\\\\', '/')}"
                self.graph.upsert_edge(fail_id, fid, "failed_on")

        return trace_node_id

    def decay_and_prune(self, half_life_days: float = 7.0, prune_threshold: float = 0.05) -> Dict[str, int]:
        """Apply exponential half-life decay to behavioral edges and prune dead ones."""
        conn = self.db.get_connection()
        now = time.time()
        decay_constant = math.log(2) / (half_life_days * 86400.0)

        # Select dynamic/behavioral edges
        behavioral_types = ("co_modified_with", "recalled_with", "touched", "failed_with")
        placeholders = ",".join("?" for _ in behavioral_types)
        
        rows = conn.execute(
            f"SELECT source_id, target_id, edge_type, weight, last_active_at FROM edges WHERE edge_type IN ({placeholders})",
            behavioral_types,
        ).fetchall()

        decayed_count = 0
        pruned_count = 0

        for r in rows:
            dt = max(0.0, now - float(r["last_active_at"]))
            new_w = float(r["weight"]) * math.exp(-decay_constant * dt)
            if new_w < prune_threshold:
                conn.execute(
                    "DELETE FROM edges WHERE source_id = ? AND target_id = ? AND edge_type = ?",
                    (r["source_id"], r["target_id"], r["edge_type"]),
                )
                pruned_count += 1
            else:
                conn.execute(
                    "UPDATE edges SET weight = ? WHERE source_id = ? AND target_id = ? AND edge_type = ?",
                    (new_w, r["source_id"], r["target_id"], r["edge_type"]),
                )
                decayed_count += 1

        conn.commit()
        return {"decayed": decayed_count, "pruned": pruned_count}


def hashlib_short(text: str) -> str:
    import hashlib
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:12]
