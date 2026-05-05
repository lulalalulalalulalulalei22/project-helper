import os
import subprocess
import shutil
from urllib.parse import urlparse
from config import REPOS_DIR, IGNORED_DIRS, IGNORED_EXTENSIONS

# Windows 默认编码是 GBK，Git 输出常常含 UTF-8 字符（emoji 等）
# 统一用 UTF-8 + replace，防止 UnicodeDecodeError 导致 subprocess 线程崩溃
_SUBPROCESS_KW = {"encoding": "utf-8", "errors": "replace", "text": True}


def get_repo_name(repo_url: str) -> str:
    path = urlparse(repo_url).path.rstrip("/")
    return path.split("/")[-1].replace(".git", "")


def get_repo_dir(repo_url: str) -> str:
    name = get_repo_name(repo_url)
    safe_name = "".join(c if c.isalnum() or c in "-_" else "_" for c in name)
    return os.path.join(REPOS_DIR, safe_name)


def clone_repo(repo_url: str) -> str:
    target_dir = get_repo_dir(repo_url)
    if os.path.exists(target_dir):
        try:
            shutil.rmtree(target_dir)
        except PermissionError:
            subprocess.run(["cmd", "/c", "rmdir", "/s", "/q", target_dir],
                           capture_output=True, timeout=30, **_SUBPROCESS_KW)
            if os.path.exists(target_dir):
                shutil.rmtree(target_dir, ignore_errors=True)
    subprocess.run(
        ["git", "clone", "--depth", "1", repo_url, target_dir],
        capture_output=True, timeout=300, **_SUBPROCESS_KW
    )
    return target_dir


def get_commit_hash(repo_dir: str) -> str:
    result = subprocess.run(
        ["git", "-C", repo_dir, "rev-parse", "HEAD"],
        capture_output=True, timeout=10, **_SUBPROCESS_KW
    )
    return result.stdout.strip()


def get_file_tree(repo_dir: str, max_depth: int = 4) -> dict:
    tree = {}

    def walk(dir_path: str, depth: int):
        if depth > max_depth:
            return {}
        entries = {}
        try:
            items = sorted(os.listdir(dir_path))
        except PermissionError:
            return {}

        files_count = 0
        for name in items:
            if name in IGNORED_DIRS:
                continue
            full = os.path.join(dir_path, name)
            if os.path.isdir(full):
                if files_count < 30:
                    sub = walk(full, depth + 1)
                    if sub is not None:
                        entries[name + "/"] = sub
                        files_count += 1
            else:
                ext = os.path.splitext(name)[1].lower()
                if ext not in IGNORED_EXTENSIONS and files_count < 50:
                    entries[name] = None
                    files_count += 1
        return entries if entries else {}

    tree[os.path.basename(repo_dir)] = walk(repo_dir, 1)
    return tree


def read_file_content(repo_dir: str, relative_path: str) -> str:
    full_path = os.path.normpath(os.path.join(repo_dir, relative_path))
    if not full_path.startswith(os.path.normpath(repo_dir)):
        return "[Error: path traversal denied]"
    if not os.path.isfile(full_path):
        return f"[Error: file not found: {relative_path}]"
    size = os.path.getsize(full_path)
    if size > 1024 * 1024:
        return f"[File too large: {size} bytes. Showing first 100KB]\n" + _read_head(full_path, 100 * 1024)
    try:
        with open(full_path, "r", encoding="utf-8", errors="replace") as f:
            return f.read()
    except Exception as e:
        return f"[Error reading file: {e}]"


def search_in_files(repo_dir: str, pattern: str, glob_pattern: str = "*") -> str:
    try:
        result = subprocess.run(
            ["rg", "--line-number", "--max-count=3", "--no-heading",
             "--max-filesize=500K", "-g", glob_pattern, pattern, repo_dir],
            capture_output=True, timeout=15, **_SUBPROCESS_KW
        )
        output = result.stdout.strip()
        if output:
            lines = output.split("\n")[:30]
            return "\n".join(lines)
    except FileNotFoundError:
        pass

    try:
        result = subprocess.run(
            ["grep", "-rn", "--include=" + glob_pattern, "-m", "3", pattern, repo_dir],
            capture_output=True, timeout=15, **_SUBPROCESS_KW
        )
        output = result.stdout.strip()
        if output:
            lines = output.split("\n")[:30]
            return "\n".join(lines)
    except FileNotFoundError:
        pass

    # Pure Python fallback
    import fnmatch
    import re as _re
    matches = []
    try:
        pat = _re.compile(pattern)
    except _re.error:
        pat = _re.compile(_re.escape(pattern))
    for root, dirs, files in os.walk(repo_dir):
        dirs[:] = [d for d in dirs if d not in IGNORED_DIRS]
        for fname in files:
            if not fnmatch.fnmatch(fname, glob_pattern):
                continue
            fpath = os.path.join(root, fname)
            ext = os.path.splitext(fname)[1].lower()
            if ext in IGNORED_EXTENSIONS:
                continue
            if os.path.getsize(fpath) > 500 * 1024:
                continue
            try:
                with open(fpath, "r", encoding="utf-8", errors="replace") as f:
                    for i, line in enumerate(f, 1):
                        if pat.search(line):
                            rel = os.path.relpath(fpath, repo_dir)
                            matches.append(f"{rel}:{i}:{line.rstrip()[:200]}")
                            if len(matches) >= 30:
                                break
            except Exception:
                continue
            if len(matches) >= 30:
                break
        if len(matches) >= 30:
            break
    return "\n".join(matches) if matches else f"No matches found for '{pattern}' in {glob_pattern}"


def _read_head(filepath: str, max_bytes: int) -> str:
    with open(filepath, "r", encoding="utf-8", errors="replace") as f:
        return f.read(max_bytes)


def get_key_files(repo_dir: str) -> list:
    """Identify key files for analysis."""
    candidates = [
        "README.md", "README.rst", "README", "CONTRIBUTING.md",
        "setup.py", "setup.cfg", "pyproject.toml", "Cargo.toml",
        "package.json", "go.mod", "Gemfile", "Makefile", "CMakeLists.txt",
        "Dockerfile", "docker-compose.yml", "docker-compose.yaml",
        ".env.example", "config.yaml", "config.yml", "config.json",
    ]
    key_files = []
    for f in candidates:
        fp = os.path.join(repo_dir, f)
        if os.path.isfile(fp):
            key_files.append(f)
    src_dirs = ["src", "lib", "app", "core", "pkg", "cmd", "internal",
                "main", "api", "controllers", "models", "views", "routes",
                "services", "utils", "handlers", "middleware"]
    for d in src_dirs:
        dp = os.path.join(repo_dir, d)
        if os.path.isdir(dp):
            for root, dirs, files in os.walk(dp):
                dirs[:] = [x for x in dirs if x not in IGNORED_DIRS]
                for f in files:
                    if f.endswith((".py", ".js", ".ts", ".go", ".rs", ".java",
                                   ".rb", ".php", ".c", ".cpp", ".h", ".hpp",
                                   ".vue", ".tsx", ".jsx", ".swift", ".kt")):
                        rel = os.path.relpath(os.path.join(root, f), repo_dir)
                        key_files.append(rel)
                        if len(key_files) >= 80:
                            return key_files[:80]
    return key_files[:80]


def cleanup_repo(repo_dir: str):
    if os.path.exists(repo_dir):
        shutil.rmtree(repo_dir)
