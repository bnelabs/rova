<p align="center">
  <img src="ROVA.png" alt="Rova" width="600">
</p>

# Rova — Rapid On-demand Virtual Assistant

Rova is a rich terminal frontend for [llama-router](https://github.com/komedi/llama-router), built on [Textual](https://textual.textualize.io/). It provides an interactive chat TUI with streaming SSE responses, slash-command system, fuzzy command palette, local tool execution, secure sandboxing, MCP integration, plugin extensibility, session persistence, and multiple themes.

<p align="center">
  <img src="https://img.shields.io/pypi/v/rova?color=cba6f7" alt="PyPI">
  <img src="https://img.shields.io/badge/python-3.12%20%7C%203.13-blue" alt="Python">
  <img src="https://img.shields.io/badge/tests-165%20passed-brightgreen" alt="Tests">
  <img src="https://img.shields.io/badge/license-MIT-green" alt="License">
</p>

---

## Prerequisites

- **Python 3.12+**
- **[llama-router](https://github.com/komedi/llama-router)** running on `http://127.0.0.1:8010` (or set `ROVA_URL`)

---

## Installation

### pipx (recommended)

```sh
pipx install rova
```

### Homebrew (macOS / Linux)

```sh
brew install bnelabs/tap/rova
```

### From source

```sh
git clone https://github.com/bnelabs/rova.git
cd rova
python -m venv .venv
.venv/bin/pip install -e .
ln -sf "$(pwd)/bin/rova" ~/.local/bin/rova
```

### Docker

```sh
docker build -t rova .
docker run -it --rm \
  -v ~/.config/rova:/root/.config/rova \
  -v ~/rova-workspace:/root/rova-workspace \
  rova chat
```

For a quick-start stack with llama-router, use the included `docker-compose.yml`:

```sh
docker compose up -d llama-router
docker compose run rova chat
```

---

## CLI Usage

Rova can be used directly from the command line for one-shot prompts or management commands:

```sh
# Interactive chat (default, opens TUI)
rova chat

# One-shot prompt
rova send "explain quicksort in 3 sentences"

# Check router health
rova health

# List available profiles
rova profiles

# Ingest documents for RAG
rova ingest /path/to/docs https://example.com/page

# Search the RAG index
rova search "query terms"

# Version info
rova --version
```

### CLI Flags

| Flag | Default | Description |
|------|---------|-------------|
| `--url` | `http://127.0.0.1:8010` | Router base URL |
| `--workspace` | `~/rova-workspace` | Workspace directory for generated files |
| `--skills-dir` | `./skills` | Directory containing skill `.md` files |
| `--profile` | auto | Force a router task profile |
| `--model` | auto | Override the model selection |
| `--quality` | auto | Quality hint: `fast`, `balanced`, or `best` |
| `--rag` | off | Enable RAG (Retrieval-Augmented Generation) |
| `--max-tokens` | auto | Override max output tokens |
| `--json` | off | Request JSON-object responses |

---

## Interactive TUI Commands

Press `/` in the TUI to open the interactive command palette with fuzzy filtering, arrow-key navigation, and Tab autocomplete. The palette shows commands grouped by category.

### Chat

| Command | Description |
|---------|-------------|
| `/state` | Show active settings (profile, RAG, quality, tokens, model) |
| `/tokens` | Show estimated context token usage and capacity |
| `/model [name]` | Show current model, list available models, or switch models |
| `/history` | Open scrollable history browser with fuzzy search |
| `/clear` | Clear all conversation history |
| `/compact` | Summarize conversation history and continue |
| `/profile <name>` | Force a router task profile, or omit for auto-detection |
| `/quality fast\|balanced\|best` | Set quality hint metadata |
| `/json [on\|off]` | Toggle JSON object response mode |
| `/max <tokens>` | Override max_tokens, or omit for auto |
| `/autocompact [on\|off]` | Toggle auto-compaction at 80% context threshold |
| `/copy` | Copy last assistant message to system clipboard |

### RAG (Retrieval-Augmented Generation)

| Command | Description |
|---------|-------------|
| `/rag [on\|off]` | Toggle RAG metadata for chat requests |
| `/rag ingest <path-or-url>...` | Ingest local files/directories or URLs into the index |
| `/rag search <query>` | Search the active RAG index |
| `/rag list` | List all indexed documents |
| `/rag delete <id>` | Remove a document from the RAG index |
| `/rag update <path>` | Re-index specific paths |

### Skills

Skills are reusable prompt templates stored as Markdown files with `{param}` placeholder substitution.

| Command | Description |
|---------|-------------|
| `/skills` | List available skill files in the skills directory |
| `/skill use <name> [key=val...]` | Add a skill with optional parameters |
| `/skill drop <name>` | Remove one active skill from the conversation |
| `/skill clear` | Remove all active skills |
| `/skill show <name>` | Print the contents of a skill file |

Example skill file (`skills/search.md`):

```markdown
When answering questions, use web_search with query="{query}" and cite your sources.
```

Usage:

```
/skill use search query="Python 3.13 release notes"
```

### Sessions & Export

Conversations can be saved, loaded, and exported in multiple formats. Rova also auto-saves on exit as `__autosave__`.

| Command | Description |
|---------|-------------|
| `/session save <name>` | Save current conversation to `~/.config/rova/sessions/` |
| `/session load <name>` | Load and restore a previously saved session |
| `/session list` | List all saved sessions with previews and timestamps |
| `/session delete <name>` | Delete a saved session |
| `/export markdown` | Export conversation as Markdown to the workspace |
| `/export json` | Export conversation as JSON |
| `/export html` | Export conversation as a styled HTML page |

### Plugins

Custom tools can be loaded from Python scripts in `~/.config/rova/plugins/`. Each file exposes a `register(registry)` function that adds tools via `registry.add_tool()`. See [docs/TOOLS.md](docs/TOOLS.md) for the API reference.

| Command | Description |
|---------|-------------|
| `/plugin list` | List loaded custom tool plugins |
| `/plugin reload` | Reload plugins from disk |

### MCP (Model Context Protocol)

Rova can connect to external MCP servers (stdio or SSE transport) to access hundreds of community-built tools without changing Rova's code. Configure servers in `~/.config/rova/config.json`:

```json
{
  "mcp_servers": [
    {
      "name": "github",
      "transport": "sse",
      "url": "http://127.0.0.1:3001/mcp"
    },
    {
      "name": "filesystem",
      "transport": "stdio",
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-filesystem", "/tmp"]
    }
  ]
}
```

| Command | Description |
|---------|-------------|
| `/mcp list` | List connected MCP servers and their tool counts |
| `/mcp tools <server>` | List tools exposed by a specific MCP server |

### Workspace & System

| Command | Description |
|---------|-------------|
| `/workspace` | Show workspace directory and list generated files |
| `/preview <filename>` | Preview a workspace file's contents |
| `/theme <name>` | Switch theme: `rova`, `dracula`, `solarized-dark`, `high-contrast` |
| `/health` | Check llama-router and upstream model health |
| `/profiles` | List available router task profiles |
| `/help` | Show the full command reference |
| `/exit` | Quit Rova |

---

## Keybindings

| Key | Context | Action |
|-----|---------|--------|
| `Enter` | Normal mode | Submit message |
| `Enter` | Slash mode | Execute or select command |
| `Shift+Enter` | Any | Insert newline |
| `↑` / `↓` | Normal mode | Navigate input history |
| `↑` / `↓` | Slash mode | Navigate command palette |
| `Tab` | Slash mode | Fuzzy-autocomplete command |
| `Escape` | Slash mode | Dismiss command palette |
| `Ctrl+R` | Any | Open interactive history browser (fuzzy search supported) |
| `Ctrl+S` | History screen | Quick-save current session |
| `Ctrl+Y` | Any | Copy last assistant response to clipboard |
| `F1` / `Ctrl+H` | Any | Show help screen |
| `Ctrl+Q` / `Ctrl+C` | Any | Quit |

---

## Themes

Four themes included — switch at runtime with `/theme <name>`:

| Theme | Accent | Style |
|-------|--------|-------|
| `rova` (default) | `#cba6f7` mauve | Catppuccin Mocha |
| `dracula` | `#bd93f9` purple | Dracula |
| `solarized-dark` | `#268bd2` blue | Solarized Dark |
| `high-contrast` | `#ffff00` yellow | Accessibility-focused |

---

## Built-in Tools

The local tool executor provides 9 tools the LLM can call. All tools are validated before execution (argument size caps, SSRF prevention, path traversal hardening). `execute_python` runs in a sandboxed environment.

| Tool | Description | Sandbox Profile |
|------|-------------|----------------|
| `execute_python` | Sandboxed Python execution (256MB, 25s, seccomp) | No network, no filesystem |
| `write_file` | Write/update files in workspace | Filesystem access |
| `read_file` | Read file contents (max 50MB) | Filesystem access |
| `list_files` | List directory contents | Filesystem access |
| `web_search` | Search via DuckDuckGo (no API key) | Network access |
| `web_fetch` | Fetch URL content (HTML stripped) | Network access |
| `get_time` | Current system time in ISO 8601 | Minimal isolation |
| `calculate` | Safe arithmetic expression evaluator | Minimal isolation |
| `system_info` | OS, Python version, CPU count | Minimal isolation |

### File Diffing

When `write_file` modifies an existing file, it generates a unified diff. The TUI can display this in a `DiffView` widget with syntax-colored additions/deletions and approve/reject buttons, preventing accidental overwrites.

---

## Sandbox & Security

Rova implements layered security for code execution:

- **Nsjail Sandbox** (strongest): Linux namespace isolation, seccomp-bpf syscall allowlist, network namespace isolation, no host filesystem access
- **Bwrap Sandbox**: Bubblewrap-based user namespace isolation, minimal `/dev` bind (null, urandom, zero, fd), conditional network/filesystem grants per sandbox profile
- **RLimit Sandbox**: Resource limits via `setrlimit()` (memory, CPU, file size, child processes)
- **Noop Sandbox**: Fallback for Windows or when explicit

Backend priority: `nsjail` > `bwrap` > `rlimit` > `none`.

Security features across all tools:

- **SSRF prevention**: URL validation, DNS resolution checks against private IPv4/IPv6 blocks
- **Path traversal hardening**: Symlink-aware path validation, workspace containment
- **Environment sanitization**: Secrets, tokens, API keys, SSH keys stripped from subprocess environments
- **Argument validation**: Size caps on code (100KB), file writes (10MB), search queries (500 chars)

---

## Skills

Skills are reusable Markdown prompt templates. They support `{param}` placeholder substitution for dynamic content injection.

```
skills/
├── code-check.md      # Code review assistant
├── concise.md         # Force concise responses
├── deep-review.md     # Comprehensive code analysis
└── rag-answer.md      # RAG-aware answering with citations
```

Skills appear as system messages in the LLM context, allowing them to persist across `/clear`.

---

## Configuration

Rova stores configuration in `~/.config/rova/`:

```
~/.config/rova/
├── config.json          # MCP servers, model preferences, sandbox backend
├── sessions/            # Saved conversation sessions (JSON)
│   ├── __autosave__.json
│   └── my-session.json
├── plugins/             # Custom tool Python files
│   └── hello.py
└── state.json           # Persistent TUI state (profile, theme, quality)
```

Example `config.json`:
```json
{
  "model": "gemma-4-12b-it",
  "sandbox": "bwrap",
  "mcp_servers": [
    {
      "name": "github",
      "transport": "sse",
      "url": "http://127.0.0.1:3001/mcp"
    }
  ]
}
```

---

## Docker

### Standalone

```sh
docker build -t rova .
docker run -it --rm \
  -v ~/.config/rova:/root/.config/rova \
  -v ~/rova-workspace:/root/rova-workspace \
  rova chat
```

### Quick-start stack with llama-router

The `docker-compose.yml` starts both rova and llama-router on a shared network:

```sh
# Start the router in background
docker compose up -d llama-router

# Launch the TUI
docker compose run rova chat
```

The stack mounts `~/.config/rova` and `~/.config/llama-router` for persistent configuration. Environment variable `ROVA_URL=http://llama-router:8010` is set automatically.

---

## Testing

```sh
# Install dev dependencies
pip install -e ".[dev]"

# Run full test suite
python -m pytest tests/ -v

# With coverage
python -m pytest tests/ -v --cov=rova --cov-report=term-missing

# Lint and type-check
ruff check rova/ tests/
mypy rova/
```

165 tests covering commands, tools, state, skills, client, integration, session management, TUI components, and the command palette.

---

## Documentation

| Document | Description |
|----------|-------------|
| [ARCHITECTURE.md](ARCHITECTURE.md) | System design, data flow, component tree, key patterns |
| [CHANGELOG.md](CHANGELOG.md) | Version history and release notes |
| [CONTRIBUTING.md](CONTRIBUTING.md) | Dev setup, testing, linting, PR process |
| [docs/TOOLS.md](docs/TOOLS.md) | Custom tool + plugin API with JSON Schema |
| [docs/SKILLS.md](docs/SKILLS.md) | Skill authoring guide with parameters |
| [docs/homebrew.rb](docs/homebrew.rb) | Homebrew formula template |

---

## License

MIT — see the [LICENSE](LICENSE) file for details.
