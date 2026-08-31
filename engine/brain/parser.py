"""AST Code parser for Python using the standard library `ast`.

Extracts classes, functions, methods, signatures, imports, and calls.
"""

from __future__ import annotations

import ast
import hashlib
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple


def _format_signature(node: ast.FunctionDef | ast.AsyncFunctionDef) -> str:
    args = []
    # positional args
    for a in node.args.args:
        ann = f": {ast.unparse(a.annotation)}" if a.annotation else ""
        args.append(f"{a.arg}{ann}")
    
    # vararg
    if node.args.vararg:
        args.append(f"*{node.args.vararg.arg}")
    
    # kwarg
    if node.args.kwarg:
        args.append(f"**{node.args.kwarg.arg}")
    
    ret = f" -> {ast.unparse(node.returns)}" if node.returns else ""
    async_prefix = "async " if isinstance(node, ast.AsyncFunctionDef) else ""
    return f"{async_prefix}def {node.name}({', '.join(args)}){ret}"


class CodeVisitor(ast.NodeVisitor):
    def __init__(self, file_path: str, source_code: str):
        self.file_path = file_path
        self.source_code = source_code
        self.lines = source_code.splitlines()
        self.symbols: List[Dict[str, Any]] = []
        self.edges: List[Dict[str, Any]] = []
        self._current_scope: List[str] = []
        self.imports: List[str] = []

    def visit_Import(self, node: ast.Import) -> None:
        for alias in node.names:
            self.imports.append(alias.name)
            self.edges.append({
                "source_id": f"sym:file:{self.file_path}",
                "target_name": alias.name,
                "edge_type": "imports",
                "line": node.lineno,
            })
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        mod = node.module or ""
        for alias in node.names:
            full = f"{mod}.{alias.name}" if mod else alias.name
            self.imports.append(full)
            self.edges.append({
                "source_id": f"sym:file:{self.file_path}",
                "target_name": full,
                "edge_type": "imports",
                "line": node.lineno,
            })
        self.generic_visit(node)

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        class_id = f"sym:class:{self.file_path}:{node.name}"
        bases = [ast.unparse(b) for b in node.bases]
        doc = ast.get_docstring(node) or ""
        
        self.symbols.append({
            "id": class_id,
            "node_type": "symbol",
            "name": node.name,
            "file_path": self.file_path,
            "line_start": node.lineno,
            "line_end": getattr(node, "end_lineno", node.lineno),
            "signature": f"class {node.name}({', '.join(bases)})",
            "content": doc,
            "metadata": {
                "kind": "class",
                "bases": bases,
            }
        })
        
        self.edges.append({
            "source_id": class_id,
            "target_id": f"sym:file:{self.file_path}",
            "edge_type": "defined_in",
        })
        
        for base in bases:
            self.edges.append({
                "source_id": class_id,
                "target_name": base,
                "edge_type": "inherits",
            })

        self._current_scope.append(node.name)
        self.generic_visit(node)
        self._current_scope.pop()

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        self._handle_function(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        self._handle_function(node)

    def _handle_function(self, node: ast.FunctionDef | ast.AsyncFunctionDef) -> None:
        scope = ".".join(self._current_scope)
        full_name = f"{scope}.{node.name}" if scope else node.name
        func_id = f"sym:func:{self.file_path}:{full_name}"
        sig = _format_signature(node)
        doc = ast.get_docstring(node) or ""

        self.symbols.append({
            "id": func_id,
            "node_type": "symbol",
            "name": full_name,
            "file_path": self.file_path,
            "line_start": node.lineno,
            "line_end": getattr(node, "end_lineno", node.lineno),
            "signature": sig,
            "content": doc,
            "metadata": {
                "kind": "method" if self._current_scope else "function",
                "is_async": isinstance(node, ast.AsyncFunctionDef),
            }
        })

        parent_id = (
            f"sym:class:{self.file_path}:{self._current_scope[-1]}"
            if self._current_scope
            else f"sym:file:{self.file_path}"
        )
        self.edges.append({
            "source_id": func_id,
            "target_id": parent_id,
            "edge_type": "defined_in",
        })

        # Capture calls inside function
        calls = []
        for child in ast.walk(node):
            if isinstance(child, ast.Call):
                try:
                    callee = ast.unparse(child.func)
                    calls.append(callee)
                    self.edges.append({
                        "source_id": func_id,
                        "target_name": callee,
                        "edge_type": "calls",
                    })
                except Exception:
                    pass

        self._current_scope.append(node.name)
        self.generic_visit(node)
        self._current_scope.pop()


def parse_python_file(file_path: str | Path, root_dir: str | Path = ".") -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """Parse a single Python file into symbols and edges."""
    path = Path(file_path)
    root = Path(root_dir)
    rel_path = str(path.relative_to(root)).replace("\\", "/") if path.is_absolute() else str(path).replace("\\", "/")
    
    if not path.exists():
        return [], []
    
    source = path.read_text(encoding="utf-8", errors="replace")
    try:
        tree = ast.parse(source, filename=str(path))
    except SyntaxError:
        return [], []

    visitor = CodeVisitor(rel_path, source)
    
    # Add file-level node
    file_node_id = f"sym:file:{rel_path}"
    file_doc = ast.get_docstring(tree) or ""
    symbols = [{
        "id": file_node_id,
        "node_type": "symbol",
        "name": rel_path,
        "file_path": rel_path,
        "line_start": 1,
        "line_end": len(visitor.lines),
        "signature": f"module {rel_path}",
        "content": file_doc,
        "metadata": {"kind": "file", "line_count": len(visitor.lines)},
    }]

    visitor.visit(tree)
    symbols.extend(visitor.symbols)
    return symbols, visitor.edges


def scan_directory(root_dir: str | Path = ".", excludes: Optional[List[str]] = None) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """Scan all python files in directory."""
    root = Path(root_dir)
    default_excludes = {".git", ".venv", "venv", "__pycache__", ".pytest_cache", "build", "dist", ".sevolve"}
    if excludes:
        default_excludes.update(excludes)
        
    all_symbols = []
    all_edges = []
    
    for p in root.rglob("*.py"):
        if any(part in default_excludes for part in p.parts):
            continue
        syms, edgs = parse_python_file(p, root)
        all_symbols.extend(syms)
        all_edges.extend(edgs)
        
    return all_symbols, all_edges
