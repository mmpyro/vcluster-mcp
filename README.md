# vcluster MCP Server

This is a Model Context Protocol (MCP) server that provides tools for managing [vcluster](https://github.com/loft-sh/vcluster) instances. It allows AI assistants to list, describe, create, delete, pause, resume, and even execute commands inside virtual clusters.

## Features

- **Lifecycle Management**: Create, delete, pause, resume, and disconnect vclusters.
- **Observability**: List all vclusters and get detailed descriptions of specific instances.
- **Remote Execution**: Execute commands directly inside a vcluster context using the `vcluster connect` mechanism.
- **Namespace Metadata**: Manage labels and annotations on Kubernetes namespaces associated with vclusters.

## Project Structure

The project follows a modular structure optimized for MCP:

- `src/`: Core application source code.
  - `tools/`: MCP tool implementations (vcluster operations, namespace metadata).
  - `prompt/`: MCP prompt templates to guide the LLM in:
    - **VCluster Management**: General assistance with vcluster operations.
    - **Lifecycle Operations**: Focused guidance on create/delete/pause/resume.
    - **Metadata Management**: Assistance with namespace labels and annotations.
    - **Troubleshooting**: Systematic diagnosis of vcluster-related issues.
  - `utils/`: Shared utilities, Kubernetes client setup, and vcluster manager.
  - `tests/`: Comprehensive unit tests for the server logic.
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
