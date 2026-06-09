"""Input area for chat messages with slash-command support."""

from __future__ import annotations

from textual.widgets import Input
from textual.message import Message


class ChatInput(Input):
    """Single-line input widget. Posts ChatSubmitted on Enter."""

    class ChatSubmitted(Message):
        """Emitted when the user submits (Enter), carrying the trimmed text."""

        def __init__(self, value: str) -> None:
            super().__init__()
            self.value = value

    def __init__(self, **kwargs) -> None:
        super().__init__(
            placeholder="Type a message or / for commands…",
            **kwargs,
        )

    def action_submit(self) -> None:
        """Intercept Textual's default submit to emit our custom message."""
        value = self.value
        if value.strip():
            self.post_message(self.ChatSubmitted(value))
        self.clear()
