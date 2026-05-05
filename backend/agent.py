import os
import json
import asyncio
from typing import AsyncIterator
from langchain.agents import create_agent
from langchain_openai import ChatOpenAI
from langchain.tools import tool
from langchain.messages import HumanMessage, AIMessage

from config import (
    DEEPSEEK_API_KEY, DEEPSEEK_BASE_URL, DEEPSEEK_MODEL,
)
from git_utils import (
    read_file_content, search_in_files, get_file_tree,
    get_key_files, get_repo_dir
)

_current_repo_dir: str = ""


def set_current_repo(repo_dir: str):
    global _current_repo_dir
    _current_repo_dir = repo_dir


class MissingAPIKeyError(Exception):
    pass


def _check_api_key():
    if not DEEPSEEK_API_KEY:
        raise MissingAPIKeyError(
            "DEEPSEEK_API_KEY 环境变量未设置。请在 .env 文件中配置后重试。\n"
            "获取 API Key: https://platform.deepseek.com/"
        )


def _create_model(temperature=0.3, max_tokens=4096):
    _check_api_key()
    return ChatOpenAI(
        model=DEEPSEEK_MODEL,
        openai_api_key=DEEPSEEK_API_KEY,
        openai_api_base=DEEPSEEK_BASE_URL,
        temperature=temperature,
        max_tokens=max_tokens,
        model_kwargs={"extra_body": {"thinking": {"type": "disabled"}}},
    )


@tool
def tool_read_file(path: str) -> str:
    """Read the full content of a file in the project.
    Provide a relative path like 'src/main.py' or 'README.md'."""
    return read_file_content(_current_repo_dir, path)


@tool
def tool_search_code(pattern: str, glob_pattern: str = "*") -> str:
    """Search for code patterns using regex in the project files.
    Specify a glob_pattern like '*.py' or '*.js' to filter file types."""
    return search_in_files(_current_repo_dir, pattern, glob_pattern)


@tool
def tool_list_directory(path: str = "") -> str:
    """List files and subdirectories in a given directory of the project.
    Use '' or '.' for the root directory."""
    import os as _os
    target = _current_repo_dir
    if path and path not in ("", "."):
        target = _os.path.normpath(_os.path.join(_current_repo_dir, path))
        if not target.startswith(_os.path.normpath(_current_repo_dir)):
            return "[Error: path traversal denied]"
    try:
        items = _os.listdir(target)
        result = []
        for name in sorted(items):
            full = _os.path.join(target, name)
            prefix = "[D] " if _os.path.isdir(full) else "[F] "
            result.append(prefix + name)
        return "\n".join(result[:60])
    except Exception as e:
        return f"[Error: {e}]"


@tool
def tool_get_tree() -> str:
    """Get the full directory tree of the project."""
    tree = get_file_tree(_current_repo_dir)
    return _format_tree(tree)


@tool
def tool_get_key_files() -> str:
    """Get a list of key files worth analyzing in the project."""
    return "\n".join(get_key_files(_current_repo_dir))


_tool_labels = {
    "tool_read_file": "📖 正在读取文件",
    "tool_search_code": "🔍 正在搜索代码",
    "tool_list_directory": "📂 正在浏览目录",
    "tool_get_tree": "🌲 正在生成目录树",
    "tool_get_key_files": "🔑 正在识别关键文件",
    "read_file": "📖 正在读取",
    "search_code": "🔍 正在搜索",
    "list_directory": "📂 正在浏览",
    "get_tree": "🌲 正在生成树",
    "get_key_files": "🔑 正在识别",
}


def _tool_action_name(name: str) -> str:
    return _tool_labels.get(name, f"🤖 正在执行: {name}")


def _format_tree(tree: dict, indent: int = 0) -> str:
    lines = []
    for name, children in tree.items():
        prefix = "  " * indent
        if name.endswith("/"):
            lines.append(f"{prefix}├── {name}")
            if children:
                lines.append(_format_tree(children, indent + 1))
        else:
            lines.append(f"{prefix}├── {name}")
    return "\n".join(lines)


def create_analysis_agent():
    model = _create_model(temperature=0.3, max_tokens=8192)
    return create_agent(
        model=model,
        tools=[tool_read_file, tool_search_code, tool_list_directory,
               tool_get_tree, tool_get_key_files],
        system_prompt="""You are an expert software engineer analyzing an open-source project.
Your goal is to understand the project deeply and produce a comprehensive, beginner-friendly analysis.

Use the available tools to explore the codebase:
1. Start with tool_get_tree() to see the project structure
2. Read key files like README.md, package.json, setup.py, etc.
3. Explore main source directories
4. Search for important patterns (main functions, class definitions, routes, etc.)

Be thorough but efficient. When you've gathered enough information, produce a complete analysis report.""",
    )


def create_qa_agent():
    model = _create_model(temperature=0.3, max_tokens=4096)
    return create_agent(
        model=model,
        tools=[tool_read_file, tool_search_code, tool_list_directory,
               tool_get_tree],
        system_prompt="""You are an expert software engineer helping a user understand a codebase.
Answer questions about the project clearly and thoroughly.

Use the available tools to find relevant code:
- tool_read_file: Read specific files
- tool_search_code: Search for patterns in code
- tool_list_directory: Browse directory contents
- tool_get_tree: View project structure

When answering:
1. Find the relevant code using the tools
2. Explain the code in simple terms
3. Show code snippets with file paths
4. Connect related pieces of code

Be patient and thorough. The user may be new to programming.""",
    )


