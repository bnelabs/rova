# Changelog

All notable changes to Rova are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Dict-based command dispatch (`COMMAND_DISPATCH`) replacing if-elif chain
- Custom exception hierarchy (`rova/errors.py`): `RovaError`, `RouterAPIError`, `ToolExecutionError`, `SandboxError`, `ConfigError`, `PluginError`, `MCPError`
- `_async_request` / `_sync_request` helpers reducing client code duplication (~80 lines removed)
- Centralised configuration constants (`rova/constants.py`)
- Input validation for tool arguments (file size caps, URL scheme restrictions, SSRF prevention for `web_fetch`)
- Symlink-aware path traversal hardening (`_validate_path`)
- Environment variable sanitisation in sandbox (`_sanitize_env`)
- "Did you mean?" suggestions for unknown commands, profiles, qualities, themes, and skills
- Copy-to-clipboard support (`/copy` command, `Ctrl+Y` keybinding)
- Multi-model support (`/model <name>`, `--model` CLI flag, `model` config key)
- Docker image (`Dockerfile`, `.dockerignore`, `docker-compose.yml`)
- Test coverage reporting via `pytest-cov` in CI
- TUI structural tests (`tests/test_tui.py`)

### Changed
- `handle_slash_command` now dispatches via `COMMAND_DISPATCH` dict
- `RouterClient` methods delegate to shared `_sync_request` / `_async_request` helpers
- Sandbox backends inherit timeout from `SANDBOX_TIMEOUT` constant
- `ChatState.model` replaces hardcoded `DEFAULT_MODEL` in payloads
- Hardcoded magic numbers replaced with named constants

## [0.2.0] — 2025-06

### Added
- Sandbox abstraction with `BwrapSandbox`, `RLimitSandbox`, and `NoopSandbox` backends
- Plugin system (`rova/plugins.py`): custom tools from Python files in `~/.config/rova/plugins/`
- MCP (Model Context Protocol) support (`rova/mcp_client.py`): JSON-RPC over stdio
- Session management: `/session save|load|list|delete`, `--session` CLI flag
- Conversation export: `/export markdown|json|html`

## [0.1.0] — 2025-05

### Added
- Initial release: TUI frontend for llama-router
- Interactive chat with streaming SSE support
- Built-in tools: `execute_python`, `write_file`, `read_file`, `list_files`, `web_search`, `web_fetch`, `get_time`, `calculate`, `system_info`
- Slash-command system with fuzzy command palette
- Theme system with 4 built-in themes (rova, dracula, solarized-dark, high-contrast)
- Skills system with markdown skill files and parameter substitution
- RAG integration with ingest, search, list, delete commands
- File explorer sidebar
- Token usage estimation and auto-compaction at 80% context
