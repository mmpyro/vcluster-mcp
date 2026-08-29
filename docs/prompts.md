# Prompts

Six prompts. Each returns a formatted instruction string that primes the
assistant for one kind of task and lists only the tools relevant to it.

All parameters are optional strings; an empty value degrades to generic
guidance rather than failing.

| Prompt | Parameters | Use when |
| --- | --- | --- |
| `vcluster_management_assistant` | `kubeconfig_path` | General entry point — catalogues all 16 tools |
| `vcluster_lifecycle_assistant` | `operation`, `vcluster_name`, `kubeconfig_path` | Creating, deleting, pausing or resuming |
| `vcluster_access_assistant` | `vcluster_name`, `namespace`, `kubeconfig_path` | Getting credentials or running commands inside a vcluster |
| `vcluster_certificates_assistant` | `vcluster_name`, `namespace`, `kubeconfig_path` | Inspecting certificate expiry |
| `namespace_metadata_assistant` | `namespace`, `metadata_type`, `kubeconfig_path` | Managing labels and annotations |
| `vcluster_troubleshooting_assistant` | `issue_description`, `kubeconfig_path` | Diagnosing a reported problem |

## `vcluster_management_assistant`

The broad one. Lists every tool grouped into lifecycle, operations, labels and
annotations, plus key concepts (what a vcluster is, what pause/resume mean, the
difference between labels and annotations). Start here when the user's goal is
not yet clear.

## `vcluster_lifecycle_assistant`

`operation` is the required focus — `create`, `delete`, `pause`, `resume` or
`describe`. Carries per-operation guidance, including the safety rules for
delete:

- `delete_namespace` defaults to `False`, so the host namespace survives
- Only pass `True` after confirming with the user that nothing unrelated lives there
- `ignore_not_found=True` for retries, `keep_pvc=True` to keep data

## `vcluster_access_assistant`

Covers the decision that is easy to get wrong: `vcluster_call` for one or two
commands, `vcluster_kubeconfig` when another tool needs credentials or many
commands are coming. Includes the rules for handling the exported file — pass
the path, never read the contents, delete it afterwards — and explains the
port-forward timeout and how `server=` avoids it.

## `vcluster_certificates_assistant`

Explains why expired certificates are hard to spot: a vcluster can look healthy
in `vcluster_list` while being unreachable, and the only symptom is an opaque
TLS error. Walks through reading expiry dates and flagging anything expiring
within 30 days.

Rotation is not a tool, so this prompt instructs the assistant to hand the user
the CLI command and state the consequence — particularly that `rotate-ca`
invalidates every kubeconfig previously issued for that vcluster.

## `namespace_metadata_assistant`

`metadata_type` selects `labels` or `annotations`. Explains the practical
difference (labels are for selection and are syntax-restricted; annotations are
freeform and are not selectable) and lists common use cases.

## `vcluster_troubleshooting_assistant`

`issue_description` is free text. Lists the diagnostic tools and seven common
failure modes with their symptoms:

1. vcluster not starting
2. vcluster not listed
3. cannot pause or resume
4. deletion issues
5. metadata issues
6. expired or invalid certificates
7. cannot get a kubeconfig

Ends with a fixed workflow: gather, identify, check metadata, act, verify.
