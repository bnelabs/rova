"""Local tool executor — runs tools on the client side."""

from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path
from typing import Any

import httpx


def execute_tool_call(
    call: dict[str, Any],
    workspace_dir: Path,
) -> dict[str, Any]:
    """Execute a single tool call locally and return a tool result message."""
    function = call.get("function") or {}
    name = function.get("name")
    raw_arguments = function.get("arguments") or "{}"
    arguments = (
        json.loads(raw_arguments) if isinstance(raw_arguments, str) else raw_arguments
    )

    if name == "execute_python":
        result = execute_python(arguments, workspace_dir)
    elif name == "write_file":
        result = write_file(arguments, workspace_dir)
    elif name == "read_file":
        result = read_file(arguments, workspace_dir)
    elif name == "list_files":
        result = list_files(arguments, workspace_dir)
    elif name == "web_search":
        result = web_search(arguments)
    elif name == "web_fetch":
        result = web_fetch(arguments)
    else:
        result = f"unknown tool: {name}"

    return {
        "role": "tool",
        "tool_call_id": call.get("id", ""),
        "name": name,
        "content": result if isinstance(result, str) else json.dumps(result, sort_keys=True),
    }


# -- Python execution ---------------------------------------------------

def execute_python(arguments: dict[str, Any], workspace_dir: Path) -> str:
    code = arguments.get("code", "")
    try:
        result = subprocess.run(
            ["python3", "-c", code],
            capture_output=True,
            text=True,
            timeout=30,
            cwd=str(workspace_dir),
        )
        return result.stdout if result.returncode == 0 else result.stderr
    except subprocess.TimeoutExpired:
        return "error: execution timed out (30s)"
    except Exception as e:
        return str(e)


# -- File operations ----------------------------------------------------

def write_file(arguments: dict[str, Any], workspace_dir: Path) -> str:
    path = arguments.get("path", "")
    content = arguments.get("content", "")
    try:
        file_path = _resolve_path(path, workspace_dir)
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(content, encoding="utf-8")
        return f"wrote {len(content)} bytes to {file_path}"
    except Exception as e:
        return str(e)


def read_file(arguments: dict[str, Any], workspace_dir: Path) -> str:
    path = arguments.get("path", "")
    try:
        file_path = _resolve_path(path, workspace_dir)
        return file_path.read_text(encoding="utf-8")
    except Exception as e:
        return str(e)


def list_files(arguments: dict[str, Any], workspace_dir: Path) -> str:
    path = arguments.get("path", ".")
    try:
        target = _resolve_path(path, workspace_dir)
        if not target.exists():
            return f"path not found: {target}"
        entries = []
        for f in sorted(target.iterdir()):
            kind = "dir" if f.is_dir() else "file"
            size = f.stat().st_size
            entries.append(f"{f.name} ({kind}, {size} bytes)")
        return "\n".join(entries) if entries else "empty directory"
    except Exception as e:
        return str(e)


def _resolve_path(path: str, workspace_dir: Path) -> Path:
    p = Path(path)
    if p.is_absolute():
        return p
    return (workspace_dir / p).resolve()


# -- Web tools ----------------------------------------------------------

def web_search(arguments: dict[str, Any]) -> str:
    """Search the web using DuckDuckGo HTML (no API key required)."""
    query = arguments.get("query", "")
    if not query:
        return "error: query is required"

    try:
        response = httpx.get(
            "https://html.duckduckgo.com/html/",
            params={"q": query},
            timeout=15.0,
            headers={"User-Agent": "rova/0.2.0"},
            follow_redirects=True,
        )
        response.raise_for_status()
        results = _parse_ddg_results(response.text)
        if not results:
            return f"no results found for: {query}"
        return json.dumps(results, indent=2, ensure_ascii=False)
    except httpx.HTTPError as e:
        return f"search error: {e}"
    except Exception as e:
        return f"search error: {e}"


