"""Bi-directional Obsidian Markdown vault sync for sevolve brain.

Exports nodes to `.sevolve/vault/*.md` with YAML frontmatter and `[[WikiLinks]]`.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Dict, List, Optional
from .db import BrainDB
from .graph import BrainGraph


def _sanitize_filename(node_id: str) -> str:
    safe = re.sub(r'[^a-zA-Z0-9_\-]+', '_', node_id)
    safe = re.sub(r'_+', '_', safe).strip('_')
    if len(safe) > 80:
        import hashlib
        h = hashlib.sha256(node_id.encode("utf-8")).hexdigest()[:8]
        safe = f"{safe[:60]}_{h}"
    return safe or "node"


class VaultSync:
    def __init__(self, graph: Optional[BrainGraph] = None):
        self.graph = graph or BrainGraph()
        self.db = self.graph.db

    def export_vault(self, target_dir: str | Path = ".sevolve/vault") -> int:
        """Export all nodes and edges into Obsidian Markdown files."""
        out_dir = Path(target_dir)
        out_dir.mkdir(parents=True, exist_ok=True)
        
        conn = self.db.get_connection()
        nodes = conn.execute("SELECT * FROM nodes").fetchall()
        
        count = 0
        for n in nodes:
            node_id = n["id"]
            safe_name = _sanitize_filename(node_id)
            file_path = out_dir / f"{safe_name}.md"

            # Get outgoing edges
            edges = self.graph.get_neighbors(node_id, direction="out")
            links_by_type: Dict[str, List[str]] = {}
            for e in edges:
                target_safe = _sanitize_filename(e["id"])
                links_by_type.setdefault(e["edge_type"], []).append(
                    f"[[{target_safe}|{e['name']}]] (w={e['weight']:.2f})"
                )

            frontmatter = {
                "id": node_id,
                "type": n["node_type"],
                "name": n["name"],
                "file_path": n["file_path"],
                "line_start": n["line_start"],
                "line_end": n["line_end"],
                "signature": n["signature"],
                "created_at": n["created_at"],
                "updated_at": n["updated_at"],
            }
            
            fm_yaml = "\n".join(f"{k}: {json.dumps(v)}" for k, v in frontmatter.items() if v is not None)
            
            body_parts = [f"---\n{fm_yaml}\n---\n"]
            body_parts.append(f"# {n['name']}\n")
            if n["signature"]:
                body_parts.append(f"```python\n{n['signature']}\n```\n")
            if n["content"]:
                body_parts.append(f"## Documentation\n{n['content']}\n")

            if links_by_type:
                body_parts.append("## Relationships\n")
                for etype, links in links_by_type.items():
                    body_parts.append(f"### {etype.upper()}\n")
                    for link in links:
                        body_parts.append(f"- {link}\n")

            file_path.write_text("".join(body_parts), encoding="utf-8")
            count += 1

        return count

    def import_vault(self, target_dir: str | Path = ".sevolve/vault") -> int:
        """Scan Obsidian Markdown files in vault and sync back into SQLite."""
        in_dir = Path(target_dir)
        if not in_dir.exists():
            return 0
            
        count = 0
        for md_file in in_dir.glob("*.md"):
            text = md_file.read_text(encoding="utf-8", errors="replace")
            fm_match = re.match(r"^---\s*\n(.*?)\n---\s*\n(.*)$", text, re.DOTALL)
            if not fm_match:
                continue
                
            fm_text, body = fm_match.groups()
            fm: Dict[str, Any] = {}
            for line in fm_text.splitlines():
                if ":" in line:
                    k, v = line.split(":", 1)
                    try:
                        fm[k.strip()] = json.loads(v.strip())
                    except Exception:
                        fm[k.strip()] = v.strip()
                        
            node_id = fm.get("id")
            if not node_id:
                continue
                
            self.graph.upsert_node(
                node_id=node_id,
                node_type=fm.get("type", "symbol"),
                name=fm.get("name", md_file.stem),
                file_path=fm.get("file_path"),
                line_start=fm.get("line_start"),
                line_end=fm.get("line_end"),
                signature=fm.get("signature"),
                content=body.strip(),
            )
            count += 1
            
        return count
