import os
from dotenv import load_dotenv

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# 自动加载项目根目录的 .env 文件
load_dotenv(os.path.join(BASE_DIR, ".env"))

DATA_DIR = os.path.join(BASE_DIR, "data")
REPOS_DIR = os.path.join(DATA_DIR, "repos")
DB_PATH = os.path.join(DATA_DIR, "cache.db")

DEEPSEEK_API_KEY = os.environ.get("DEEPSEEK_API_KEY", "")
DEEPSEEK_BASE_URL = "https://api.deepseek.com"
DEEPSEEK_MODEL = "deepseek-v4-pro"

MAX_FILE_SIZE_BYTES = 500 * 1024
MAX_FILES_TO_ANALYZE = 80

IGNORED_DIRS = {
    ".git", "node_modules", "__pycache__", ".venv", "venv",
    "target", "build", "dist", ".next", ".nuxt", "vendor",
    ".idea", ".vscode", ".gradle", "coverage", ".tox",
    "egg-info", ".eggs", ".mypy_cache", ".pytest_cache",
}

IGNORED_EXTENSIONS = {
    ".png", ".jpg", ".jpeg", ".gif", ".ico", ".svg", ".webp",
    ".woff", ".woff2", ".ttf", ".eot", ".otf",
    ".mp3", ".mp4", ".avi", ".mov", ".mkv",
    ".zip", ".tar", ".gz", ".bz2", ".7z", ".rar",
    ".pdf", ".doc", ".docx", ".xls", ".xlsx",
    ".pyc", ".pyo", ".class", ".o", ".so", ".dll", ".exe",
    ".lock", ".sum", ".map",
}
