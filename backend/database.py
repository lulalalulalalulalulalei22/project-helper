import sqlite3
import json
from datetime import datetime
from config import DB_PATH


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS projects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            repo_url TEXT NOT NULL,
            commit_hash TEXT NOT NULL DEFAULT '',
            project_name TEXT NOT NULL DEFAULT '',
            tech_stack TEXT NOT NULL DEFAULT '[]',
            report TEXT NOT NULL DEFAULT '',
            tree TEXT NOT NULL DEFAULT '{}',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(repo_url, commit_hash)
        );
        CREATE TABLE IF NOT EXISTS analysis_progress (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            repo_url TEXT NOT NULL,
            step TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'pending',
            message TEXT NOT NULL DEFAULT '',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)
    conn.commit()
    conn.close()


def save_analysis(repo_url: str, commit_hash: str, project_name: str,
                  tech_stack: list, report: str, tree: dict) -> int:
    conn = get_db()
    conn.execute(
        """INSERT OR REPLACE INTO projects
           (repo_url, commit_hash, project_name, tech_stack, report, tree)
           VALUES (?, ?, ?, ?, ?, ?)""",
        (repo_url, commit_hash, project_name,
         json.dumps(tech_stack), report, json.dumps(tree))
    )
    conn.commit()
    project_id = conn.execute(
        "SELECT id FROM projects WHERE repo_url=? AND commit_hash=?",
        (repo_url, commit_hash)
    ).fetchone()[0]
    conn.close()
    return project_id


def get_cached_analysis(repo_url: str, commit_hash: str):
    conn = get_db()
    row = conn.execute(
        "SELECT * FROM projects WHERE repo_url=? AND commit_hash=?",
        (repo_url, commit_hash)
    ).fetchone()
    conn.close()
    if row:
        return dict(row)
    return None


def list_cached_projects():
    conn = get_db()
    rows = conn.execute(
        "SELECT id, repo_url, project_name, tech_stack, created_at FROM projects ORDER BY created_at DESC"
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_project_by_id(project_id: int):
    conn = get_db()
    row = conn.execute("SELECT * FROM projects WHERE id=?", (project_id,)).fetchone()
    conn.close()
    if row:
        d = dict(row)
        d["tech_stack"] = json.loads(d["tech_stack"])
        d["tree"] = json.loads(d["tree"])
        return d
    return None


def delete_project(project_id: int):
    conn = get_db()
    conn.execute("DELETE FROM projects WHERE id=?", (project_id,))
    conn.commit()
    conn.close()
