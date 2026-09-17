# vcluster MCP Server

This is a Model Context Protocol (MCP) server that provides tools for managing [vcluster](https://github.com/loft-sh/vcluster) instances. It allows AI assistants to list, describe, create, delete, pause, resume, export kubeconfigs, inspect control-plane certificates, and even execute commands inside virtual clusters.

## Features

- **Lifecycle Management**: Create (with full helm flag coverage - `--set`, multiple values files, chart pinning, `--expose`), delete, pause, resume, and disconnect vclusters.
- **Observability**: List all vclusters and get detailed descriptions of specific instances.
- **Kubeconfig Export**: Write a vcluster kubeconfig to a private (0600) temporary file and return its path, so credentials are never returned inline and the caller's kube context is left untouched.
- **Certificate Inspection**: Read-only `vcluster certs check` for control-plane certificate expiry.
- **Remote Execution**: Execute commands directly inside a vcluster context using the `vcluster connect` mechanism.
- **Namespace Metadata**: Manage labels and annotations on Kubernetes namespaces associated with vclusters.
- **Read-only Resources**: Browse the environment through `vcluster://` URIs without invoking a tool.
- **Low context cost**: The advertised tool surface is 8,868 chars (~2.5k tokens), down from 29,035. Responses are compact JSON, sent once rather than twice, and hard-capped. A regression test holds the line.

## Documentation

Full documentation lives in [`docs/`](docs/index.md):

- [Tools](docs/tools.md) — all 12 operations, their parameters and safety notes
- [Resources](docs/resources.md) — the 2 read-only `vcluster://` URIs
- [Architecture](docs/architecture.md) — how a call flows through the code, and how to add a tool

## Fixes

- **`vcluster_certs_check` never worked.** It passed `-s` to the CLI, and
  `--silent` suppresses the JSON result itself rather than just the log noise,
  so every call returned `{"error": "Failed to parse vcluster output: ..."}`.
  The flag is gone; the CLI already logs to stderr.
- **`_run_command` discarded stdout on any non-zero exit**, so a command that
  partially succeeded lost its output. It now prefers stdout whenever the
  process wrote any.

## Breaking changes

- **Tools return a JSON string, not a structured object.** Every tool is now
  registered with `structured_output=False`, so responses arrive as a single
  compact text block with no `structuredContent`. Clients that read the
  structured half must parse the text instead.
- **The six namespace label/annotation tools are now two.**
  `get/set/delete_namespace_label` and `get/set/delete_namespace_annotation` are
  replaced by `namespace_metadata_get(namespace, kind)` and
  `namespace_metadata_set(namespace, kind, key, value)`, where omitting `value`
  deletes the key.
- **All six prompts were removed.** Their bodies re-listed the tool schemas the
  client already loads.
- **`vcluster://clusters` and `vcluster://{namespace}/{name}` were removed.**
  They duplicated `vcluster_list` and `vcluster_describe`.
- **`vcluster_list` drops the `Created` field by default**, since `AgeSeconds`
  carries the same fact; pass `full=True` to get it back.
- **Responses are capped** at 20,000 chars (2,000 for stderr inside an error
  message), with an explicit `[truncated: N more chars]` marker.
- **`vcluster_delete` no longer deletes the host namespace by default.** Previously
  every delete passed `--delete-namespace`, which destroyed the namespace along with
  any unrelated workloads in it. The namespace is now preserved unless you pass
  `delete_namespace=True`; vcluster still cleans up namespaces it created itself.

## Project Structure

The project follows a modular structure optimized for MCP:

- `src/`: Core application source code.
  - `tools/`: MCP tool implementations (vcluster operations, namespace metadata).
  - `resources/`: Read-only `vcluster://` resources for browsing clusters,
    certificates and namespace metadata.
  - `utils/`: Shared utilities, Kubernetes client setup, and vcluster manager.
  - `tests/`: Comprehensive unit tests for the server logic.
- `docs/`: Tool, resource and architecture documentation.
- `pyproject.toml`: Project configuration and dependency management via `uv`.

## Prerequisites

To run this MCP server and manage vclusters, you need the following:

### 1. Python Environment
This project uses `uv` for dependency management. See [Development Commands](#development-commands) for installation.

### 2. vcluster CLI
[vcluster CLI](https://vcluster.com/docs/getting-started/installation) must be installed on your system and available in your PATH.

### 3. kubectl
[kubectl](https://kubernetes.io/docs/tasks/tools/) must be installed and configured with access to the host Kubernetes cluster where vclusters are running.

## Development Commands

For convenience, a `Makefile` is provided with common tasks:

- **Sync dependencies**:
  ```bash
  make sync      # Production only
  make sync-dev  # Include dev dependencies
  ```
- **Running tests**:
  ```bash
  make unittest          # Run unit tests only
  make test-cov          # Run tests with coverage report
  ```
- **Quality Checks**:
  ```bash
  make lint              # Run flake8 linting
  make typecheck         # Run mypy type checking
  make check             # Run both linting and type checking
  ```
- **Local Development**:
  ```bash
  make dev               # Start server in development mode
  ```

## Configuration for Cloud Code / Claude Desktop

To use this MCP server, add the following configuration to your `mcpServers` setting:

### Local path

**Important**: Before using this MCP server, you need to install the dependencies. Run this command in the project root:
```bash
uv sync
```

Then add the following configuration to your MCP settings:

```json
{
  "mcpServers": {
    "vcluster": {
      "type": "stdio",
      "command": "uv",
      "args": [
        "--directory",
        "~/vcluster-mcp-server",
        "run",
        "python",
        "src/server.py"
      ],
      "env": {}
    }
  }
}
```

### uvx

[`uvx`](https://docs.astral.sh/uv/guides/tools/) is a `uv` subcommand for running Python tools in an isolated, cached environment.

Example configuration:
```json
{
  "mcpServers": {
    "vcluster": {
      "type": "stdio",
      "command": "uvx",
      "args": [
        "git+https://github.com/mmpyro/vcluster-mcp-server.git"
      ]
    }
  }
}
```

## Contributing

Unit tests are located in `src/tests`. Please ensure all tests pass before submitting changes.
