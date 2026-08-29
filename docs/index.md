# vcluster MCP Server documentation

Version 1.0.0

An MCP server that wraps the [vcluster CLI](https://vcluster.com/docs) so an AI
assistant can manage virtual Kubernetes clusters. It exposes **16 tools**,
**6 prompts** and **4 resources**.

Only open-source vcluster CLI commands are used. Nothing here requires a
vCluster Platform / Pro licence.

## Contents

| Document | What it covers |
| --- | --- |
| [Tools](tools.md) | The 16 callable operations, their parameters and safety notes |
| [Prompts](prompts.md) | The 6 guided workflows and when each applies |
| [Resources](resources.md) | The 4 read-only URIs for browsing the environment |
| [Architecture](architecture.md) | How a tool call flows through the code, and where to add a new one |

## Quick reference

**Discover what exists**

```
vcluster_list()                          -> all vclusters
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
  are accepted and passed through unchanged.
