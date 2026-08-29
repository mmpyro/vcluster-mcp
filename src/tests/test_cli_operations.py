"""Tests for CLI command operations."""

import json
import os
import stat
import pytest
from unittest.mock import patch
from utils.exceptions import ValidationError, VClusterTimeoutError
from utils.vcluster_manager import CommandResult, KUBECONFIG_TIMEOUT_SECONDS


class TestVClusterList:
    """Tests for vcluster list operation."""

    def test_list_success(self, vcluster_manager, mock_successful_vcluster_list):
        """Test successful vcluster list."""
        mock_result = CommandResult(
            exit_code=0,
            output=json.dumps(mock_successful_vcluster_list),
        )

        with patch.object(vcluster_manager, "_run_command", return_value=mock_result):
            result = vcluster_manager.list()

        assert result.is_ok
        assert result.value == mock_successful_vcluster_list

    def test_list_with_dict_response(self, vcluster_manager):
        """Test list when response is a dict with items."""
        response = {"items": [{"name": "test"}]}
        mock_result = CommandResult(exit_code=0, output=json.dumps(response))

        with patch.object(vcluster_manager, "_run_command", return_value=mock_result):
            result = vcluster_manager.list()

        assert result.is_ok
        assert result.value == [{"name": "test"}]

    def test_list_failure(self, vcluster_manager):
        """Test list when command fails."""
        mock_result = CommandResult(exit_code=1, output="Command failed")

        with patch.object(vcluster_manager, "_run_command", return_value=mock_result):
            result = vcluster_manager.list()

        assert result.is_err
        assert "vcluster list failed" in result.error

    def test_list_json_decode_error(self, vcluster_manager):
        """Test list when JSON parsing fails."""
        mock_result = CommandResult(exit_code=0, output="not valid json")

        with patch.object(vcluster_manager, "_run_command", return_value=mock_result):
            result = vcluster_manager.list()

        assert result.is_err
        assert "Failed to parse" in result.error

    def test_list_cli_error(self, vcluster_manager):
        """Test list when CLI is not found — should return error result."""
        mock_result = CommandResult(exit_code=1, output="CLI not found")

        with patch.object(vcluster_manager, "_run_command", return_value=mock_result):
            result = vcluster_manager.list()

        assert result.is_err
        assert "vcluster list failed" in result.error


class TestVClusterDescribe:
    """Tests for vcluster describe operation."""

    def test_describe_success(self, vcluster_manager, mock_successful_vcluster_describe):
        """Test successful vcluster describe."""
        mock_result = CommandResult(
            exit_code=0,
            output=json.dumps(mock_successful_vcluster_describe),
        )

        with patch.object(vcluster_manager, "_run_command", return_value=mock_result):
            result = vcluster_manager.describe("test-cluster")

        assert result.is_ok
        assert result.value == mock_successful_vcluster_describe

    def test_describe_with_namespace(self, vcluster_manager, mock_successful_vcluster_describe):
        """Test describe with custom namespace."""
        mock_result = CommandResult(
            exit_code=0,
            output=json.dumps(mock_successful_vcluster_describe),
        )

        with patch.object(vcluster_manager, "_run_command", return_value=mock_result):
            result = vcluster_manager.describe("test-cluster", namespace="custom-ns")

        assert result.is_ok

    def test_describe_not_found(self, vcluster_manager):
        """Test describe when vcluster doesn't exist."""
        mock_result = CommandResult(exit_code=1, output="VCluster 'test' not found")

        with patch.object(vcluster_manager, "_run_command", return_value=mock_result):
            result = vcluster_manager.describe("test")

        assert result.is_err
        assert "not found" in result.error

    def test_describe_not_found_does_not_exist(self, vcluster_manager):
        """Test describe when vcluster 'does not exist'."""
        mock_result = CommandResult(exit_code=1, output="VCluster does not exist")

        with patch.object(vcluster_manager, "_run_command", return_value=mock_result):
            result = vcluster_manager.describe("test")

        assert result.is_err
        assert "not found" in result.error

    def test_describe_validation_error_empty_name(self, vcluster_manager):
        """Test describe with empty name raises ValidationError."""
        with pytest.raises(ValidationError):
            vcluster_manager.describe("")

    def test_describe_validation_error_invalid_name(self, vcluster_manager):
        """Test describe with invalid name raises ValidationError."""
        with pytest.raises(ValidationError):
            vcluster_manager.describe("InvalidName")


