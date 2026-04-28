import os
import re
import ast
import shutil
import zipfile
import hashlib
from pathlib import Path
from typing import List, Dict, Optional, Tuple
import git
from app.core.config import settings

# Files/dirs to ignore during ingestion
IGNORE_DIRS = {
    "node_modules", ".git", "dist", "build", "__pycache__", ".next",
    "venv", ".venv", "env", ".env", "coverage", ".nyc_output",
    "target", ".gradle", ".idea", ".vscode", "vendor", "bower_components",
    "eggs", ".eggs", "*.egg-info", ".tox", ".pytest_cache", ".mypy_cache",
}

IGNORE_EXTENSIONS = {
    ".png", ".jpg", ".jpeg", ".gif", ".svg", ".ico", ".webp", ".bmp",
    ".mp4", ".avi", ".mov", ".mp3", ".wav", ".ogg",
    ".zip", ".tar", ".gz", ".rar", ".7z",
    ".lock", ".sum", ".mod",
    ".min.js", ".min.css",
    ".woff", ".woff2", ".ttf", ".eot",
    ".pdf", ".docx", ".xlsx",
    ".pyc", ".pyo", ".class", ".o", ".so", ".dll",
    ".bin", ".exe", ".app",
}

LANGUAGE_MAP = {
    ".py": "python", ".js": "javascript", ".jsx": "javascript",
    ".ts": "typescript", ".tsx": "typescript", ".java": "java",
    ".go": "go", ".rs": "rust", ".cpp": "cpp", ".c": "c",
    ".cs": "csharp", ".rb": "ruby", ".php": "php", ".swift": "swift",
    ".kt": "kotlin", ".scala": "scala", ".sh": "bash",
    ".yaml": "yaml", ".yml": "yaml", ".json": "json",
    ".html": "html", ".css": "css", ".md": "markdown",
    ".sql": "sql", ".r": "r", ".vue": "vue",
}

MAX_CHUNK_TOKENS = 800
MIN_CHUNK_LINES = 5


class CodeChunk:
    def __init__(
        self,
        content: str,
        file_path: str,
        start_line: int,
        end_line: int,
        language: str,
        chunk_type: str = "block",  # function | class | block
        name: Optional[str] = None,
    ):
        self.content = content
        self.file_path = file_path
        self.start_line = start_line
        self.end_line = end_line
        self.language = language
        self.chunk_type = chunk_type
        self.name = name
        self.metadata = {
            "file_path": file_path,
            "start_line": start_line,
            "end_line": end_line,
            "language": language,
            "chunk_type": chunk_type,
            "name": name or "",
        }

    def to_dict(self) -> dict:
        return {
            "content": self.content,
            "file_path": self.file_path,
            "start_line": self.start_line,
            "end_line": self.end_line,
            "language": self.language,
            "chunk_type": self.chunk_type,
            "name": self.name or "",
        }


def should_ignore_path(path: Path) -> bool:
    """Return True if this path should be skipped."""
    for part in path.parts:
        if part in IGNORE_DIRS:
            return True
    ext = path.suffix.lower()
    if ext in IGNORE_EXTENSIONS:
        return True
    # Skip minified files
    if ".min." in path.name:
        return True
    return False


def detect_language(file_path: Path) -> str:
    return LANGUAGE_MAP.get(file_path.suffix.lower(), "text")


def clone_github_repo(github_url: str, dest_dir: str, token: Optional[str] = None) -> str:
    """Clone a GitHub repository to a local directory."""
    os.makedirs(dest_dir, exist_ok=True)
    if token:
        # Inject token for private repos
        url = github_url.replace("https://", f"https://{token}@")
    else:
        url = github_url
    git.Repo.clone_from(url, dest_dir, depth=1)
    return dest_dir


def extract_zip(zip_path: str, dest_dir: str) -> str:
    """Extract a ZIP archive."""
    os.makedirs(dest_dir, exist_ok=True)
    with zipfile.ZipFile(zip_path, "r") as zf:
        zf.extractall(dest_dir)
    # If there's a single root folder, return it directly
    contents = list(Path(dest_dir).iterdir())
    if len(contents) == 1 and contents[0].is_dir():
        return str(contents[0])
    return dest_dir


