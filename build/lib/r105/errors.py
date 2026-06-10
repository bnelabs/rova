"""Custom exception hierarchy for r105.

Provides typed, catchable exceptions for every subsystem so callers
can handle specific error categories without parsing strings.
"""

from __future__ import annotations


class R105Error(Exception):
    """Base for all r105-specific exceptions.

    Every r105 exception inherits from this class so callers can write
    ``except R105Error`` to catch any application-level failure.
    """

    exit_code: int = 1


# -- API / network -------------------------------------------------------


class RouterAPIError(R105Error):
    """llama-router API returned an error or could not be reached."""

    def __init__(
        self,
        message: str,
        *,
        status_code: int | None = None,
        response_body: str | None = None,
    ) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.response_body = response_body


# -- Tools ---------------------------------------------------------------


class ToolExecutionError(R105Error):
    """A tool failed during execution (sandbox, I/O, or logic error)."""

    def __init__(
        self,
        tool_name: str,
        message: str,
        *,
        original_error: BaseException | None = None,
    ) -> None:
        super().__init__(f"[{tool_name}] {message}")
        self.tool_name = tool_name
        self.original_error = original_error


# -- Sandbox -------------------------------------------------------------


class SandboxError(R105Error):
    """Sandbox execution failed, timed out, or was denied."""


class SandboxUnavailableError(SandboxError):
    """The requested sandbox backend is not available on this system."""


class SandboxTimeoutError(SandboxError):
    """Sandboxed code exceeded the execution time limit."""


# -- Configuration -------------------------------------------------------


class ConfigError(R105Error):
    """Configuration is invalid, missing, or malformed."""


# -- Plugins -------------------------------------------------------------


class PluginError(R105Error):
    """Plugin loading or execution failed."""


# -- MCP -----------------------------------------------------------------


class MCPError(R105Error):
    """MCP server communication or initialization failed."""


class MCPConnectionError(MCPError):
    """Could not establish a connection to an MCP server."""


class MCPToolError(MCPError):
    """An MCP tool call returned an error or no result."""

    def __init__(
        self,
        server_name: str,
        tool_name: str,
        message: str,
        *,
        original_error: BaseException | None = None,
    ) -> None:
        super().__init__(f"[{server_name}/{tool_name}] {message}")
        self.server_name = server_name
        self.tool_name = tool_name
        self.original_error = original_error