class TestVClusterPauseResume:
    """Tests for vcluster pause and resume operations."""

    def test_pause_success(self, vcluster_manager):
        """Test successful vcluster pause."""
        mock_result = CommandResult(exit_code=0, output="Paused successfully")

        with patch.object(vcluster_manager, "_run_command", return_value=mock_result):
            result = vcluster_manager.pause("test-cluster")

        assert result.is_ok

    def test_resume_success(self, vcluster_manager):
        """Test successful vcluster resume."""
        mock_result = CommandResult(exit_code=0, output="Resumed successfully")

        with patch.object(vcluster_manager, "_run_command", return_value=mock_result):
            result = vcluster_manager.resume("test-cluster")

        assert result.is_ok

    def test_pause_failure(self, vcluster_manager):
        """Test pause when command fails."""
        mock_result = CommandResult(exit_code=1, output="Pause failed")

        with patch.object(vcluster_manager, "_run_command", return_value=mock_result):
            result = vcluster_manager.pause("test-cluster")

        assert result.is_err

    def test_resume_failure(self, vcluster_manager):
        """Test resume when command fails."""
        mock_result = CommandResult(exit_code=1, output="Resume failed")

        with patch.object(vcluster_manager, "_run_command", return_value=mock_result):
            result = vcluster_manager.resume("test-cluster")

        assert result.is_err

    def test_pause_validation_error(self, vcluster_manager):
        """Test pause with invalid name raises ValidationError."""
        with pytest.raises(ValidationError):
            vcluster_manager.pause("InvalidName")

    def test_resume_validation_error(self, vcluster_manager):
        """Test resume with invalid name raises ValidationError."""
        with pytest.raises(ValidationError):
            vcluster_manager.resume("InvalidName")


class TestVClusterDelete:
    """Tests for vcluster delete operation."""

    def test_delete_success(self, vcluster_manager):
        """Test successful vcluster delete."""
        mock_result = CommandResult(exit_code=0, output="Deleted successfully")

        with patch.object(vcluster_manager, "_run_command", return_value=mock_result):
            result = vcluster_manager.delete("test-cluster")

        assert result.is_ok

    def test_delete_failure(self, vcluster_manager):
        """Test delete when command fails."""
        mock_result = CommandResult(exit_code=1, output="Delete failed")

        with patch.object(vcluster_manager, "_run_command", return_value=mock_result):
            result = vcluster_manager.delete("test-cluster")

        assert result.is_err
        assert "vcluster delete failed" in result.error

    def test_delete_validation_error(self, vcluster_manager):
        """Test delete with invalid name raises ValidationError."""
        with pytest.raises(ValidationError):
            vcluster_manager.delete("InvalidName")

    def test_delete_default_argv_preserves_namespace(self, vcluster_manager):
        """Test delete does not pass --delete-namespace by default.

        This is the regression guard for the destructive default: deleting a
        vcluster must not take out the host namespace and everything in it.
        """
        mock_result = CommandResult(exit_code=0, output="Deleted successfully")

        with patch.object(
            vcluster_manager, "_run_command", return_value=mock_result
        ) as mock_run:
            result = vcluster_manager.delete("test-cluster")

        assert result.is_ok
        call_args = mock_run.call_args[0][0]
        assert call_args == [
            "vcluster", "delete", "test-cluster", "-n", "vcluster-test-cluster",
        ]
        assert "--delete-namespace" not in call_args

    def test_delete_with_delete_namespace(self, vcluster_manager):
        """Test delete_namespace=True opts into destroying the namespace."""
        mock_result = CommandResult(exit_code=0, output="Deleted successfully")

        with patch.object(
            vcluster_manager, "_run_command", return_value=mock_result
        ) as mock_run:
            result = vcluster_manager.delete("test-cluster", delete_namespace=True)

        assert result.is_ok
        call_args = mock_run.call_args[0][0]
        assert call_args == [
            "vcluster", "delete", "test-cluster", "-n", "vcluster-test-cluster",
            "--delete-namespace",
        ]

    def test_delete_all_flags(self, vcluster_manager):
        """Test delete emits every flag in the documented order."""
        mock_result = CommandResult(exit_code=0, output="Deleted successfully")

        with patch.object(
            vcluster_manager, "_run_command", return_value=mock_result
        ) as mock_run:
            result = vcluster_manager.delete(
                "test-cluster",
                namespace="custom-ns",
                delete_namespace=True,
                keep_pvc=True,
                ignore_not_found=True,
                wait=False,
            )

        assert result.is_ok
        call_args = mock_run.call_args[0][0]
        assert call_args == [
            "vcluster", "delete", "test-cluster", "-n", "custom-ns",
            "--delete-namespace", "--keep-pvc", "--ignore-not-found", "--wait=false",
        ]

    def test_delete_wait_true_omits_flag(self, vcluster_manager):
        """Test wait=True matches the CLI default and emits nothing."""
        mock_result = CommandResult(exit_code=0, output="Deleted successfully")

        with patch.object(
            vcluster_manager, "_run_command", return_value=mock_result
        ) as mock_run:
            vcluster_manager.delete("test-cluster", wait=True)

        call_args = mock_run.call_args[0][0]
        assert not any(arg.startswith("--wait") for arg in call_args)

    def test_delete_validation_error_invalid_namespace(self, vcluster_manager):
        """Test delete with invalid namespace raises ValidationError."""
        with pytest.raises(ValidationError):
            vcluster_manager.delete("test-cluster", namespace="Invalid_NS")


