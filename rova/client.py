"""HTTP client for llama-router API — sync and async support."""

from __future__ import annotations

import json
import time
from typing import Any, AsyncGenerator

import httpx

from rova.state import (
    DEFAULT_MODEL,
    ChatResult,
    ChatState,
)


def _metadata_from_state(state: ChatState) -> dict[str, Any]:
    metadata: dict[str, Any] = {}
    if state.profile:
        metadata["profile"] = state.profile
    if state.rag is not None:
        metadata["rag"] = state.rag
    if state.quality:
        metadata["quality"] = state.quality
    return metadata


def _extract_assistant_content(raw: dict[str, Any]) -> str:
    choices = raw.get("choices") or []
    if not choices:
        return ""
    message = choices[0].get("message") or {}
    content = message.get("content", "")
    if isinstance(content, str):
        return content.strip()
    return str(content).strip()


def _extract_tool_calls(raw: dict[str, Any]) -> list[dict[str, Any]]:
    choices = raw.get("choices") or []
    if not choices:
        return []
    message = choices[0].get("message") or {}
    calls = message.get("tool_calls") or []
    return [call for call in calls if isinstance(call, dict)]


def _maybe_float(value: Any) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _build_payload(message: str, state: ChatState, tools: list[dict[str, Any]] | None = None, stream: bool = False) -> dict[str, Any]:
    """Build the request payload for a chat completion."""
    from rova.skills import get_skill_messages
    messages = [*get_skill_messages(state.skills_dir, state.active_skills), *state.history, {"role": "user", "content": message}]
    payload: dict[str, Any] = {
        "model": DEFAULT_MODEL,
        "messages": messages,
        "stream": stream,
    }
    metadata = _metadata_from_state(state)
    if metadata:
        payload["metadata"] = metadata
    if state.max_tokens is not None:
        payload["max_tokens"] = state.max_tokens
    if state.json_mode:
        payload["response_format"] = {"type": "json_object"}
    if tools:
        payload["tools"] = tools
        payload["tool_choice"] = "auto"
    return payload


def _parse_response(raw: dict[str, Any], started: float) -> ChatResult:
    """Parse an API response into a ChatResult."""
    wall_seconds = time.perf_counter() - started
    content = _extract_assistant_content(raw)
    tool_calls = _extract_tool_calls(raw)
    timings = raw.get("timings") or {}
    return ChatResult(
        content=content,
        wall_seconds=wall_seconds,
        prompt_tps=_maybe_float(timings.get("prompt_per_second")),
        generation_tps=_maybe_float(timings.get("predicted_per_second")),
        raw=raw,
        tool_calls=tool_calls,
    )


