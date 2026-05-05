import os
import json
import asyncio
from typing import AsyncIterable
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from starlette.responses import StreamingResponse

from config import REPOS_DIR, DATA_DIR
from database import init_db, save_analysis, get_cached_analysis, list_cached_projects, get_project_by_id, delete_project
from git_utils import clone_repo, get_commit_hash, get_repo_dir, get_repo_name
from agent import run_analysis_stream, run_qa_stream, MissingAPIKeyError


def _sse_event(event: str, data: str) -> str:
    lines = [f"event: {event}"] if event else []
    for line in data.split("\n"):
        lines.append(f"data: {line}")
    lines.append("")
    return "\n".join(lines)


async def _with_keepalive(agen, interval: int = 10):
    try:
        while True:
            try:
                item = await asyncio.wait_for(agen.__anext__(), timeout=interval)
                yield item
            except asyncio.TimeoutError:
                yield _sse_event("progress", json.dumps(
                    {"step": "ping", "status": "running", "message": ""}
                ))
    except StopAsyncIteration:
        pass


@asynccontextmanager
async def lifespan(app: FastAPI):
    os.makedirs(REPOS_DIR, exist_ok=True)
    os.makedirs(DATA_DIR, exist_ok=True)
    init_db()
    yield


app = FastAPI(title="Project Helper", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/projects")
async def list_projects():
    projects = list_cached_projects()
    for p in projects:
        if isinstance(p.get("tech_stack"), str):
            p["tech_stack"] = json.loads(p["tech_stack"])
    return {"projects": projects}


@app.get("/api/projects/{project_id}")
async def get_project(project_id: int):
    project = get_project_by_id(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


@app.delete("/api/projects/{project_id}")
async def remove_project(project_id: int):
    delete_project(project_id)
    return {"ok": True}


@app.get("/api/analyze")
async def analyze_repo(
    repo_url: str = Query(..., description="GitHub repository URL"),
    force: bool = Query(False, description="Force re-analysis"),
):
    repo_url = repo_url.strip().rstrip("/")
    repo_dir = get_repo_dir(repo_url)

    async def event_stream():
        commit = ""
        try:
            from agent import _check_api_key
            _check_api_key()

            yield _sse_event("progress", json.dumps(
                {"step": "clone", "status": "running", "message": f"正在克隆 {repo_url}..."},
                ensure_ascii=False
            ))

            clone_repo(repo_url)
            commit = get_commit_hash(repo_dir)

            if not force:
                cached = get_cached_analysis(repo_url, commit)
                if cached:
                    cached["tech_stack"] = (
                        json.loads(cached["tech_stack"])
                        if isinstance(cached.get("tech_stack"), str)
                        else cached.get("tech_stack", [])
                    )
                    cached["tree"] = (
                        json.loads(cached["tree"])
                        if isinstance(cached.get("tree"), str)
                        else cached.get("tree", {})
                    )
                    yield _sse_event("progress", json.dumps(
                        {"step": "cached", "status": "done",
                         "message": "该版本已分析过，直接加载缓存!",
                         "data": cached},
                        ensure_ascii=False
                    ))
                    yield _sse_event("done", json.dumps({"project_id": cached["id"]}))
                    return

            yield _sse_event("progress", json.dumps(
                {"step": "clone", "status": "done", "message": "代码克隆完成"},
                ensure_ascii=False
            ))

            project_name = get_repo_name(repo_url)
            project_id = None

            async for progress in run_analysis_stream(repo_dir):
                if progress.get("step") == "summary" and progress.get("status") == "done":
                    data = progress.get("data", {})
                    report = data.get("report", "")
                    tech_stack = data.get("tech_stack", [])
                    tree = data.get("tree", {})
                    pname = data.get("project_name", project_name)
                    project_id = save_analysis(
                        repo_url=repo_url, commit_hash=commit,
                        project_name=pname, tech_stack=tech_stack,
                        report=report, tree=tree,
                    )
                    progress["data"]["project_id"] = project_id
                yield _sse_event("progress", json.dumps(progress, ensure_ascii=False))

            yield _sse_event("done", json.dumps({"project_id": project_id}))

        except Exception as e:
            yield _sse_event("error", json.dumps({"message": str(e)}, ensure_ascii=False))

    return StreamingResponse(
        _with_keepalive(event_stream()),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
        },
    )


@app.get("/api/chat")
async def chat_with_project(
    project_id: int = Query(..., description="Project ID"),
    question: str = Query(..., description="User question"),
):
    project = get_project_by_id(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    repo_dir = get_repo_dir(project["repo_url"])
    if not os.path.exists(repo_dir):
        clone_repo(project["repo_url"])

    async def chat_stream():
        try:
            async for chunk in run_qa_stream(repo_dir, question):
                yield _sse_event("chat", json.dumps(chunk, ensure_ascii=False))
        except Exception as e:
            yield _sse_event("error", json.dumps({"message": str(e)}, ensure_ascii=False))

    return StreamingResponse(
        _with_keepalive(chat_stream()),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
        },
    )


@app.get("/api/health")
async def health_check():
    return {"status": "ok", "model": "deepseek-v4-pro"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