class TestVClusterCreate:
    """Tests for vcluster create operation."""

    def test_create_success(self, vcluster_manager):
        """Test successful vcluster create."""
        mock_result = CommandResult(exit_code=0, output="Created successfully")

        with patch.object(vcluster_manager, "_run_command", return_value=mock_result):
            result = vcluster_manager.create("new-cluster")

        assert result.is_ok

    def test_create_with_values_file(self, vcluster_manager, tmp_path):
        """Test create with values file."""
        values_file = tmp_path / "values.yaml"
        values_file.write_text("replicas: 1")

        mock_result = CommandResult(exit_code=0, output="Created successfully")

        with patch.object(vcluster_manager, "_run_command", return_value=mock_result):
            result = vcluster_manager.create("new-cluster", values=str(values_file))

        assert result.is_ok

    def test_create_failure(self, vcluster_manager):
        """Test create when command fails."""
        mock_result = CommandResult(exit_code=1, output="Create failed")

        with patch.object(vcluster_manager, "_run_command", return_value=mock_result):
            result = vcluster_manager.create("new-cluster")

        assert result.is_err
        assert "vcluster create failed" in result.error

    def test_create_validation_error_invalid_name(self, vcluster_manager):
        """Test create with invalid name raises ValidationError."""
        with pytest.raises(ValidationError):
            vcluster_manager.create("InvalidName")

    def test_create_validation_error_nonexistent_values_file(self, vcluster_manager):
        """Test create with nonexistent values file raises ValidationError."""
        with pytest.raises(ValidationError):
            vcluster_manager.create("new-cluster", values="/nonexistent.yaml")

    def test_create_with_upgrade(self, vcluster_manager):
        """Test create with upgrade flag appends --upgrade to command."""
        mock_result = CommandResult(exit_code=0, output="Upgraded successfully")

        with patch.object(
            vcluster_manager, "_run_command", return_value=mock_result
        ) as mock_run:
            result = vcluster_manager.create("new-cluster", upgrade=True)

        assert result.is_ok
        call_args = mock_run.call_args[0][0]
        assert "--upgrade" in call_args

    def test_create_without_upgrade(self, vcluster_manager):
        """Test create without upgrade flag does not append --upgrade."""
        mock_result = CommandResult(exit_code=0, output="Created successfully")

        with patch.object(
            vcluster_manager, "_run_command", return_value=mock_result
        ) as mock_run:
            result = vcluster_manager.create("new-cluster")

        assert result.is_ok
        call_args = mock_run.call_args[0][0]
        assert "--upgrade" not in call_args

    def test_create_with_values_and_upgrade(self, vcluster_manager, tmp_path):
        """Test create with both values file and upgrade flag."""
        values_file = tmp_path / "values.yaml"
        values_file.write_text("replicas: 1")

        mock_result = CommandResult(exit_code=0, output="Created successfully")

        with patch.object(
            vcluster_manager, "_run_command", return_value=mock_result
        ) as mock_run:
            result = vcluster_manager.create(
                "new-cluster", values=str(values_file), upgrade=True
            )

        assert result.is_ok
        call_args = mock_run.call_args[0][0]
        assert "--values" in call_args
        assert "--upgrade" in call_args

    def test_create_default_argv(self, vcluster_manager):
        """Test create with no options emits the minimal command."""
        mock_result = CommandResult(exit_code=0, output="Created successfully")

        with patch.object(
            vcluster_manager, "_run_command", return_value=mock_result
        ) as mock_run:
            result = vcluster_manager.create("new-cluster")

        assert result.is_ok
        assert mock_run.call_args[0][0] == [
            "vcluster", "create", "new-cluster", "--connect=false",
        ]

    def test_create_with_namespace(self, vcluster_manager):
        """Test create passes -n when a namespace is given."""
        mock_result = CommandResult(exit_code=0, output="Created successfully")

        with patch.object(
            vcluster_manager, "_run_command", return_value=mock_result
        ) as mock_run:
            result = vcluster_manager.create("new-cluster", namespace="custom-ns")

        assert result.is_ok
        assert mock_run.call_args[0][0] == [
            "vcluster", "create", "new-cluster", "--connect=false", "-n", "custom-ns",
        ]

    def test_create_with_multiple_values_files(self, vcluster_manager, tmp_path):
        """Test create repeats --values and preserves caller order.

        Helm merges values files left to right, so the order is meaningful and
        must not be sorted.
        """
        first = tmp_path / "base.yaml"
        first.write_text("replicas: 1")
        second = tmp_path / "override.yaml"
        second.write_text("replicas: 2")

        mock_result = CommandResult(exit_code=0, output="Created successfully")

        with patch.object(
            vcluster_manager, "_run_command", return_value=mock_result
        ) as mock_run:
            result = vcluster_manager.create(
                "new-cluster", values=[str(first), str(second)]
            )

        assert result.is_ok
        assert mock_run.call_args[0][0] == [
            "vcluster", "create", "new-cluster", "--connect=false",
            "--values", str(first), "--values", str(second),
        ]

    def test_create_set_values_are_sorted(self, vcluster_manager):
        """Test --set pairs are emitted in sorted key order for determinism."""
        mock_result = CommandResult(exit_code=0, output="Created successfully")

        with patch.object(
            vcluster_manager, "_run_command", return_value=mock_result
        ) as mock_run:
            result = vcluster_manager.create(
                "new-cluster", set_values={"b.second": "2", "a.first": "1"}
            )

        assert result.is_ok
        assert mock_run.call_args[0][0] == [
            "vcluster", "create", "new-cluster", "--connect=false",
            "--set", "a.first=1", "--set", "b.second=2",
        ]

    def test_create_chart_flags(self, vcluster_manager):
        """Test chart pinning flags are passed through."""
        mock_result = CommandResult(exit_code=0, output="Created successfully")

        with patch.object(
            vcluster_manager, "_run_command", return_value=mock_result
        ) as mock_run:
            result = vcluster_manager.create(
                "new-cluster",
                chart_version="0.36.0",
                chart_repo="https://charts.loft.sh",
                chart_name="vcluster",
            )

        assert result.is_ok
        assert mock_run.call_args[0][0] == [
            "vcluster", "create", "new-cluster", "--connect=false",
            "--chart-version", "0.36.0",
            "--chart-repo", "https://charts.loft.sh",
            "--chart-name", "vcluster",
        ]

    def test_create_namespace_flag_omitted_by_default(self, vcluster_manager):
        """Test --create-namespace is omitted when not explicitly disabled."""
        mock_result = CommandResult(exit_code=0, output="Created successfully")

        with patch.object(
            vcluster_manager, "_run_command", return_value=mock_result
        ) as mock_run:
            vcluster_manager.create("new-cluster")

        call_args = mock_run.call_args[0][0]
        assert not any(arg.startswith("--create-namespace") for arg in call_args)

    def test_create_namespace_flag_disabled(self, vcluster_manager):
        """Test create_namespace=False emits the negated flag with '='."""
        mock_result = CommandResult(exit_code=0, output="Created successfully")

        with patch.object(
            vcluster_manager, "_run_command", return_value=mock_result
        ) as mock_run:
            vcluster_manager.create("new-cluster", create_namespace=False)

        assert "--create-namespace=false" in mock_run.call_args[0][0]

    def test_create_all_flags(self, vcluster_manager, tmp_path):
        """Test the full flag set in the documented order."""
        values_file = tmp_path / "values.yaml"
        values_file.write_text("replicas: 1")

        mock_result = CommandResult(exit_code=0, output="Created successfully")

        with patch.object(
            vcluster_manager, "_run_command", return_value=mock_result
        ) as mock_run:
            result = vcluster_manager.create(
                "new-cluster",
                values=str(values_file),
                upgrade=True,
                namespace="custom-ns",
                set_values={"sync.toHost.ingresses.enabled": "true"},
                chart_version="0.36.0",
                chart_repo="https://charts.loft.sh",
                chart_name="vcluster",
                expose=True,
                create_namespace=False,
                kube_config_context_name="my-context",
            )

        assert result.is_ok
        assert mock_run.call_args[0][0] == [
            "vcluster", "create", "new-cluster", "--connect=false",
            "-n", "custom-ns",
            "--values", str(values_file),
            "--set", "sync.toHost.ingresses.enabled=true",
            "--chart-version", "0.36.0",
            "--chart-repo", "https://charts.loft.sh",
            "--chart-name", "vcluster",
            "--kube-config-context-name", "my-context",
            "--expose",
            "--create-namespace=false",
            "--upgrade",
        ]

    def test_create_validation_error_invalid_namespace(self, vcluster_manager):
        """Test create with invalid namespace raises ValidationError."""
        with pytest.raises(ValidationError):
            vcluster_manager.create("new-cluster", namespace="Invalid_NS")

    @pytest.mark.parametrize("key", ["a=b", "a,b", "-x", "a b", ""])
    def test_create_validation_error_invalid_set_key(self, vcluster_manager, key):
        """Test malformed --set keys are rejected."""
        with pytest.raises(ValidationError):
            vcluster_manager.create("new-cluster", set_values={key: "1"})

    def test_create_validation_error_set_value_with_comma(self, vcluster_manager):
        """Test comma in a --set value is rejected.

        Helm splits --set on commas, so the value would silently become two
        separate assignments.
        """
        with pytest.raises(ValidationError):
            vcluster_manager.create("new-cluster", set_values={"a.b": "one,two"})

    def test_create_validation_error_chart_version_leading_dash(self, vcluster_manager):
        """Test a chart version starting with '-' is rejected as flag-like."""
        with pytest.raises(ValidationError):
            vcluster_manager.create("new-cluster", chart_version="--evil")

    def test_create_validation_error_missing_values_file_in_list(self, vcluster_manager, tmp_path):
        """Test every entry in a values list is validated."""
        good = tmp_path / "values.yaml"
        good.write_text("replicas: 1")

        with pytest.raises(ValidationError):
            vcluster_manager.create(
                "new-cluster", values=[str(good), "/nonexistent.yaml"]
            )


