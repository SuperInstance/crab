# 🐚 crab — Agent Shell for Repo Entry/Leave

> Like entering a MUD room: step into a repo, use its tools, and step out.

Crab is the fleet's shell for **entering and leaving repos** (shells). An agent (or human) can enter a repo, browse its manifest and tools, run commands, watch for outputs, and leave cleanly.

## Quick Start

```bash
# Install
bash install.sh

# Enter a repo
crab enter ~/.openclaw/workspace/arch-sw

# See what's available
crab whoami

# Run a tool from the repo
crab tool install

# Inspect another repo without entering
crab inspect ~/.openclaw/workspace/purplepincher-org-pages

# Watch a repo for outputs
crab watch ~/.openclaw/workspace/research/seed-tick-audit

# Inherit tools from another repo
crab follow ~/.openclaw/workspace/fleet/vessel

# See full status
crab status

# Leave
crab leave
```

## Commands

| Command | Description |
|---------|-------------|
| `crab enter <path>` | Enter a repo — reads MANIFEST, loads tools, starts TICK |
| `crab leave` | Leave current repo — stops TICK, pops from stack |
| `crab list` | List available repos (scan for MANIFEST) |
| `crab whoami` | Show current repo context + available tools |
| `crab inspect <path>` | Show repo MANIFEST + tick + tools without entering |
| `crab tool <name> [args]` | Run a tool from the current repo |
| `crab watch <path>` | Subscribe to a repo's outputs (IO pulls) |
| `crab follow <path>` | Inherit tools from another repo |
| `crab status` | Show entered repos, their health, and tools |

## Manifest Format

Crab works with any of these manifest formats in a repo directory:

### `MANIFEST.md` (Markdown)

```markdown
# My Repo

Description of what this repo provides.

## Tools

- `install.sh` — Install this repo's components
- `uninstall.sh` — Remove this repo's components
- `deploy.sh` — Deploy to production (http://localhost:8900/deploy)

## Provides

- logging
- auth
- routing
```

### `MANIFEST.yaml`

```yaml
name: my-repo
description: A fleet service repo
port: 8900
status: core
tools:
  - name: install
    type: script
    path: scripts/install.sh
    description: Install this repo
  - name: health
    type: http
    endpoint: http://localhost:8900/health
    description: Health check
provides:
  - auth-service
```

### `MANIFEST.json`

```json
{
  "name": "my-repo",
  "description": "JSON manifest example",
  "port": 8847,
  "tools": [
    {
      "name": "status",
      "type": "http",
      "endpoint": "http://localhost:8847/status"
    }
  ]
}
```

### Auto-detected Tools

If no tools are explicitly listed in the manifest, crab will auto-detect:

- `install.sh` / `uninstall.sh` at repo root
- Executable scripts in `scripts/` directory
- Any file referenced in the `provides` list found at standard paths

## Tool Types

| Type | Purpose | Example |
|------|---------|---------|
| `script` | Run a local script | `crab tool install` → runs `install.sh` |
| `http` | Call an HTTP endpoint | `crab tool health` → POST to URL |
| `builtin` | Built-in crab handler | (internal) |

## Architecture

```
┌─────────────────────────────────────────────┐
│                  CrabShell                    │
│                                              │
│  ┌────────┐  ┌────────┐  ┌────────┐         │
│  │ Repo 1 │  │ Repo 2 │  │ Repo 3 │  stack  │
│  └────┬───┘  └────┬───┘  └────┬───┘         │
│       │           │           │              │
│  ┌────▼───────────▼───────────▼───┐          │
│  │      Tool Registry             │          │
│  │  ┌──────┐ ┌──────┐ ┌──────┐   │          │
│  │  │http  │ │script│ │mcp   │   │          │
│  │  └──────┘ └──────┘ └──────┘   │          │
│  └────────────────────────────────┘          │
│                                              │
│  Watch Thread ←────────────────── TICK ──►  │
│  Follow Registry (inherited tools)           │
│  State Persistence ──► ~/.crab/state.json    │
└─────────────────────────────────────────────┘
```

## State Persistence

Crab saves state to `~/.crab/`:

- `state.json` — current entered/watched/followed repos
- `tick-{name}.json` — per-repo TICK status
- `watch-{name}.json` — per-watch health checks

This allows agents to resume shell context across sessions.

## Shell Completion

```bash
# Bash
eval "$(crab completions bash)"

# Zsh
eval "$(crab completions zsh)"
```

## Development