def web_fetch(arguments: dict[str, Any]) -> str:
    """Fetch a URL and return its text content (HTML tags stripped)."""
    url = arguments.get("url", "")
    max_length = arguments.get("max_length", 8000)
    if not url:
        return "error: url is required"

    try:
        response = httpx.get(
            url,
            timeout=15.0,
            headers={"User-Agent": "rova/0.2.0"},
            follow_redirects=True,
        )
        response.raise_for_status()
        text = _strip_html(response.text)
        if len(text) > max_length:
            text = text[:max_length] + f"\n... (truncated, original: {len(text)} chars)"
        return text
    except httpx.HTTPError as e:
        return f"fetch error: {e}"
    except Exception as e:
        return f"fetch error: {e}"


def _parse_ddg_results(html: str) -> list[dict[str, str]]:
    """Extract search results from DuckDuckGo HTML response."""
    results: list[dict[str, str]] = []
    # DDG HTML results are in <a class="result__a"> for titles
    # and <a class="result__snippet"> for snippets
    title_pattern = re.compile(
        r'<a[^>]*class="result__a"[^>]*>(.*?)</a>', re.DOTALL | re.IGNORECASE
    )
    snippet_pattern = re.compile(
        r'<a[^>]*class="result__snippet"[^>]*>(.*?)</a>', re.DOTALL | re.IGNORECASE
    )
    url_pattern = re.compile(
        r'<a[^>]*class="result__url"[^>]*>(.*?)</a>', re.DOTALL | re.IGNORECASE
    )

    titles = title_pattern.findall(html)
    snippets = snippet_pattern.findall(html)
    urls = url_pattern.findall(html)

    for i, title in enumerate(titles[:10]):
        results.append({
            "title": _clean_html(title),
            "url": _clean_html(urls[i]) if i < len(urls) else "",
            "snippet": _clean_html(snippets[i]) if i < len(snippets) else "",
        })

    return results


def _strip_html(html: str) -> str:
    """Strip HTML tags and return plain text."""
    # Remove scripts and styles
    text = re.sub(r'<script[^>]*>.*?</script>', '', html, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r'<style[^>]*>.*?</style>', '', text, flags=re.DOTALL | re.IGNORECASE)
    # Replace common block elements with newlines
    text = re.sub(r'</?(?:div|p|br|li|h[1-6]|tr|article|section)[^>]*>', '\n', text, flags=re.IGNORECASE)
    # Remove all remaining HTML tags
    text = re.sub(r'<[^>]+>', '', text)
    # Decode HTML entities
    text = text.replace('&amp;', '&').replace('&lt;', '<').replace('&gt;', '>')
    text = text.replace('&quot;', '"').replace('&#x27;', "'").replace('&nbsp;', ' ')
    # Collapse whitespace
    text = re.sub(r'\n\s*\n', '\n\n', text)
    text = re.sub(r'[ \t]+', ' ', text)
    return text.strip()


def _clean_html(text: str) -> str:
    """Remove HTML tags from a short snippet."""
    text = re.sub(r'<[^>]+>', '', text)
    text = text.replace('&amp;', '&').replace('&lt;', '<').replace('&gt;', '>')
    text = text.replace('&quot;', '"').replace('&#x27;', "'").replace('&nbsp;', ' ')
    return text.strip()


# -- Tool definitions (JSON Schema for the LLM) -------------------------

TOOL_DEFINITIONS: list[dict[str, Any]] = [
    {
        "type": "function",
        "function": {
            "name": "execute_python",
            "description": "Execute Python code and return stdout or stderr.",
            "parameters": {
                "type": "object",
                "properties": {
                    "code": {
                        "type": "string",
                        "description": "Python source code to execute.",
                    },
                },
                "required": ["code"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "write_file",
            "description": "Write content to a file in the workspace.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "File path (relative to workspace or absolute).",
                    },
                    "content": {
                        "type": "string",
                        "description": "File content to write.",
                    },
                },
                "required": ["path", "content"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "Read the contents of a file.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "File path to read.",
                    },
                },
                "required": ["path"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "list_files",
            "description": "List files in a directory.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Directory path to list (default: workspace root).",
                    },
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "web_search",
            "description": "Search the web and return results with titles, URLs, and snippets.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search query string.",
                    },
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "web_fetch",
            "description": "Fetch a URL and return its text content (HTML tags removed).",
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {
                        "type": "string",
                        "description": "URL to fetch.",
                    },
                    "max_length": {
                        "type": "integer",
                        "description": "Maximum characters to return (default: 8000).",
                    },
                },
                "required": ["url"],
            },
        },
    },
]
