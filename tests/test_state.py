import pytest
from pathlib import Path
from rova.state import ChatState, estimate_tokens, token_usage

def test_estimate_tokens():
    assert estimate_tokens("hello world") == 2
    assert estimate_tokens("") == 0
    assert estimate_tokens("hello, world!") == 4

def test_chat_state_init():
    state = ChatState()
    assert state.profile is None
    assert state.history == []
    assert state.active_skills == []

def test_token_usage_basic():
    state = ChatState(history=[
        {"role": "user", "content": "hello"},
        {"role": "assistant", "content": "hi there"}
    ])
    usage = token_usage(state)
    assert usage.used_tokens == 3 # "hello" (1) + "hi" "there" (2)
    assert usage.percent > 0