async def run_analysis_stream(repo_dir: str) -> AsyncIterator[dict]:
    set_current_repo(repo_dir)

    yield {"step": "start", "status": "running", "message": "开始分析项目..."}

    yield {"step": "tree", "status": "running", "message": "正在生成目录树..."}
    tree = get_file_tree(repo_dir)
    yield {"step": "tree", "status": "done", "message": "目录树生成完成",
           "data": tree}

    yield {"step": "key_files", "status": "running", "message": "正在识别关键文件..."}
    key_files = get_key_files(repo_dir)
    yield {"step": "key_files", "status": "done",
           "message": f"识别到 {len(key_files)} 个关键文件",
           "data": key_files}

    yield {"step": "analysis", "status": "running",
           "message": "正在使用 AI 深度分析源码..."}

    agent = create_analysis_agent()

    analysis_prompt = f"""Please analyze this project thoroughly and produce a report in Chinese.

The project directory tree has been explored. Key files identified:
{chr(10).join(key_files[:30])}

Please use the tools to explore the project, then generate a comprehensive analysis report with the following sections (use Chinese, keep code terms in English):

## 项目概述
Brief description of what this project does, who it's for.

## 技术栈
List all technologies, frameworks, languages used.

## 目录结构
Explain the directory layout and what each important directory contains.

## 核心模块
Deep dive into the most important modules/components and how they work.

## 数据流
How data moves through the application (API requests, database queries, state management, etc.)

## 设计模式
Any notable design patterns or architectural decisions.

## 阅读建议
Recommended reading order for newcomers to understand the codebase.

Format the report in Markdown. Be specific and cite file paths."""
    try:
        report = ""
        async for chunk in agent.astream(
            {"messages": [HumanMessage(content=analysis_prompt)]},
            stream_mode=["updates"],
            version="v2",
        ):
            # v2 chunks are (namespace, data) tuples
            data = chunk[1] if isinstance(chunk, tuple) else chunk.get("data", chunk)
            for source, update in data.items():
                last_msg = update.get("messages", [None])[-1]
                if last_msg is None:
                    continue
                msg_type = getattr(last_msg, "type", None)
                if msg_type == "tool":
                    tool_name = getattr(last_msg, "name", "unknown")
                    action = _tool_action_name(tool_name)
                    yield {"step": "analysis", "status": "running",
                           "message": f"{action}..."}
                elif msg_type == "ai":
                    content = getattr(last_msg, "content", "")
                    if isinstance(content, str) and len(content) > len(report):
                        report = content

        if not report:
            raise RuntimeError("Agent returned empty report")

        yield {"step": "analysis", "status": "done",
               "message": "AI 分析完成", "data": report}

        yield {"step": "summary", "status": "running", "message": "正在生成总结..."}

        summary_model = _create_model(temperature=0.1, max_tokens=1024)
        summary_agent = create_agent(
            model=summary_model,
            tools=[],
            system_prompt="You extract project metadata from analysis reports. Output ONLY valid JSON.",
        )

        summary_prompt = f"""From this analysis report, extract:
1. "project_name": A concise project name
2. "tech_stack": Array of key technologies used

Report content:
{report[:5000]}

Respond with ONLY valid JSON like: {{"project_name": "...", "tech_stack": ["..."]}}"""

        summary_result = await summary_agent.ainvoke(
            {"messages": [HumanMessage(content=summary_prompt)]}
        )
        summary_text = summary_result["messages"][-1].content
        if hasattr(summary_text, '__iter__') and not isinstance(summary_text, str):
            summary_text = str(summary_text)

        try:
            start = summary_text.find("{")
            end = summary_text.rfind("}") + 1
            if start != -1 and end > start:
                metadata = json.loads(summary_text[start:end])
            else:
                raise ValueError("No JSON found")
        except (json.JSONDecodeError, ValueError):
            metadata = {
                "project_name": os.path.basename(repo_dir),
                "tech_stack": []
            }

        yield {"step": "summary", "status": "done",
               "message": "分析完成!",
               "data": {
                   "report": report,
                   "project_name": metadata.get("project_name", ""),
                   "tech_stack": metadata.get("tech_stack", []),
                   "tree": tree,
               }}

    except Exception as e:
        yield {"step": "error", "status": "error",
               "message": f"分析出错: {str(e)}"}


async def run_qa_stream(repo_dir: str, question: str,
                        chat_history: list = None) -> AsyncIterator[dict]:
    set_current_repo(repo_dir)

    agent = create_qa_agent()

    messages = []
    if chat_history:
        for msg in chat_history[-6:]:
            if msg.get("role") == "user":
                messages.append(HumanMessage(content=msg["content"]))
            else:
                messages.append(AIMessage(content=msg["content"]))
    messages.append(HumanMessage(content=question))

    try:
        for chunk in agent.stream(
            {"messages": messages},
            stream_mode=["messages", "updates"],
            version="v2",
        ):
            if chunk.get("type") == "messages":
                token, metadata = chunk["data"]
                if hasattr(token, "text") and token.text:
                    yield {"type": "text", "content": token.text}
                if hasattr(token, "tool_call_chunks") and token.tool_call_chunks:
                    for tc in token.tool_call_chunks:
                        if hasattr(tc, "name") and tc.name:
                            yield {"type": "tool_start", "content": tc.name}
            elif chunk.get("type") == "updates":
                for source, update in chunk["data"].items():
                    last_msg = update.get("messages", [None])[-1]
                    if last_msg and hasattr(last_msg, "type") and last_msg.type == "tool":
                        yield {"type": "tool_result",
                               "content": str(last_msg.content)[:200]}

        yield {"type": "done", "content": ""}
    except Exception as e:
        yield {"type": "error", "content": str(e)}
