"""Main chat screen — the primary interactive screen."""

from __future__ import annotations

import json
from pathlib import Path

import httpx
from rich.text import Text
from textual import work
from textual.app import ComposeResult
from textual.containers import Horizontal
from textual.screen import Screen
from textual.widgets import Static

from rova.client import RouterClient
from rova.state import ChatState, DEFAULT_MODEL, token_usage
from rova.commands import handle_slash_command
from rova.tools import execute_tool_call, TOOL_DEFINITIONS
from rova.tui.widgets.chat_view import ChatView
from rova.tui.widgets.input_area import ChatInput
from rova.tui.widgets.command_palette import CommandPalette, COMMAND_DEFS
from rova.tui.widgets.sidebar import Sidebar
from rova.tui.widgets.status_bar import StatusBarWidget


def _is_exact_command(text: str) -> bool:
    """Check if the input text has a recognized command as its first word.

    /help           → True  (exact match)
    /profile simple → True  (/profile is a known command)
    /prf            → False (fuzzy/partial, needs palette selection)
    """
    first_word = text.strip().split()[0] if text.strip() else ""
    for cmd, _usage, _desc in COMMAND_DEFS:
        if cmd == first_word:
            return True
    return False


class ChatScreen(Screen[None]):
    """The main chat screen with chat history, command palette, input, and sidebar."""

    def __init__(
        self,
        client: RouterClient,
        state: ChatState,
        workspace_dir: Path,
    ) -> None:
        super().__init__()
        self.client = client
        self.state = state
        self.workspace = workspace_dir
        self._http = httpx.AsyncClient()

    def on_unmount(self) -> None:
        import asyncio

        asyncio.create_task(self._http.aclose())

    def compose(self) -> ComposeResult:
        yield Static(self._render_header(), id="rova-header")
        with Horizontal(id="main-content"):
            yield ChatView(id="chat-view")
            yield Sidebar(id="sidebar")
        yield CommandPalette(id="command-palette")
        yield ChatInput(id="chat-input")
        yield StatusBarWidget(id="status-bar")

    def on_mount(self) -> None:
        self._refresh_all()

    # -- Input handling ---------------------------------------------------

    def on_chat_input_chat_submitted(self, event: ChatInput.ChatSubmitted) -> None:
        """Handle a normal (non-slash) message submission."""
        text = event.value.strip()
        if not text:
            return

        chat_view = self.query_one("#chat-view", ChatView)

        if text.startswith("/"):
            result = handle_slash_command(
                text, self.state, self.client, self.workspace
            )
            if text in {"/exit", "/quit"}:
                self.app.exit()
                return
            chat_view.add_system(result)
        else:
            chat_view.add_user(text)
            self._send_message(text)

        self._refresh_all()

    # -- Slash command palette --------------------------------------------

    def on_chat_input_slash_changed(self, event: ChatInput.SlashChanged) -> None:
        """Update the command palette filter as the user types."""
        palette = self.query_one("#command-palette", CommandPalette)
        if event.value.startswith("/"):
            palette.show_commands(event.value)
        else:
            palette.hide()

    def on_chat_input_slash_navigate(self, event: ChatInput.SlashNavigate) -> None:
        """Move the palette selection up or down."""
        palette = self.query_one("#command-palette", CommandPalette)
        if not palette.is_visible:
            return
        if event.direction == -1:
            palette.select_prev()
        else:
            palette.select_next()

    def on_chat_input_slash_select(self, event: ChatInput.SlashSelect) -> None:
        """Enter pressed in slash mode — select command or execute directly."""
        palette = self.query_one("#command-palette", CommandPalette)
        input_widget = self.query_one("#chat-input", ChatInput)
        chat_view = self.query_one("#chat-view", ChatView)

        current_text = input_widget.text.strip()
        palette.hide()

        # If the user typed an exact command (like /help, /clear, /exit),
        # execute it directly without going through the palette picker.
        if _is_exact_command(current_text):
            result = handle_slash_command(
                current_text, self.state, self.client, self.workspace
            )
            if current_text in {"/exit", "/quit"}:
                self.app.exit()
                return
            chat_view.add_system(result)
            input_widget.clear()
            self._refresh_all()
            return

        # Otherwise: fill the input with the selected command so the user
        # can add arguments, then press Enter again to execute.
        selected_cmd = palette.get_selected_command()
        if selected_cmd:
            input_widget.text = selected_cmd + " "
            # Move cursor to end
            input_widget.cursor_location = (
                input_widget.document.line_count - 1,
                len(input_widget.text),
            )
            # Re-post slash changed so the palette updates for the new text
            if selected_cmd.startswith("/"):
                input_widget.post_message(
                    ChatInput.SlashChanged(selected_cmd + " ")
                )
        self._refresh_all()

    def on_chat_input_slash_dismiss(self, event: ChatInput.SlashDismiss) -> None:
        """Escape pressed — hide the palette."""
        palette = self.query_one("#command-palette", CommandPalette)
        palette.hide()
        self._refresh_all()

    # -- Message sending & tool loop --------------------------------------

    @work(exclusive=True)
    async def _send_message(self, message: str) -> None:
        chat_view = self.query_one("#chat-view", ChatView)
        tools = TOOL_DEFINITIONS if self.state.profile == "tool_agent" else None

        if tools:
            # If tools are active, we use non-streaming for now to handle the loop
            try:
                result = await self.client.async_send(
                    message, self.state, tools, self._http
                )
            except Exception as exc:
                chat_view.add_error(f"Send failed: {exc}")
                self._refresh_all()
                return
        else:
            # Normal chat uses streaming
            import time
            start_time = time.perf_counter()
            full_content = []
            stream_widget = None
            try:
                async for chunk in self.client.async_stream(
                    message, self.state, None, self._http
                ):
                    if not stream_widget:
                         stream_widget = chat_view.start_assistant_stream()
                    full_content.append(chunk)
                    chat_view.append_assistant(stream_widget, chunk)

                wall_seconds = time.perf_counter() - start_time
                # Remove the streaming widget and add a proper Panel for the final result
                if stream_widget:
                    stream_widget.remove()
                chat_view.add_assistant("".join(full_content), wall_seconds)
                self._refresh_all()
                return
            except Exception as exc:
                chat_view.add_error(f"Stream failed: {exc}")
                self._refresh_all()
                return

        max_iterations = 10
        iteration = 0
        while result.tool_calls and iteration < max_iterations:
            iteration += 1
            for tc in result.tool_calls:
                func = tc.get("function", {})
                name = func.get("name", "unknown")
                try:
                    args = func.get("arguments", {})
                    if isinstance(args, str):
                        args = json.loads(args)
                except (json.JSONDecodeError, TypeError):
                    args = {}
                args_str = json.dumps(args, indent=2, sort_keys=True)
                chat_view.add_tool_call(name, args_str)

                tool_result_msg = execute_tool_call(tc, self.workspace)
                result_content = tool_result_msg.get("content", "")
                chat_view.add_tool_result(result_content)

                self.state.history.append(
                    {
                        "role": "assistant",
                        "content": result.content or "",
                        "tool_calls": result.tool_calls,
                    }
                )
                self.state.history.append(tool_result_msg)

            try:
                result = await self.client.async_send(
                    "Tool results received. Continue or provide final answer.",
                    self.state,
                    tools,
                    self._http,
                )
            except Exception as exc:
                chat_view.add_error(f"Tool loop error: {exc}")
                self._refresh_all()
                return

        chat_view.add_assistant(result.content, result.wall_seconds)
        self._refresh_all()

    # -- Refresh helpers --------------------------------------------------

    def _render_header(self) -> str:
        usage = token_usage(self.state)
        pct = f"({usage.percent:.0f}%)" if usage.percent > 0 else ""
        return (
            f"Rova  ·  {DEFAULT_MODEL}  ·  "
            f"{usage.used_tokens}/{usage.context_tokens} {pct}  ·  "
            f"{self.client.base_url}\n"
            f"profile={self.state.profile or 'auto'}  "
            f"rag={self.state.rag if self.state.rag is not None else 'auto'}  "
            f"quality={self.state.quality or 'auto'}  "
            f"skills={','.join(self.state.active_skills) if self.state.active_skills else 'none'}"
        )

    def _refresh_all(self) -> None:
        self._refresh_header()
        self._refresh_sidebar()
        self._refresh_status_bar()

    def _refresh_header(self) -> None:
        try:
            self.query_one("#rova-header", Static).update(self._render_header())
        except Exception:
            pass

    def _refresh_sidebar(self) -> None:
        try:
            self.query_one("#sidebar", Sidebar).refresh_state(
                self.state, self.workspace
            )
        except Exception:
            pass

    def _refresh_status_bar(self) -> None:
        try:
            usage = token_usage(self.state)
            self.query_one("#status-bar", StatusBarWidget).update_status(
                self.state, usage
            )
        except Exception:
            pass