class TestVClusterCall:
    """Tests for vcluster call operation."""

    def test_call_success_default_namespace(self, vcluster_manager):
        """Test successful command execution with default namespace."""
        mock_result = CommandResult(
            exit_code=0, output="NAME          READY   STATUS\npod-1         1/1     Running"
        )

        with patch.object(
            vcluster_manager, "_run_command", return_value=mock_result
        ) as mock_run:
            result = vcluster_manager.call("test-cluster", "kubectl get pods")

        assert result.is_ok
        assert result.value.exit_code == 0
        assert "pod-1" in result.value.output

        call_args = mock_run.call_args[0][0]
        assert call_args == [
            "vcluster", "connect", "test-cluster",
            "-n", "vcluster-test-cluster", "-s", "--",
            "kubectl", "get", "pods",
        ]

    def test_call_success_custom_namespace(self, vcluster_manager):
        """Test successful command execution with custom namespace."""
        mock_result = CommandResult(exit_code=0, output="ok")

        with patch.object(
            vcluster_manager, "_run_command", return_value=mock_result
        ) as mock_run:
            result = vcluster_manager.call(
                "test-cluster", "kubectl get nodes", namespace="custom-ns"
            )

        assert result.is_ok
        call_args = mock_run.call_args[0][0]
        assert "-n" in call_args
        ns_index = call_args.index("-n")
        assert call_args[ns_index + 1] == "custom-ns"

    def test_call_failure(self, vcluster_manager):
        """Test call when the executed command fails."""
        mock_result = CommandResult(exit_code=1, output="connection refused")

        with patch.object(vcluster_manager, "_run_command", return_value=mock_result):
            result = vcluster_manager.call("test-cluster", "kubectl get pods")

        assert result.is_err
        assert "vcluster call failed" in result.error

    def test_call_validation_error_empty_name(self, vcluster_manager):
        """Test call with empty name raises ValidationError."""
        with pytest.raises(ValidationError):
            vcluster_manager.call("", "kubectl get pods")

    def test_call_validation_error_invalid_name(self, vcluster_manager):
        """Test call with invalid name raises ValidationError."""
        with pytest.raises(ValidationError):
            vcluster_manager.call("InvalidName", "kubectl get pods")

    def test_call_validation_error_empty_command(self, vcluster_manager):
        """Test call with empty command raises ValidationError."""
        with pytest.raises(ValidationError):
            vcluster_manager.call("test-cluster", "")

    def test_call_validation_error_whitespace_command(self, vcluster_manager):
        """Test call with whitespace-only command raises ValidationError."""
        with pytest.raises(ValidationError):
            vcluster_manager.call("test-cluster", "   ")

    def test_call_command_with_quoted_args(self, vcluster_manager):
        """Test call correctly splits command with quoted arguments."""
        mock_result = CommandResult(exit_code=0, output="done")

        with patch.object(
            vcluster_manager, "_run_command", return_value=mock_result
        ) as mock_run:
            result = vcluster_manager.call(
                "test-cluster", 'kubectl get pods -l "app=nginx"'
            )

        assert result.is_ok
        call_args = mock_run.call_args[0][0]
        # shlex.split should parse the quoted argument correctly
        assert "app=nginx" in call_args

    def test_call_invalid_command_syntax(self, vcluster_manager):
        """Test call with unbalanced quotes raises ValidationError."""
        with pytest.raises(ValidationError):
            vcluster_manager.call("test-cluster", 'kubectl get pods -l "app=nginx')

    def test_call_validation_error_invalid_namespace(self, vcluster_manager):
        """Test call with invalid namespace raises ValidationError."""
        with pytest.raises(ValidationError):
            vcluster_manager.call(
                "test-cluster", "kubectl get pods", namespace="Invalid_NS"
            )


