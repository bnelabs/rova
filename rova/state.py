"""Chat state and related data classes."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

DEFAULT_MODEL = "gemma-4-12b-it"
DEFAULT_CONTEXT_TOKENS = 262144
VALID_PROFILES = {
    "simple",
    "strict_json",
    "coding",
    "complex_reasoning",
    "long_context_qa",
    "tool_agent",
    "creative",
}
VALID_QUALITIES = {"fast", "balanced", "best"}


@dataclass
class ChatState:
    profile: str | None = None
    rag: bool | None = None
    quality: str | None = None
    max_tokens: int | None = None
    json_mode: bool = False
    skills_dir: Path = field(default_factory=lambda: Path("skills"))
    active_skills: list[str] = field(default_factory=list)
    context_tokens: int = DEFAULT_CONTEXT_TOKENS
    history: list[dict[str, str]] = field(default_factory=list)


@dataclass(frozen=True)
class ChatResult:
    content: str
    wall_seconds: float
    prompt_tps: float | None
    generation_tps: float | None
    raw: dict[str, Any]
    tool_calls: list[dict[str, Any]] = field(default_factory=list)


@dataclass(frozen=True)
class TokenUsage:
    used_tokens: int
    context_tokens: int

    @property
    def percent(self) -> float:
        if self.context_tokens <= 0:
            return 0.0
        return min(100.0, (self.used_tokens / self.context_tokens) * 100)


def token_usage(state: ChatState) -> TokenUsage:
    from rova.skills import get_skill_messages
    texts: list[str] = []
    for msg in get_skill_messages(state.skills_dir, state.active_skills):
        texts.append(msg.get("content", ""))
    texts.extend(str(message.get("content", "")) for message in state.history)
    return TokenUsage(
        used_tokens=sum(estimate_tokens(text) for text in texts),
        context_tokens=state.context_tokens,
    )


def estimate_tokens(text: str) -> int:
    if not text:
        return 0
    pieces = re.findall(r"\w+|[^\w\s]", text, flags=re.UNICODE)
    return max(1, len(pieces))