class RouterClient:
    """HTTP client for the llama-router API.

    Supports both sync (for non-interactive use) and async (for TUI use).
    """

    def __init__(
        self,
        base_url: str = "http://127.0.0.1:8010",
        timeout: float = 300.0,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    # -- Sync API (for CLI subcommands) -----------------------------------

    def health(self) -> dict[str, Any]:
        response = httpx.get(f"{self.base_url}/health", timeout=10.0)
        response.raise_for_status()
        return response.json()

    def profiles(self) -> dict[str, Any]:
        response = httpx.get(f"{self.base_url}/profiles", timeout=10.0)
        response.raise_for_status()
        return response.json()

    def ingest(self, paths: list[str] | None = None, urls: list[str] | None = None) -> dict[str, Any]:
        payload: dict[str, Any] = {"paths": paths or [], "urls": urls or []}
        response = httpx.post(f"{self.base_url}/rag/ingest", json=payload, timeout=self.timeout)
        response.raise_for_status()
        return response.json()

    def search(self, query: str, top_k: int = 5) -> dict[str, Any]:
        response = httpx.post(
            f"{self.base_url}/rag/search",
            json={"query": query, "top_k": top_k},
            timeout=self.timeout,
        )
        response.raise_for_status()
        return response.json()

    def send(
        self,
        message: str,
        state: ChatState,
        tools: list[dict[str, Any]] | None = None,
    ) -> ChatResult:
        """Send a message synchronously and return the result."""
        payload = _build_payload(message, state, tools, stream=False)
        started = time.perf_counter()
        response = httpx.post(
            f"{self.base_url}/v1/chat/completions",
            json=payload,
            timeout=self.timeout,
        )
        response.raise_for_status()
        raw = response.json()
        result = _parse_response(raw, started)
        state.history.extend([
            {"role": "user", "content": message},
            {"role": "assistant", "content": result.content},
        ])
        return result

    def compact(self, state: ChatState) -> ChatResult:
        """Summarize conversation history and replace it with the summary."""
        if not state.history:
            return ChatResult(
                content="No conversation history to compact.",
                wall_seconds=0,
                prompt_tps=None,
                generation_tps=None,
                raw={},
            )
        transcript = "\n\n".join(
            f"{message['role']}: {message['content']}" for message in state.history
        )
        prompt = (
            "Compact the conversation below into a durable summary for continuing the same chat. "
            "Preserve user goals, decisions, constraints, important facts, open questions, file paths, "
            "commands, and unresolved work. Remove filler and repeated wording. Return only the summary.\n\n"
            f"{transcript}"
        )
        compact_state = ChatState(
            profile="complex_reasoning",
            quality="balanced",
            max_tokens=2048,
            skills_dir=state.skills_dir,
            context_tokens=state.context_tokens,
        )
        result = self.send(prompt, compact_state)
        state.history = [
            {"role": "system", "content": f"Conversation summary so far:\n{result.content}"}
        ]
        return result

    # -- Async API (for TUI) -----------------------------------------------

    async def async_send(
        self,
        message: str,
        state: ChatState,
        tools: list[dict[str, Any]] | None = None,
        client: httpx.AsyncClient | None = None,
    ) -> ChatResult:
        """Send a message asynchronously using an optional shared AsyncClient."""
        payload = _build_payload(message, state, tools, stream=False)
        started = time.perf_counter()

        if client is not None:
            response = await client.post(
                f"{self.base_url}/v1/chat/completions",
                json=payload,
                timeout=self.timeout,
            )
        else:
            async with httpx.AsyncClient() as ac:
                response = await ac.post(
                    f"{self.base_url}/v1/chat/completions",
                    json=payload,
                    timeout=self.timeout,
                )

        response.raise_for_status()
        raw = response.json()
        result = _parse_response(raw, started)
        state.history.extend([
            {"role": "user", "content": message},
            {"role": "assistant", "content": result.content},
        ])
        return result

    async def async_stream(
        self,
        message: str,
        state: ChatState,
        tools: list[dict[str, Any]] | None = None,
        client: httpx.AsyncClient | None = None,
    ) -> AsyncGenerator[str, None]:
        """Stream a chat completion asynchronously."""
        payload = _build_payload(message, state, tools, stream=True)

        # Internal helper to handle the request
        async def _stream_req(c: httpx.AsyncClient):
            async with c.stream(
                "POST",
                f"{self.base_url}/v1/chat/completions",
                json=payload,
                timeout=self.timeout,
            ) as response:
                response.raise_for_status()
                full_content = []
                async for line in response.aiter_lines():
                    if not line.startswith("data: "):
                        continue
                    data_str = line[6:].strip()
                    if data_str == "[DONE]":
                        break
                    try:
                        chunk = json.loads(data_str)
                        choices = chunk.get("choices") or []
                        if not choices:
                            continue
                        delta = choices[0].get("delta") or {}
                        content = delta.get("content", "")
                        if content:
                            full_content.append(content)
                            yield content
                    except json.JSONDecodeError:
                        continue

                # Update state history after stream is complete
                state.history.extend([
                    {"role": "user", "content": message},
                    {"role": "assistant", "content": "".join(full_content)},
                ])

        if client is not None:
            async for chunk in _stream_req(client):
                yield chunk
        else:
            async with httpx.AsyncClient() as ac:
                async for chunk in _stream_req(ac):
                    yield chunk

    async def async_health(self, client: httpx.AsyncClient | None = None) -> dict[str, Any]:
        if client is not None:
            response = await client.get(f"{self.base_url}/health", timeout=10.0)
        else:
            async with httpx.AsyncClient() as ac:
                response = await ac.get(f"{self.base_url}/health", timeout=10.0)
        response.raise_for_status()
        return response.json()
