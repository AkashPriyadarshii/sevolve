"""Versioned artifact store.

An artifact is a skill, prompt, tool description, or rule that the engine
evolves. Content lives as real files (readable diffs); metadata is JSONL
alongside. Git is the VCS, the store is the working tree.
"""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any, Optional

KINDS = {"skill", "prompt", "tool_desc", "rule"}
DRAFT, PROMOTED, ROLLED_BACK = "draft", "promoted", "rolled_back"


def _now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


class ArtifactStore:
    def __init__(self, root: Path | str = "artifacts"):
        self.root = Path(root)

    def _dir(self, kind: str, aid: str) -> Path:
        if kind not in KINDS:
            raise ValueError(f"unknown kind {kind!r}; use one of {sorted(KINDS)}")
        return self.root / kind / aid

    def _ensure_dir(self, kind: str, aid: str) -> Path:
        d = self._dir(kind, aid)
        d.mkdir(parents=True, exist_ok=True)
        return d

    def _meta_path(self, kind: str, aid: str) -> Path:
        return self._dir(kind, aid) / "meta.jsonl"

    def add_version(
        self,
        kind: str,
        aid: str,
        content: str,
        parent: int | None = None,
        status: str = DRAFT,
        score: float | None = None,
        grades: dict[str, Any] | None = None,
        trace_ids: list[str] | None = None,
    ) -> dict[str, Any]:
        meta = self.meta(kind, aid)
        if not meta:
            version = 1
            rec_parent = parent
        else:
            latest = meta[-1]
            version = latest["version"] + 1
            rec_parent = parent if parent is not None else latest["version"]

        rec = {
            "version": version,
            "parent": rec_parent,
            "created_at": _now(),
            "status": status,
            "score": score,
            "grades": grades if grades is not None else {},
            "trace_ids": trace_ids if trace_ids is not None else [],
        }
        d = self._ensure_dir(kind, aid)
        d.joinpath(f"v{version}.txt").write_text(content, encoding="utf-8")
        with self._meta_path(kind, aid).open("a", encoding="utf-8") as f:
            f.write(json.dumps(rec) + "\n")
        return rec

    def create(self, kind: str, aid: str, content: str) -> dict[str, Any]:
        meta = self.meta(kind, aid)
        if meta:
            raise ValueError(f"artifact {kind}/{aid} already exists")
        return self.add_version(kind, aid, content)

    def meta(self, kind: str, aid: str) -> list[dict[str, Any]]:
        p = self._meta_path(kind, aid)
        if not p.exists():
            return []
        return [json.loads(line) for line in p.read_text(encoding="utf-8").splitlines() if line]

    def get(self, kind: str, aid: str) -> dict[str, Any] | None:
        """Latest version as {**record, content}."""
        meta = self.meta(kind, aid)
        if not meta:
            return None
        latest = meta[-1]
        p = self._dir(kind, aid) / f"v{latest['version']}.txt"
        if not p.exists():
            return None
        content = p.read_text(encoding="utf-8")
        return {**latest, "content": content, "kind": kind, "id": aid}

    def get_version(self, kind: str, aid: str, version: int) -> dict[str, Any] | None:
        meta = [m for m in self.meta(kind, aid) if m["version"] == version]
        if not meta:
            return None
        p = self._dir(kind, aid) / f"v{version}.txt"
        if not p.exists():
            return None
        content = p.read_text(encoding="utf-8")
        return {**meta[0], "content": content, "kind": kind, "id": aid}

    def set_score(self, kind: str, aid: str, version: int, score: float, grades: dict[str, Any], trace_ids: list[str]) -> None:
        """Rewrite the meta line for a version with eval results (idempotent)."""
        lines = self.meta(kind, aid)
        for rec in lines:
            if rec["version"] == version:
                rec["score"] = score
                rec["grades"] = grades
                rec["trace_ids"] = trace_ids
        self._write_meta(kind, aid, lines)

    def set_status(self, kind: str, aid: str, version: int, status: str) -> None:
        lines = self.meta(kind, aid)
        for rec in lines:
            if rec["version"] == version:
                rec["status"] = status
        self._write_meta(kind, aid, lines)

    def _write_meta(self, kind: str, aid: str, lines: list[dict[str, Any]]) -> None:
        with self._meta_path(kind, aid).open("w", encoding="utf-8") as f:
            for rec in lines:
                f.write(json.dumps(rec) + "\n")

    def list(self, kind: Optional[str] = None) -> list[dict[str, Any]]:
        out = []
        if not self.root.exists():
            return out
        kinds = [kind] if kind else sorted(d.name for d in self.root.iterdir() if d.is_dir())
        for k in kinds:
            base = self.root / k
            if not base.exists():
                continue
            for d in sorted(base.iterdir()):
                if not d.is_dir():
                    continue
                meta = self.meta(k, d.name)
                if meta:
                    latest = meta[-1]
                    out.append({"id": d.name, "kind": k, "version": latest["version"],
                                "status": latest["status"], "score": latest["score"]})
        return out
