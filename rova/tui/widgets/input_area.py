"""Input area for chat messages with slash-command palette support."""

from __future__ import annotations

from textual.widgets import Input
from textual.message import Message
from textual import events

from rova.tui.widgets.command_palette import COMMAND_DEFS


class ChatInput(Input):
    """Input widget with slash-command detection and Tab autocomplete.

    Posts:
      ChatSubmitted - when user presses Enter with non-empty text
      SlashChanged  - when the value changes while starting with /
    """

    class ChatSubmitted(Message):
        """Emitted when the user submits (Enter), carrying the trimmed text."""

        def __init__(self, value: str) -> None:
            super().__init__()
            self.value = value

    class SlashChanged(Message):
        """Emitted when the input value changes while starting with /."""

        def __init__(self, value: str) -> None:
            super().__init__()
            self.value = value

    def __init__(self, **kwargs) -> None:
        super().__init__(
            placeholder="Type a message or / for commands…",
            **kwargs,
        )

    # -- Submit ----------------------------------------------------------

    def action_submit(self) -> None:
        """Intercept Textual's default submit to emit our custom message."""
        value = self.value
        if value.strip():
            self.post_message(self.ChatSubmitted(value))
        self.clear()

    # -- Slash detection -------------------------------------------------

    def watch_value(self, value: str) -> None:
        """Called by Textual whenever the input value changes."""
        if value.startswith("/"):
            self.post_message(self.SlashChanged(value))
        else:
            self.post_message(self.SlashChanged(""))

    # -- Tab autocomplete ------------------------------------------------

    def action_focus_next(self) -> None:
        """Override Tab: autocomplete when in slash mode, else move focus."""
        if self.value.startswith("/"):
            match = _best_match(self.value)
            if match:
                self.value = match
                self.cursor_position = len(match)
                self.post_message(self.SlashChanged(match))
        else:
            # Delegate to the screen-level focus-next behavior
            self.screen.action_focus_next()


def _best_match(partial: str) -> str | None:
    """Return the best autocomplete match for a partial slash command."""
    prefix = partial.lower()
    candidates = [
        cmd for cmd, _usage, _desc in COMMAND_DEFS
        if cmd.lower().startswith(prefix)
    ]
    if not candidates:
        candidates = [
            cmd for cmd, _usage, _desc in COMMAND_DEFS
            if prefix.lstrip("/") in cmd.lower()
        ]
    if not candidates:
        return None

    # Return the shortest exact prefix match, or the first candidate
    exact = [c for c in candidates if c.lower().startswith(prefix)]
    candidate = (exact or candidates)[0]

    # If there's a single candidate, add a trailing space
    if len(exact or candidates) == 1:
        return candidate + " "
    return candidate
