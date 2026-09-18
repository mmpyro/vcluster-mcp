# vcluster MCP Server documentation

Version 1.0.0

An MCP server that wraps the [vcluster CLI](https://vcluster.com/docs) so an AI
assistant can manage virtual Kubernetes clusters. It exposes **12 tools** and
**2 resources**.

Only open-source vcluster CLI commands are used. Nothing here requires a
vCluster Platform / Pro licence.

## Contents

| Document | What it covers |
| --- | --- |
| [Tools](tools.md) | The 12 callable operations, their parameters and safety notes |
| [Resources](resources.md) | The 2 read-only URIs for browsing the environment |
| [Architecture](architecture.md) | How a tool call flows through the code, and where to add a new one |

## Quick reference

**Discover what exists**

```
vcluster_list()                          -> all vclusters (identity + status)
vcluster_list(full=True)                 -> every field the CLI emits
vcluster_describe("my-cluster")          -> one vcluster in detail
```

**Create and tear down**

```
vcluster_create("my-cluster", namespace="my-ns", chart_version="0.36.0")
vcluster_delete("my-cluster", namespace="my-ns")     # namespace is preserved
```

**Get access**

```
vcluster_kubeconfig("my-cluster", server="https://vc.example.com")
  -> {"kubeconfig_path": "...", "context": "...", "server": "..."}

vcluster_call("my-cluster", "kubectl get pods -A")
```

**Diagnose**

```
vcluster_certs_check("my-cluster")       -> certificate expiry
```

## Requirements

- Python 3.13+
- [`vcluster` CLI](https://vcluster.com/docs/getting-started/installation) on `PATH` (developed against v0.36.0)
- `kubectl`, configured against the host cluster

## Known limitations

- **`kubeconfig_path` does not reach the CLI.** It configures the Python
  Kubernetes client only. The `vcluster` subprocess uses the ambient
  `KUBECONFIG` / `~/.kube/config`. Set `KUBECONFIG` in the MCP server's
  environment if you need a non-default kubeconfig.
- **Exported kubeconfig files are not cleaned up.** `vcluster_kubeconfig`
  returns a `0600` temp file path; the caller is responsible for deleting it.
- **Most commands have no timeout.** Only `vcluster_kubeconfig` is bounded
  (60s). An unreachable cluster can make other tools hang.
- **The `certs check` JSON shape is not pinned.** Both an object and an array
  are accepted and passed through unchanged. Against v0.36.0 it is an array of
  `{filename, subject, issuer, expiryTime, status}`.
- **`vcluster_kubeconfig` needs `server=` for an unreachable vcluster.** Without
  it, `vcluster connect --print` falls back to port-forwarding and never exits,
  so the tool returns the 60s timeout error.

## Response size

Responses are compact JSON strings, capped at `MAX_RESPONSE_CHARS` (20,000) with
an explicit `[truncated: N more chars]` marker. Stderr echoed into an error
message is capped separately at `MAX_ERROR_CHARS` (2,000).

Every tool is registered with `structured_output=False`. This is deliberate and
load-bearing: an `outputSchema` makes the SDK send each response twice, as both
`content` and `structuredContent`, and adds ~300 chars per tool to the listing
every client loads at startup. `src/tests/test_context_budget.py` fails if a new
tool omits the flag, or if the whole advertised surface exceeds 10,000 chars
(currently 8,868, down from 29,035).
