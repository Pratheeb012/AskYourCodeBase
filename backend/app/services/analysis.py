import ast
import re
from typing import List, Dict, Optional
from pathlib import Path
from app.services.ingestion import get_all_code_files, detect_language


class StaticIssue:
    def __init__(self, file_path: str, line: int, issue_type: str, message: str, severity: str):
        self.file_path = file_path
        self.line = line
        self.issue_type = issue_type
        self.message = message
        self.severity = severity  # "warning" | "info" | "error"

    def to_dict(self):
        return {
            "file_path": self.file_path,
            "line": self.line,
            "issue_type": self.issue_type,
            "message": self.message,
            "severity": self.severity,
        }


def analyze_python_file(file_path: Path, repo_root: str) -> List[StaticIssue]:
    """Basic static analysis for Python files."""
    rel_path = str(file_path.relative_to(repo_root)).replace("\\", "/")
    issues = []
    try:
        content = file_path.read_text(encoding="utf-8", errors="replace")
        tree = ast.parse(content)
    except Exception:
        return []

    lines = content.splitlines()

    for node in ast.walk(tree):
        # Long functions (> 80 lines)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            func_len = (node.end_lineno or 0) - node.lineno
            if func_len > 80:
                issues.append(StaticIssue(
                    file_path=rel_path,
                    line=node.lineno,
                    issue_type="long_function",
                    message=f"Function '{node.name}' is {func_len} lines long (recommended < 80)",
                    severity="warning",
                ))
            # Detect too many arguments
            arg_count = len(node.args.args) + len(node.args.kwonlyargs)
            if arg_count > 7:
                issues.append(StaticIssue(
                    file_path=rel_path,
                    line=node.lineno,
                    issue_type="too_many_args",
                    message=f"Function '{node.name}' has {arg_count} parameters (recommended < 7)",
                    severity="info",
                ))

        # Detect bare except
        if isinstance(node, ast.ExceptHandler) and node.type is None:
            issues.append(StaticIssue(
                file_path=rel_path,
                line=node.lineno,
                issue_type="bare_except",
                message="Bare 'except:' clause catches all exceptions including SystemExit",
                severity="warning",
            ))

        # Detect TODO/FIXME comments
    for i, line in enumerate(lines, 1):
        if re.search(r"\b(TODO|FIXME|HACK|XXX)\b", line, re.IGNORECASE):
            issues.append(StaticIssue(
                file_path=rel_path,
                line=i,
                issue_type="todo_comment",
                message=f"Found marker: {line.strip()[:80]}",
                severity="info",
            ))

    return issues


def run_static_analysis(repo_path: str) -> Dict:
    """Run static analysis across the entire repo."""
    files = get_all_code_files(repo_path)
    all_issues: List[StaticIssue] = []

    for f in files:
        lang = detect_language(f)
        if lang == "python":
            issues = analyze_python_file(f, repo_path)
            all_issues.extend(issues)

    summary = {
        "total_issues": len(all_issues),
        "by_severity": {},
        "by_type": {},
        "issues": [i.to_dict() for i in all_issues[:200]],  # Cap at 200
    }

    for issue in all_issues:
        summary["by_severity"][issue.severity] = summary["by_severity"].get(issue.severity, 0) + 1
        summary["by_type"][issue.issue_type] = summary["by_type"].get(issue.issue_type, 0) + 1

    return summary


def build_dependency_graph(repo_path: str) -> Dict:
    """Build a simple import dependency graph for Python files."""
    files = get_all_code_files(repo_path)
    graph = {}
    module_map = {}

    # Map file paths to module names
    for f in files:
        if detect_language(f) != "python":
            continue
        rel = str(f.relative_to(repo_path)).replace("\\", "/").replace("/", ".").replace(".py", "")
        module_map[rel] = str(f.relative_to(repo_path)).replace("\\", "/")

    for f in files:
        if detect_language(f) != "python":
            continue
        rel_path = str(f.relative_to(repo_path)).replace("\\", "/")
        try:
            content = f.read_text(encoding="utf-8", errors="replace")
            tree = ast.parse(content)
        except Exception:
            continue

        imports = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.add(alias.name.split(".")[0])
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    imports.add(node.module.split(".")[0])

        graph[rel_path] = list(imports)

    return {
        "nodes": list(set(graph.keys())),
        "edges": [
            {"from": src, "to": dep}
            for src, deps in graph.items()
            for dep in deps
        ],
    }
