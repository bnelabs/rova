"""Command palette dropdown that appears when user types /."""

from __future__ import annotations

from textual.widgets import Static


# Structured command definitions: (command, usage, description)
COMMAND_DEFS: list[tuple[str, str, str]] = [
    # Chat
    ("/state", "", "Show active settings (profile, rag, quality, tokens)"),
    ("/tokens", "", "Show estimated context usage"),
    ("/model", "", "Show active model and context window capacity"),
    ("/history", "", "Show last 12 messages in compact form"),
    ("/clear", "", "Clear all conversation history"),
    ("/compact", "", "Summarize conversation history and continue"),
    ("/profile", "<name>", "Force a router task profile, or omit for auto"),
    ("/quality", "fast|balanced|best", "Set quality hint metadata"),
    ("/json", "[on|off]", "Toggle JSON object response mode"),
    ("/max", "<tokens>", "Override max_tokens, or omit for auto"),
    # RAG
    ("/rag", "on|off", "Toggle RAG metadata for chat requests"),
    ("/rag ingest", "<path-or-url>...", "Ingest local files/directories or URLs"),
    ("/rag search", "<query>", "Search the active RAG index"),
    # Skills
    ("/skills", "", "List available skill files"),
    ("/skill use", "<name>", "Add a skill to the active chat"),
    ("/skill drop", "<name>", "Remove one active skill"),
    ("/skill clear", "", "Remove all active skills"),
    ("/skill show", "<name>", "Print a skill file"),
    # Workspace
    ("/workspace", "", "Show workspace directory and generated files"),
    # System
    ("/health", "", "Check llama-router health"),
    ("/profiles", "", "List available router profiles"),
    ("/help", "", "Show full command reference"),
    ("/exit", "", "Quit Rova"),
]


class CommandPalette(Static):
    """A suggestion palette that appears above the input when typing /.

    Shows filtered commands with descriptions as the user types."""

    def show_commands(self, filter_text: str) -> None:
        """Show commands matching the partial input."""
        prefix = filter_text.lstrip("/").lower()
        lines: list[str] = []

        for cmd, usage, desc in COMMAND_DEFS:
            cmd_name = cmd.lstrip("/").lower()
            if prefix and prefix not in cmd_name:
                continue
            usage_str = f" {usage}" if usage else ""
            lines.append(f"[bold]{cmd}[/bold]{usage_str}")
            lines.append(f"  [dim]{desc}[/dim]")

        if not lines:
            lines.append(f"[dim]no commands matching '{filter_text}'[/dim]")

        self.update("\n".join(lines))
        if filter_text:
            self.add_class("-visible")
        else:
            self.remove_class("-visible")

    def hide(self) -> None:
        self.remove_class("-visible")
