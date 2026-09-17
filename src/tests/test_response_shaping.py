"""Tests for the size and shape of what tools send back to the model."""

import json
from unittest.mock import MagicMock, patch

from tools.vcluster import MAX_RESPONSE_CHARS, LIST_DROP_KEYS, _emit, _project
from utils.result import Result
from utils.vcluster_manager import MAX_ERROR_CHARS, CommandResult, _clip


class TestEmit:
    """Tests for the shared response serializer."""

    def test_json_is_compact(self):
        """No whitespace padding - the SDK would otherwise pretty-print it."""
        assert _emit({"a": 1, "b": [1, 2]}) == '{"a":1,"b":[1,2]}'

    def test_str_passes_through(self):
        """A str return is what bypasses the SDK's indent=2 conversion."""
        assert _emit("already text") == "already text"

    def test_command_result_is_flattened(self):
        """CommandResult is not JSON-serializable on its own."""
        payload = json.loads(_emit(CommandResult(exit_code=0, output="done")))

        assert payload == {"exit_code": 0, "output": "done"}

    def test_oversized_output_is_truncated_with_a_marker(self):
        """A `vcluster call ... -o yaml` must not be able to fill the context."""
        result = _emit("x" * (MAX_RESPONSE_CHARS + 500))

        assert result.startswith("x" * 100)
        assert "[truncated: 500 more chars]" in result
        assert len(result) < MAX_RESPONSE_CHARS + 100

    def test_output_at_the_limit_is_untouched(self):
        """Off-by-one guard on the cap."""
        assert _emit("x" * MAX_RESPONSE_CHARS) == "x" * MAX_RESPONSE_CHARS


class TestProjection:
    """Tests for the default field projection on vcluster_list."""

    def test_drops_the_redundant_timestamp(self):
        """Created and AgeSeconds are the same fact twice."""
        entries = [{"Name": "a", "Status": "Running", "Created": "2026-09-13T07:20:50+02:00", "AgeSeconds": 399735}]

        assert _project(entries, LIST_DROP_KEYS) == [
            {"Name": "a", "Status": "Running", "AgeSeconds": 399735}
        ]

    def test_unknown_keys_are_kept(self):
        """A denylist: a field a future CLI adds must reach the model."""
        entries = [{"Name": "a", "Distro": "k3s", "SomethingNew": 1}]

        assert _project(entries, LIST_DROP_KEYS) == entries

    def test_non_list_passes_through(self):
        assert _project({"a": 1}, LIST_DROP_KEYS) == {"a": 1}

    def test_non_dict_entries_pass_through(self):
        assert _project(["a", 1], LIST_DROP_KEYS) == ["a", 1]

    def test_full_flag_skips_projection(self):
        """vcluster_list(full=True) returns every field the CLI emitted."""
        from tools.vcluster import vcluster_list

        entries = [{"Name": "a", "Created": "2026-09-13T07:20:50+02:00"}]

        with (
            patch("tools.vcluster.setup_kubernetes"),
            patch("tools.vcluster.VClusterManager") as MockManager,
        ):
            mock_manager = MagicMock()
            mock_manager.list.return_value = Result.ok(entries)
            MockManager.return_value = mock_manager

            assert json.loads(vcluster_list(full=True)) == entries
            assert json.loads(vcluster_list()) == [{"Name": "a"}]


class TestErrorClipping:
    """Tests for stderr echoed back inside error messages."""

    def test_short_error_is_untouched(self):
        assert _clip("boom") == "boom"

    def test_helm_dump_is_clipped(self):
        """A failed `vcluster create` emits an entire helm dump."""
        result = _clip("y" * (MAX_ERROR_CHARS + 42))

        assert "[truncated: 42 more chars]" in result
        assert len(result) < MAX_ERROR_CHARS + 60


class TestRunCommandStreams:
    """Tests for which stream _run_command keeps."""

    def test_nonzero_exit_keeps_stdout_when_present(self):
        """A partial-success command used to lose its stdout entirely."""
        from utils.vcluster_manager import VClusterManager

        with patch("utils.vcluster_manager.client"):
            manager = VClusterManager()

        completed = MagicMock(returncode=1, stdout="partial results", stderr="a warning")

        with patch("utils.vcluster_manager.subprocess.run", return_value=completed):
            result = manager._run_command(["vcluster", "list"])

        assert result.exit_code == 1
        assert result.output == "partial results"

    def test_nonzero_exit_falls_back_to_stderr(self):
        from utils.vcluster_manager import VClusterManager

        with patch("utils.vcluster_manager.client"):
            manager = VClusterManager()

        completed = MagicMock(returncode=1, stdout="", stderr="the real error")

        with patch("utils.vcluster_manager.subprocess.run", return_value=completed):
            result = manager._run_command(["vcluster", "list"])

        assert result.output == "the real error"
