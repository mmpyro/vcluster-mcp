Implement an MCP server for managing vcluster.
Extend existing project structure.

# Implementation
Change src/utils/vcluster_manager.py implementation to wrap vcluster cli for list, create, update, delete, describe ,pause and resume vcluster.
Use k8s api for CRUD operation on vcluster namespace labels and annotations.

## Commands to wrap

### vcluster list
`vcluster list --output json` has to be wrapped in src/utils/vcluster_manager.py by method `list`. It should return an output as json file.

### vcluster describe
`vcluster describe <vcluster name> -n <vcluster namespace> --output json` has to be wrapped in src/utils/vcluster_manager.py by method `describe`. It should return an output as json file and take two input parameters vcluster name and vcluster namespace that is optional if not passed it has to be the same as vcluster name.

### vcluster pause
`vcluster pause <vcluster name> -n <vcluster namespace>  -s` has to be wrapped in src/utils/vcluster_manager.py by method `pause`. Vcluster namespace that is optional if not passed it has to be the same as vcluster name.

### vcluster resume
`vcluster resume <vcluster name> -n <vcluster namespace>  -s` has to be wrapped in src/utils/vcluster_manager.py by method `resume`. Vcluster namespace that is optional if not passed it has to be the same as vcluster name.

### vcluster delete
`vcluster delete <vcluster name> -n <vcluster namespace> --delete-namespace -s` has to be wrapped in src/utils/vcluster_manager.py by method `delete`. Vcluster namespace that is optional if not passed it has to be the same as vcluster name.

### vcluster create
`vcluster create <vcluster name> -s --connect=false --values <path to values file>` has to be wrapped in src/utils/vcluster_manager.py by method `create`. `values` as optional parameter and if not passed shoudn't be used. If passed implement error handling for not existing file etc.

