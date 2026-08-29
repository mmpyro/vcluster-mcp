# Resources

Four read-only, URI-addressed views of the vcluster environment. Use them to
browse state; use [tools](tools.md) to change it.

All return `application/json`. Errors come back in band as
`{"error": "..."}` with a well-formed body, never as an exception.

| URI | Returns |
| --- | --- |
| `vcluster://clusters` | Every vcluster in the current context |
| `vcluster://{namespace}/{name}` | One vcluster in detail |
| `vcluster://{namespace}/{name}/certs` | Control-plane certificate report |
| `vcluster://{namespace}/metadata` | Labels and annotations on a namespace |

## `vcluster://clusters`

A static resource — no parameters. Equivalent to `vcluster_list`. The natural
starting point for discovering what exists before calling any tool.

```json
[
  {"name": "my-cluster", "namespace": "vcluster-my-cluster", "status": "Running"}
]
```

## `vcluster://{namespace}/{name}`

Equivalent to `vcluster_describe`. Note the namespace comes **first** in the
URI, unlike the tool signature where the name comes first.

```
vcluster://vcluster-my-cluster/my-cluster
```

## `vcluster://{namespace}/{name}/certs`

Equivalent to `vcluster_certs_check`.

```
vcluster://vcluster-my-cluster/my-cluster/certs
```

## `vcluster://{namespace}/metadata`

Combines `get_namespace_labels` and `get_namespace_annotations` into one
document, saving a round trip.

```json
{
  "namespace": "vcluster-my-cluster",
  "labels": {"team": "core"},
  "annotations": {"owner": "platform"}
}
```

If the namespace does not exist, the label read fails and the annotation read is
skipped, so the error is reported once.

## Resources vs tools

| | Resources | Tools |
| --- | --- | --- |
| Addressing | URI | Function call |
| Effects | Read-only | Read and write |
| `kubeconfig_path` | Not supported | Supported (with [caveats](index.md#known-limitations)) |

A URI cannot carry a kubeconfig path, so resources always use the default
kubeconfig from the environment. When you need a specific one, call the
equivalent tool instead.