class TestVClusterDisconnect:
    """Tests for vcluster disconnect operation."""

    def test_disconnect_success(self, vcluster_manager):
        """Test successful vcluster disconnect."""
        mock_result = CommandResult(exit_code=0, output="Disconnected successfully")

        with patch.object(
            vcluster_manager, "_run_command", return_value=mock_result
        ) as mock_run:
            result = vcluster_manager.disconnect()

        assert result.is_ok
        assert result.value.exit_code == 0
        call_args = mock_run.call_args[0][0]
        assert call_args == ["vcluster", "disconnect", "-s"]

    def test_disconnect_failure(self, vcluster_manager):
        """Test disconnect when command fails."""
        mock_result = CommandResult(exit_code=1, output="Disconnect failed")

        with patch.object(vcluster_manager, "_run_command", return_value=mock_result):
            result = vcluster_manager.disconnect()

        assert result.is_err
        assert "vcluster disconnect failed" in result.error


class TestVClusterCertsCheck:
    """Tests for vcluster certs check operation."""

    def test_certs_check_argv(self, vcluster_manager):
        """Test the built command, including -s for clean JSON on stdout."""
        mock_result = CommandResult(exit_code=0, output='{"certificates": []}')

        with patch.object(
            vcluster_manager, "_run_command", return_value=mock_result
        ) as mock_run:
            result = vcluster_manager.certs_check("test-cluster")

        assert result.is_ok
        assert mock_run.call_args[0][0] == [
            "vcluster", "certs", "check", "test-cluster",
            "-n", "vcluster-test-cluster", "-s", "--output", "json",
        ]

    def test_certs_check_custom_namespace(self, vcluster_manager):
        """Test certs check honours an explicit namespace."""
        mock_result = CommandResult(exit_code=0, output="{}")

        with patch.object(
            vcluster_manager, "_run_command", return_value=mock_result
        ) as mock_run:
            result = vcluster_manager.certs_check("test-cluster", namespace="custom-ns")

        assert result.is_ok
        call_args = mock_run.call_args[0][0]
        assert call_args[call_args.index("-n") + 1] == "custom-ns"

    def test_certs_check_dict_response(self, vcluster_manager):
        """Test a JSON object response is returned as-is."""
        payload = {"apiserver.crt": {"expiry": "2027-01-01T00:00:00Z"}}
        mock_result = CommandResult(exit_code=0, output=json.dumps(payload))

        with patch.object(vcluster_manager, "_run_command", return_value=mock_result):
            result = vcluster_manager.certs_check("test-cluster")

        assert result.is_ok
        assert result.value == payload

    def test_certs_check_list_response(self, vcluster_manager):
        """Test a JSON array response is also accepted.

        The exact shape of `vcluster certs check --output json` is not pinned,
        so both shapes must survive.
        """
        payload = [{"name": "apiserver.crt", "expiry": "2027-01-01T00:00:00Z"}]
        mock_result = CommandResult(exit_code=0, output=json.dumps(payload))

        with patch.object(vcluster_manager, "_run_command", return_value=mock_result):
            result = vcluster_manager.certs_check("test-cluster")

        assert result.is_ok
        assert result.value == payload

    def test_certs_check_not_found(self, vcluster_manager):
        """Test a missing vcluster produces a friendly error."""
        mock_result = CommandResult(exit_code=1, output="Error: vcluster not found")

        with patch.object(vcluster_manager, "_run_command", return_value=mock_result):
            result = vcluster_manager.certs_check("missing-cluster")

        assert result.is_err
        assert "not found" in result.error

    def test_certs_check_failure(self, vcluster_manager):
        """Test a generic CLI failure is surfaced."""
        mock_result = CommandResult(exit_code=1, output="boom")

        with patch.object(vcluster_manager, "_run_command", return_value=mock_result):
            result = vcluster_manager.certs_check("test-cluster")

        assert result.is_err
        assert "vcluster certs check failed" in result.error

    def test_certs_check_json_decode_error(self, vcluster_manager):
        """Test unparseable output produces a parse error."""
        mock_result = CommandResult(exit_code=0, output="not json")

        with patch.object(vcluster_manager, "_run_command", return_value=mock_result):
            result = vcluster_manager.certs_check("test-cluster")

        assert result.is_err
        assert "Failed to parse" in result.error

    def test_certs_check_validation_error(self, vcluster_manager):
        """Test certs check with an invalid name raises ValidationError."""
        with pytest.raises(ValidationError):
            vcluster_manager.certs_check("InvalidName")