```bash
# Run tests (if pytest available)
python3 -m pytest tests/

# Format code
python3 -m black crab.py

# Check types
python3 -m mypy crab.py --ignore-missing-imports
```

## License

Fleet tool — part of the SuperInstance fleet ecosystem.

## Ecosystem

This repo is part of the **SuperInstance** flagship ecosystem — agent-first computation, constraint theory, and self-improving runtimes.

### FLUX Runtime Family

| Repo | Language | Description |
|------|----------|-------------|
| [flux-runtime](https://github.com/SuperInstance/flux-runtime) | Python | Full FLUX runtime: markdown→bytecode, 2037 tests, zero deps |
| [flux-core](https://github.com/SuperInstance/flux-core) | Rust | Register-based bytecode VM, deterministic agent computation |
| [flux-js](https://github.com/SuperInstance/flux-js) | JavaScript | FLUX VM for Node.js and browsers, ~400ns/iter |
| [flux-compiler](https://github.com/SuperInstance/flux-compiler) | Rust/Python | Formal-methods compiler for safety-critical codegen |
| [flux-vm](https://github.com/SuperInstance/flux-vm) | Rust | Stack-based constraint-checking VM, 50 opcodes, Turing-incomplete |

### PLATO Engine Family

| Repo | Language | Description |
|------|----------|-------------|
| [plato-server](https://github.com/SuperInstance/plato-server) | Python | Knowledge tiles, fleet sync via Matrix, HTTP API |
| [plato-engine-block](https://github.com/SuperInstance/plato-engine-block) | Rust | Original room runtime: no_std + alloc, builder pattern |
| [plato-engine-block-c](https://github.com/SuperInstance/plato-engine-block-c) | C99 | Embedded reference: zero heap alloc, bare-metal portable |
| [plato-engine-block-elixir](https://github.com/SuperInstance/plato-engine-block-elixir) | Elixir | BEAM supervision trees, fault tolerance, hot reload |
| [plato-runtime-kernel](https://github.com/SuperInstance/plato-runtime-kernel) | Rust | Spatial model: tensor grid, batons, assertion traps |

### Constraint / Theory Family

| Repo | Language | Description |
|------|----------|-------------|
| [categorical-agents](https://github.com/SuperInstance/categorical-agents) | Rust | Category theory for agent composition (functors, naturality) |
| [cuda-constraint-engine](https://github.com/SuperInstance/cuda-constraint-engine) | CUDA/C | GPU constraint checking at 1B+ constraints/sec |
| [grand-pattern-rs](https://github.com/SuperInstance/grand-pattern-rs) | Rust | Fibonacci dual-direction cellular graph architecture |
| [lau-hodge-theory](https://github.com/SuperInstance/lau-hodge-theory) | Rust | Hodge decomposition, Betti numbers, spectral sequences |
| [ternary-science](https://github.com/SuperInstance/ternary-science) | Rust | Experimental evidence for ternary intelligence, 5 conservation laws |

### Agent / Infrastructure Family

| Repo | Language | Description |
|------|----------|-------------|
| [construct-core](https://github.com/SuperInstance/construct-core) | Rust | Layered trait system: bare-metal → alloc → async agent runtime |
| [crab](https://github.com/SuperInstance/crab) | Bash | Agent shell for repo entry/leave (MUD-room metaphor) |
| [exocortex](https://github.com/SuperInstance/exocortex) | Rust | Persistent cognitive substrate, S3-compatible memory |
| [git-agent](https://github.com/SuperInstance/git-agent) | Python | The repo IS the agent — autonomous lifecycle via Git |
| [capitaine-1](https://github.com/SuperInstance/capitaine-1) | TypeScript | Git-native repo-agent, Cloudflare Workers heartbeat |
| [codespace-edge-rd](https://github.com/SuperInstance/codespace-edge-rd) | Research | Codespace→Edge agent lifecycle and yoke transfer protocols |
| [git-agent-codespace](https://github.com/SuperInstance/git-agent-codespace) | DevContainer | One-click Codespace template for Git-Agent runtimes |

### Registries

| Registry | Package | Install |
|----------|---------|---------|
| **PyPI** | `flux-vm` | `pip install flux-vm` |
| **crates.io** | `fluxvm` | `cargo add fluxvm` |
| **npm** | `flux-js` | `npm install flux-js` *(coming soon)* |

### Philosophy & Architecture

- 📖 [AI-Writings](https://github.com/SuperInstance/AI-Writings) — Philosophy, essays, and design rationale
- 📦 [PACKAGES.md](https://github.com/SuperInstance/SuperInstance/blob/main/PACKAGES.md) — Full package index
