import pytest
from pathlib import Path
from rova.state import ChatState, token_usage
from rova.skills import get_skill_messages

def test_token_usage_with_skills(tmp_path):
    skills_dir = tmp_path / "skills"
    skills_dir.mkdir()
    (skills_dir / "python_expert.md").write_text("Expert in Python programming.")

    state = ChatState(
        skills_dir=skills_dir,
        active_skills=["python_expert"],
        history=[{"role": "user", "content": "help me"}]
    )

    usage = token_usage(state)
    # "Active" (1) "skill" (2) ":" (3) "python_expert" (4)
    # "Expert" (5) "in" (6) "Python" (7) "programming" (8) "." (9)
    # "help" (10) "me" (11)
    # Total 11.
    assert usage.used_tokens == 11

def test_get_skill_messages(tmp_path):
    skills_dir = tmp_path / "skills"
    skills_dir.mkdir()
    (skills_dir / "test_skill.md").write_text("Test content")

    msgs = get_skill_messages(skills_dir, ["test_skill"])
    assert len(msgs) == 1
    assert msgs[0]["role"] == "system"
    assert "Test content" in msgs[0]["content"]
