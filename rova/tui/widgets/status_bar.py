"""Bottom status bar showing profile, RAG, quality, and context usage."""

from __future__ import annotations

from textual.widgets import Static

from rova.state import ChatState, TokenUsage


class StatusBarWidget(Static):
    """Footer bar showing current settings, context usage, and busy state."""

    def __init__(self, **kwargs) -> None:
        super().__init__("", **kwargs)
        self._busy: bool = False
        self._saved_status: str = ""

    def update_status(self, state: ChatState, usage: TokenUsage) -> None:
        if self._busy:
            self._saved_status = self._render_status_line(state, usage)
            return
        self._saved_status = ""
        self.update(self._render_status_line(state, usage))

    def set_busy(self, text: str) -> None:
        """Show a busy/loading indicator (e.g. tool execution, API call)."""
        self._busy = True
        spinner = "⏳"
        if "Executing" in text or "Running" in text:
            spinner = "🔧"
        elif "Searching" in text or "Fetching" in text:
            spinner = "🔍"
        elif "Generating" in text or "Waiting" in text:
            spinner = "⏳"
        elif "Reading" in text or "Writing" in text:
            spinner = "📄"
        self.update(f"[bold #f9e2af]{spinner} {text}[/bold #f9e2af]")

    def clear_busy(self) -> None:
        """Clear busy indicator and restore saved status."""
        self._busy = False
        if self._saved_status:
            self.update(self._saved_status)
            self._saved_status = ""

    @staticmethod
    def _render_status_line(state: ChatState, usage: TokenUsage) -> str:
        profile = state.profile or "auto"
        rag = "rag" if state.rag else "no-rag"
        skills = f"+{len(state.active_skills)} skill" if state.active_skills else "plain"
        ctx_line = f"ctx={usage.used_tokens}/{usage.context_tokens} ({usage.percent:.1f}%)"
        return (
            f"rova {profile}/{rag}/{skills}  │  {ctx_line}  │  Type / for commands, /exit to quit"
        )
