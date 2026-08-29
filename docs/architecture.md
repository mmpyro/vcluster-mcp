# Architecture

## Layers

```
src/server.py           entrypoint; imports the three packages for their
                        registration side effects, then mcp.run()
  |
  +-- src/tools/        @mcp.tool()     -- 16 callable operations
  +-- src/prompt/       @mcp.prompt()   -- 6 guided workflows
  +-- src/resources/    @mcp.resource() -- 4 read-only URIs
        |
        +-- src/utils/vcluster_manager.py   VClusterManager: builds argv,
        |                                   runs the CLI, parses output
        +-- src/utils/result.py             Result[T] -- ok/err, no exceptions
        +-- src/utils/exceptions.py         VClusterError hierarchy
        +-- src/utils/k8s.py                setup_kubernetes()
        +-- src/utils/mcp.py                Server singleton wrapping FastMCP
```

`Server` (`src/utils/mcp.py`) is a thread-safe singleton around one `FastMCP`
instance. Every module does `mcp = Server().mcp` at import time, so all
decorators register onto the same server.

## How a call flows

Taking `vcluster_delete` as the example:

1. **Tool** (`src/tools/vcluster.py`) calls `setup_kubernetes(kubeconfig_path)`,
   constructs a `VClusterManager`, and delegates.
2. **Manager** (`src/utils/vcluster_manager.py`) validates inputs — raising
   `ValidationError` — defaults the namespace to `vcluster-<name>`, and builds
   the argv list.
3. **`_run_command`** runs `subprocess.run(cmd, shell=False)` and returns a
   `CommandResult(exit_code, output)`. `output` is stdout on success, stderr on
   failure. Raises `VClusterCLIError` (or `VClusterTimeoutError`) on process
   problems.
4. **Manager** inspects the exit code and returns `Result.ok(...)` or
   `Result.err(...)`.
5. **Tool** passes it through `_handle_result`, which unwraps the value or
   returns `{"error": ...}`.

Two error channels, deliberately:

- `ValidationError` **raises** out of the manager and is caught by the tool
  wrapper. Bad input never reaches a subprocess.
- Everything else becomes a `Result.err`, so the client gets a message rather
  than a stack trace.

## Command construction

`shell=False` with a list argv, so shell injection is not possible. Validation
targets the remaining risks instead: a value starting with `-` that the CLI
would parse as a flag, control characters, and commas inside `--set` values
(helm splits on them).

Two conventions worth preserving when adding a command:

- **Emit only deviations from the CLI's own defaults.** `wait=True` matches the
  CLI, so no flag is emitted. This keeps argv minimal and lets tests assert full
  equality.
- **Negated booleans need `=`.** `--wait=false`, not `--wait false` — the space
  form makes cobra read `false` as a positional argument.

## Adding a tool

1. Add the method to `VClusterManager`, following the existing skeleton:
   validate, default the namespace, build argv, run, map to `Result`.
2. Add the `@mcp.tool()` wrapper in `src/tools/vcluster.py`, with
   `kubeconfig_path` as the last parameter and a Google-style docstring — MCP
   derives the tool schema from the signature and docstring.
3. Export it from `src/tools/__init__.py` (both the import block and `__all__`).
4. Mention it in the relevant prompt in `src/prompt/prompts.py`.
5. Add tests (see below).

For a read-only view, consider a resource in `src/resources/vcluster.py`
instead — same manager method, no duplicate logic.

## Tests

`src/tests/`, 210 tests. The dominant pattern patches the manager's own
`_run_command` and asserts on the argv:

```python
def test_delete_default_argv_preserves_namespace(self, vcluster_manager):
    mock_result = CommandResult(exit_code=0, output="Deleted successfully")
    with patch.object(
        vcluster_manager, "_run_command", return_value=mock_result
    ) as mock_run:
        result = vcluster_manager.delete("test-cluster")

    assert result.is_ok
    call_args = mock_run.call_args[0][0]
    assert "--delete-namespace" not in call_args
```

| File | Covers |
| --- | --- |
| `test_cli_operations.py` | Every CLI-backed manager method, with argv assertions |
| `test_validation.py` | The validators, parametrized |
| `test_edge_cases.py` | Subprocess failure paths — the only place `subprocess.run` itself is patched |
| `test_mcp_integration.py` | Tool wrappers, including keyword forwarding to the manager |
| `test_resources.py` | The four resources |
| `test_result_type.py`, `test_exceptions.py`, `test_command_result.py` | Shared types |
| `test_namespace_metadata.py` | Label and annotation CRUD against a mocked Kubernetes API |

Fixtures live in `conftest.py`: `vcluster_manager` (with the Kubernetes clients
mocked), `mock_kubeconfig_yaml`, and sample list/describe payloads.

## Checks

```bash
make check      # flake8 (max-line-length 180) + mypy
make test-cov   # pytest with coverage; this is what CI runs
```

mypy excludes `src/tests` and runs with `check_untyped_defs` and
`warn_return_any` on.
