# Tools

16 tools, grouped by what they do. Every tool takes `kubeconfig_path` as its
last parameter (see the limitation note in [index.md](index.md#known-limitations)).

All tools return their result directly on success, or `{"error": "..."}` on
failure — they do not raise.

## Lifecycle

### `vcluster_create`

Creates a vcluster. `--connect=false` is always passed, so your kube context is
never switched implicitly.

| Parameter | Type | Default | Notes |
| --- | --- | --- | --- |
| `name` | `str` | — | DNS-1123 label |
| `values` | `str \| list[str]` | `None` | Values file path(s). Merged left to right, last wins. |
| `upgrade` | `bool` | `None` | Upgrade instead of failing if it already exists |
| `namespace` | `str` | `None` | Omitted means the current context's namespace |
| `set_values` | `dict[str, str]` | `None` | Inline helm values. **Values may not contain commas** — helm splits on them. |
| `chart_version` | `str` | `None` | e.g. `"0.36.0"` |
| `chart_repo` | `str` | `None` | Chart repository URL |
| `chart_name` | `str` | `None` | Chart name |
| `expose` | `bool` | `False` | Create a LoadBalancer service |
| `create_namespace` | `bool` | `None` | Only `False` emits a flag; the CLI creates it by default |
| `kube_config_context_name` | `str` | `None` | Override the generated context name |

```
vcluster_create(
    "my-cluster",
    namespace="my-ns",
    set_values={"sync.toHost.ingresses.enabled": "true"},
    chart_version="0.36.0",
)
```

### `vcluster_delete`

> **Changed in 1.0.0.** The host namespace is now preserved by default.

| Parameter | Type | Default | Notes |
| --- | --- | --- | --- |
| `name` | `str` | — | |
| `namespace` | `str` | `None` | Defaults to `vcluster-<name>` |
| `delete_namespace` | `bool` | `False` | **Destructive.** Deletes the namespace and every other workload in it. |
| `keep_pvc` | `bool` | `False` | Retain the data volume |
| `ignore_not_found` | `bool` | `False` | Makes retries idempotent |
| `wait` | `bool` | `True` | `False` returns immediately |

With `delete_namespace=False` the CLI still applies its own
`--auto-delete-namespace`, which removes only namespaces vcluster itself
created. A pre-existing shared namespace is left alone.

### `vcluster_pause` / `vcluster_resume`

`(name, namespace, kubeconfig_path)`. Suspend or restore a vcluster without
losing state.

## Access

### `vcluster_kubeconfig`

Exports credentials without switching your context.

| Parameter | Type | Default | Notes |
| --- | --- | --- | --- |
| `name` | `str` | — | |
| `namespace` | `str` | `None` | Defaults to `vcluster-<name>` |
| `server` | `str` | `None` | http(s) URL of the vcluster API |
| `insecure` | `bool` | `False` | Writes a kubeconfig that skips TLS verification |

Returns:

```json
{
  "kubeconfig_path": "/var/folders/.../vcluster-my-cluster-a1b2.yaml",
  "context": "vcluster_my-cluster_vcluster-my-cluster",
  "server": "https://localhost:8443"
}
```

The file is created `0600` via `mkstemp`. **The caller owns it** — delete it
when finished. Pass the path to other tools rather than reading it; it contains
client certificates.

**If the vcluster is not directly reachable this times out after 60s.** The CLI
falls back to port-forwarding and never exits, and the kubeconfig it would print
points at a local port served by the process being killed. Pass
`server=<ingress or LoadBalancer URL>` to get a standalone kubeconfig, or create
the vcluster with `expose=True`.

### `vcluster_call`

`(name, command, namespace, kubeconfig_path)`. Runs one command inside the
vcluster via `vcluster connect ... -- <command>`. The command is split with
`shlex`, so quoted arguments work. No shell is involved.

```
vcluster_call("my-cluster", "kubectl get pods -n default")
```

### `vcluster_disconnect`

`(kubeconfig_path)`. Restores the original kube context.

## Observability

### `vcluster_list`

`(kubeconfig_path)`. All vclusters in the current context, as JSON.

### `vcluster_describe`

`(name, namespace, kubeconfig_path)`. Full status and configuration for one
vcluster. Reports a friendly "not found" rather than a raw CLI error.

### `vcluster_certs_check`

`(name, namespace, kubeconfig_path)`. Control-plane certificate expiry, via
`vcluster certs check --output json`. Read-only and safe to call freely.

Worth running whenever a vcluster looks healthy in `vcluster_list` but is
unreachable — expired certificates surface only as opaque TLS failures.

Rotation is deliberately **not** exposed. Use the CLI directly if you need it:
`vcluster certs rotate` restarts the control plane, and `vcluster certs
rotate-ca` invalidates every kubeconfig previously issued for that vcluster.

## Namespace metadata

Six tools operating directly against the Kubernetes API, not the vcluster CLI:

| Tool | Signature |
| --- | --- |
| `get_namespace_labels` | `(namespace, kubeconfig_path)` |
| `set_namespace_label` | `(namespace, key, value, kubeconfig_path)` |
| `delete_namespace_label` | `(namespace, key, kubeconfig_path)` |
| `get_namespace_annotations` | `(namespace, kubeconfig_path)` |
| `set_namespace_annotation` | `(namespace, key, value, kubeconfig_path)` |
| `delete_namespace_annotation` | `(namespace, key, kubeconfig_path)` |

Deletes are idempotent — removing a key that is not present succeeds.

## Validation

Inputs are validated before any subprocess runs. A failure returns
`{"error": "Validation error for '<field>': <reason>"}`.

| Field | Rule |
| --- | --- |
| `name`, `namespace` | `^[a-z0-9]([-a-z0-9]*[a-z0-9])?$` |
| `values` | Every path must exist and be readable |
| `set_values` keys | `^[A-Za-z0-9_][A-Za-z0-9_.\[\]-]*$` |
| `set_values` values | Must be a string; no commas or control characters |
| `chart_*`, `kube_config_context_name` | Non-empty, must not start with `-` |
| `server` | Must be an `http(s)` URL |
| `command` | Non-empty, must parse with `shlex` |
