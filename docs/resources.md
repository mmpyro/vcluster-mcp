# Resources

Two read-only, URI-addressed views of the vcluster environment. Use them to
browse state; use [tools](tools.md) to change it.

`vcluster://clusters` and `vcluster://{namespace}/{name}` were removed: they
duplicated `vcluster_list` and `vcluster_describe`, and every client paid for
both listings. Use those tools instead.

All return `application/json`. Errors come back in band as
`{"error": "..."}` with a well-formed body, never as an exception.

| URI | Returns |
| --- | --- |
| `vcluster://{namespace}/{name}/certs` | Control-plane certificate report |
| `vcluster://{namespace}/metadata` | Labels and annotations on a namespace |

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
