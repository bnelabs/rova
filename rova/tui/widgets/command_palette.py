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


def _fuzzy_score(candidate: str, query: str) -> int:
    """Score a candidate against a query using character contiguity.

    Characters must appear in order. Contiguous runs score higher.
    Exact prefix match gets a large bonus.
    """
    c = candidate.lower()
    q = query.lower()
    if not q:
        return 0
    if c.startswith(q):
        return 1000 + len(q) * 10
    if q in c:
        return 500 + len(q) * 5

    qi = 0
    last_match = -1
    longest_contig = 0
    current_contig = 0
    for i, ch in enumerate(c):
        if qi < len(q) and ch == q[qi]:
            qi += 1
            if last_match >= 0 and i == last_match + 1:
                current_contig += 1
            else:
                current_contig = 1
            longest_contig = max(longest_contig, current_contig)
            last_match = i
    if qi < len(q):
        return 0
    return longest_contig * 10 + qi * 2


class CommandPalette(Static):
    """A suggestion palette that appears above the input when typing /.

    Shows fuzzy-matched commands with descriptions as the user types."""

    MAX_VISIBLE = 12

    def show_commands(self, filter_text: str) -> None:
        """Show commands fuzzy-matching the partial input."""
        query = filter_text.strip()
        lines: list[str] = []

        if query:
            # Score and sort commands
            scored: list[tuple[int, str, str, str]] = []
            for cmd, usage, desc in COMMAND_DEFS:
                score = _fuzzy_score(cmd, query)
                # Also match descriptions and usage
                if score <= 0:
                    score = _fuzzy_score(desc, query)
                if score <= 0 and usage:
                    score = _fuzzy_score(usage, query)
                if score > 0 or query.lstrip("/").lower() in cmd.lower():
                    scored.append((max(score, 1), cmd, usage, desc))

            scored.sort(key=lambda x: x[0], reverse=True)

            for score, cmd, usage, desc in scored[: self.MAX_VISIBLE]:
                usage_str = f" {usage}" if usage else ""
                lines.append(f"[bold]{cmd}[/bold]{usage_str}")
                lines.append(f"  [dim]{desc}[/dim]")

        if not lines:
            if query:
                lines.append(f"[dim]no commands matching '{query}'[/dim]")
            else:
                # Show all commands when just "/"
                for cmd, usage, desc in COMMAND_DEFS:
                    usage_str = f" {usage}" if usage else ""
                    lines.append(f"[bold]{cmd}[/bold]{usage_str}")
                    lines.append(f"  [dim]{desc}[/dim]")

        self.update("\n".join(lines))
        if query:
            self.add_class("-visible")
        else:
            self.remove_class("-visible")

    def hide(self) -> None:
        self.remove_class("-visible")
