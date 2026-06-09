"""Scrollable chat history widget with rich formatting."""

from __future__ import annotations

from textual.containers import VerticalScroll
from textual.widgets import Static
from rich.markdown import Markdown
from rich.text import Text
from rich.panel import Panel


class ChatView(VerticalScroll):
    """A scrollable chat history rendered with Rich formatting."""

    def add_user(self, text: str) -> None:
        panel = Panel(
            Text(text, style="bold"),
            title="YOU",
            border_style="blue",
            padding=(0, 1),
        )
        self.mount(Static(panel))
        self.scroll_end()

    def add_assistant(self, text: str, wall_seconds: float | None = None) -> None:
        if not text:
            self.mount(Static(Panel("(empty response)", title="ASSISTANT", border_style="yellow")))
            self.scroll_end()
            return
        markdown = Markdown(text, code_theme="monokai")
        timing = f"\n[dim][wall={wall_seconds:.2f}s][/dim]" if wall_seconds is not None else ""
        content = Panel(
            markdown,
            title="ASSISTANT",
            border_style="green",
            padding=(0, 1),
            subtitle=timing,
        )
        self.mount(Static(content))
        self.scroll_end()

    def start_assistant_stream(self) -> Static:
        """Start a new assistant message for streaming."""
        widget = Static("ASSISTANT: ", classes="assistant-stream")
        self.mount(widget)
        self.scroll_end()
        return widget

    def append_assistant(self, widget: Static, text: str) -> None:
        """Append text to an existing streaming assistant widget."""
        widget.update(str(widget.renderable) + text)
        self.scroll_end()

    def add_system(self, text: str) -> None:
        self.mount(Static(Panel(text, title="ROVA", border_style="magenta", padding=(0, 1))))
        self.scroll_end()

    def add_error(self, text: str) -> None:
        self.mount(Static(Panel(text, title="ERROR", border_style="red", padding=(0, 1))))
        self.scroll_end()

    def add_tool_call(self, name: str, args: str) -> None:
        content = f"[bold yellow]🔧 {name}[/bold yellow]\n[dim]{args}[/dim]"
        self.mount(Static(Panel(content, title="TOOL CALL", border_style="yellow", padding=(0, 1))))
        self.scroll_end()

    def add_tool_result(self, result: str) -> None:
        preview = result[:500] + ("…" if len(result) > 500 else "")
        self.mount(
            Static(Panel(
                preview,
                title="TOOL RESULT",
                border_style="cyan",
                padding=(0, 1),
            ))
        )
        self.scroll_end()