def get_all_code_files(repo_path: str) -> List[Path]:
    """Walk the repo and return all relevant source files."""
    repo = Path(repo_path)
    files = []
    for file_path in repo.rglob("*"):
        if not file_path.is_file():
            continue
        rel = file_path.relative_to(repo)
        if should_ignore_path(rel):
            continue
        # Skip binary files and huge files (> 500KB)
        if file_path.stat().st_size > 500_000:
            continue
        files.append(file_path)
    return files


def chunk_python_file(content: str, file_path: str) -> List[CodeChunk]:
    """Use AST to extract function/class-level chunks from Python files."""
    chunks = []
    lines = content.splitlines()
    try:
        tree = ast.parse(content)
    except SyntaxError:
        return chunk_by_lines(content, file_path, "python")

    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            start = node.lineno - 1
            end = node.end_lineno
            chunk_content = "\n".join(lines[start:end])
            chunk_type = "class" if isinstance(node, ast.ClassDef) else "function"
            chunks.append(CodeChunk(
                content=chunk_content,
                file_path=file_path,
                start_line=start + 1,
                end_line=end,
                language="python",
                chunk_type=chunk_type,
                name=node.name,
            ))

    if not chunks:
        return chunk_by_lines(content, file_path, "python")
    return chunks


def chunk_by_lines(content: str, file_path: str, language: str, chunk_size: int = 60) -> List[CodeChunk]:
    """Generic line-based chunking with overlap."""
    lines = content.splitlines()
    chunks = []
    overlap = 10
    i = 0
    while i < len(lines):
        end = min(i + chunk_size, len(lines))
        chunk_content = "\n".join(lines[i:end])
        if chunk_content.strip():
            chunks.append(CodeChunk(
                content=chunk_content,
                file_path=file_path,
                start_line=i + 1,
                end_line=end,
                language=language,
                chunk_type="block",
            ))
        i = end - overlap if end < len(lines) else end
    return chunks


def extract_js_ts_chunks(content: str, file_path: str, language: str) -> List[CodeChunk]:
    """Extract function/class blocks from JS/TS using regex."""
    chunks = []
    lines = content.splitlines()

    # Match function declarations, arrow functions, and classes
    patterns = [
        r"^\s*(export\s+)?(default\s+)?(async\s+)?function\s+(\w+)",
        r"^\s*(export\s+)?(const|let|var)\s+(\w+)\s*=\s*(async\s+)?\(",
        r"^\s*(export\s+)?(default\s+)?class\s+(\w+)",
    ]

    func_starts = []
    for i, line in enumerate(lines):
        for pat in patterns:
            if re.match(pat, line):
                func_starts.append(i)
                break

    if not func_starts:
        return chunk_by_lines(content, file_path, language)

    for idx, start in enumerate(func_starts):
        end = func_starts[idx + 1] if idx + 1 < len(func_starts) else len(lines)
        chunk_content = "\n".join(lines[start:end]).strip()
        if chunk_content:
            chunks.append(CodeChunk(
                content=chunk_content,
                file_path=file_path,
                start_line=start + 1,
                end_line=end,
                language=language,
                chunk_type="function",
            ))
    return chunks


def chunk_file(file_path: Path, repo_root: str) -> List[CodeChunk]:
    """Main dispatcher: chunk a file into meaningful code segments."""
    language = detect_language(file_path)
    rel_path = str(file_path.relative_to(repo_root)).replace("\\", "/")
    try:
        content = file_path.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return []

    if not content.strip():
        return []

    if language == "python":
        return chunk_python_file(content, rel_path)
    elif language in ("javascript", "typescript"):
        return extract_js_ts_chunks(content, rel_path, language)
    else:
        return chunk_by_lines(content, rel_path, language)


def get_language_stats(chunks: List[CodeChunk]) -> Dict[str, int]:
    stats: Dict[str, int] = {}
    for chunk in chunks:
        lang = chunk.language
        stats[lang] = stats.get(lang, 0) + 1
    return stats


def ingest_repository(repo_path: str) -> Tuple[List[CodeChunk], Dict]:
    """Full ingestion pipeline: walk files → chunk → return stats."""
    files = get_all_code_files(repo_path)
    all_chunks: List[CodeChunk] = []
    for f in files:
        chunks = chunk_file(f, repo_path)
        all_chunks.extend(chunks)

    stats = {
        "file_count": len(files),
        "chunk_count": len(all_chunks),
        "language_stats": get_language_stats(all_chunks),
    }
    return all_chunks, stats
