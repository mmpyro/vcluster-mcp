"""Tests for CLI command operations."""

import json
import pytest
from unittest.mock import patch
from utils.exceptions import ValidationError
from utils.vcluster_manager import CommandResult


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