class TestVClusterKubeconfig:
    """Tests for vcluster kubeconfig export."""

    def test_kubeconfig_argv_and_file(self, vcluster_manager, mock_kubeconfig_yaml):
        """Test the built command, the 0600 file, and the parsed metadata."""
        mock_result = CommandResult(exit_code=0, output=mock_kubeconfig_yaml)

        with patch.object(
            vcluster_manager, "_run_command", return_value=mock_result
        ) as mock_run:
            result = vcluster_manager.kubeconfig("test-cluster")

        assert result.is_ok
        assert mock_run.call_args[0][0] == [
            "vcluster", "connect", "test-cluster", "-n", "vcluster-test-cluster",
            "-s", "--print", "--background-proxy=false",
        ]

        path = result.value["kubeconfig_path"]
        try:
            assert os.path.exists(path)
            assert stat.S_IMODE(os.stat(path).st_mode) == 0o600
            with open(path) as handle:
                assert handle.read() == mock_kubeconfig_yaml
            assert result.value["context"] == "vcluster_test-cluster_vcluster-test-cluster"
            assert result.value["server"] == "https://localhost:8443"
        finally:
            os.unlink(path)

    def test_kubeconfig_passes_timeout(self, vcluster_manager, mock_kubeconfig_yaml):
        """Test the export is bounded so it cannot wedge the server."""
        mock_result = CommandResult(exit_code=0, output=mock_kubeconfig_yaml)

        with patch.object(
            vcluster_manager, "_run_command", return_value=mock_result
        ) as mock_run:
            result = vcluster_manager.kubeconfig("test-cluster")

        assert mock_run.call_args.kwargs["timeout"] == KUBECONFIG_TIMEOUT_SECONDS
        os.unlink(result.value["kubeconfig_path"])

    def test_kubeconfig_all_flags(self, vcluster_manager, mock_kubeconfig_yaml):
        """Test server and insecure are appended in order."""
        mock_result = CommandResult(exit_code=0, output=mock_kubeconfig_yaml)

        with patch.object(
            vcluster_manager, "_run_command", return_value=mock_result
        ) as mock_run:
            result = vcluster_manager.kubeconfig(
                "test-cluster",
                namespace="custom-ns",
                server="https://vcluster.example.com",
                insecure=True,
            )

        assert result.is_ok
        assert mock_run.call_args[0][0] == [
            "vcluster", "connect", "test-cluster", "-n", "custom-ns",
            "-s", "--print", "--background-proxy=false",
            "--server", "https://vcluster.example.com",
            "--insecure",
        ]
        os.unlink(result.value["kubeconfig_path"])

    def test_kubeconfig_timeout_is_actionable(self, vcluster_manager):
        """Test a timeout explains that --server is the way out.

        Without --server the CLI port-forwards and never exits, so this is the
        expected outcome for a plain ClusterIP vcluster, not a rare edge case.
        """
        with patch.object(
            vcluster_manager,
            "_run_command",
            side_effect=VClusterTimeoutError("vcluster command timed out after 60.0s"),
        ):
            result = vcluster_manager.kubeconfig("test-cluster")

        assert result.is_err
        assert "timed out" in result.error
        assert "server=" in result.error

    def test_kubeconfig_failure(self, vcluster_manager):
        """Test a non-zero exit is surfaced."""
        mock_result = CommandResult(exit_code=1, output="boom")

        with patch.object(vcluster_manager, "_run_command", return_value=mock_result):
            result = vcluster_manager.kubeconfig("test-cluster")

        assert result.is_err
        assert "vcluster kubeconfig failed" in result.error

    def test_kubeconfig_not_found(self, vcluster_manager):
        """Test a missing vcluster produces a friendly error."""
        mock_result = CommandResult(exit_code=1, output="Error: vcluster not found")

        with patch.object(vcluster_manager, "_run_command", return_value=mock_result):
            result = vcluster_manager.kubeconfig("missing-cluster")

        assert result.is_err
        assert "not found" in result.error

    def test_kubeconfig_empty_output(self, vcluster_manager):
        """Test empty stdout does not produce a bogus credentials file."""
        mock_result = CommandResult(exit_code=0, output="   ")

        with patch.object(vcluster_manager, "_run_command", return_value=mock_result):
            result = vcluster_manager.kubeconfig("test-cluster")

        assert result.is_err
        assert "did not return a kubeconfig" in result.error

    def test_kubeconfig_malformed_yaml(self, vcluster_manager):
        """Test unparseable output is rejected rather than written to disk."""
        mock_result = CommandResult(exit_code=0, output="::not: yaml: [")

        with patch.object(vcluster_manager, "_run_command", return_value=mock_result):
            result = vcluster_manager.kubeconfig("test-cluster")

        assert result.is_err

    def test_kubeconfig_write_failure(self, vcluster_manager, mock_kubeconfig_yaml):
        """Test a write failure is returned rather than raised."""
        mock_result = CommandResult(exit_code=0, output=mock_kubeconfig_yaml)

        with (
            patch.object(vcluster_manager, "_run_command", return_value=mock_result),
            patch.object(
                vcluster_manager, "_write_kubeconfig", side_effect=OSError("read-only fs")
            ),
        ):
            result = vcluster_manager.kubeconfig("test-cluster")

        assert result.is_err
        assert "Failed to write kubeconfig" in result.error

    def test_kubeconfig_validation_error_invalid_name(self, vcluster_manager):
        """Test kubeconfig with an invalid name raises ValidationError."""
        with pytest.raises(ValidationError):
            vcluster_manager.kubeconfig("InvalidName")

    @pytest.mark.parametrize("server", ["notaurl", "ftp://x.example.com", "https://", "-x"])
    def test_kubeconfig_validation_error_invalid_server(self, vcluster_manager, server):
        """Test a malformed server URL raises ValidationError."""
        with pytest.raises(ValidationError):
            vcluster_manager.kubeconfig("test-cluster", server=server)
