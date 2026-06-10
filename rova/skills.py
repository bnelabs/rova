"""Skill file management — load and parameterize skill files."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from rova.state import ChatState


def list_skills(skills_dir: Path) -> list[str]:
    if not skills_dir.exists():
        return []
    return sorted(path.stem for path in skills_dir.glob("*.md") if path.is_file())


def read_skill(skills_dir: Path, name: str, params: dict[str, str] | None = None) -> str:
    """Read a skill file and optionally substitute {param} placeholders."""
    if "/" in name or "\\" in name or name.startswith("."):
        return ""
    path = skills_dir / f"{name}.md"
    if not path.is_file():
        return ""
    text = path.read_text(encoding="utf-8").strip()
    if params and text:
        for key, value in params.items():
            text = text.replace(f"{{{key}}}", value)
    return text


def skill_messages(state: "ChatState") -> list[dict[str, str]]:
    """Build system messages from active skills for injection into the conversation.

    This is the canonical implementation. Both client.py and state.py use this
    so skill-loading logic stays in one place.
    """
    messages: list[dict[str, str]] = []
    for name in state.active_skills:
        params = state.skill_params.get(name)
        text = read_skill(state.skills_dir, name, params)
        if text:
            messages.append({"role": "system", "content": f"Active skill: {name}\n{text}"})
    return messages
