"""Skill file management — load and parameterize skill files."""

from __future__ import annotations

from pathlib import Path


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
