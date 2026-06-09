"""Skill file management."""

from __future__ import annotations

from pathlib import Path


def list_skills(skills_dir: Path) -> list[str]:
    if not skills_dir.exists():
        return []
    return sorted(path.stem for path in skills_dir.glob("*.md") if path.is_file())


def read_skill(skills_dir: Path, name: str) -> str:
    if "/" in name or "\\" in name or name.startswith("."):
        return ""
    path = skills_dir / f"{name}.md"
    if not path.is_file():
        return ""
    return path.read_text(encoding="utf-8").strip()


def get_skill_messages(skills_dir: Path, active_skills: list[str]) -> list[dict[str, str]]:
    messages: list[dict[str, str]] = []
    for name in active_skills:
        text = read_skill(skills_dir, name)
        if text:
            messages.append({"role": "system", "content": f"Active skill: {name}\n{text}"})
    return messages
