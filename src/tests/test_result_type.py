"""Tests for Result type behavior used by VClusterManager."""

import pytest
from utils.result import Result


class TestResultType:
    """Tests for Result type behavior used by VClusterManager."""

    def test_result_ok_properties(self):
        """Test Result.ok properties."""
        result = Result.ok("test value")

        assert result.is_ok is True
        assert result.is_err is False
        assert result.value == "test value"
        assert result.error is None

    def test_result_err_properties(self):
        """Test Result.err properties."""
        result = Result.err("error message")

        assert result.is_ok is False
        assert result.is_err is True
        assert result.value is None
        assert result.error == "error message"

    def test_result_unwrap_on_ok(self):
        """Test unwrap on success result."""
        result = Result.ok("value")
        assert result.unwrap() == "value"

    def test_result_unwrap_on_err_raises(self):
        """Test unwrap on error result raises ValueError."""
        result = Result.err("error")

        with pytest.raises(ValueError, match="Cannot unwrap error result"):
            result.unwrap()

    def test_result_unwrap_or(self):
        """Test unwrap_or returns value or default."""
        ok_result = Result.ok("value")
        assert ok_result.unwrap_or("default") == "value"

        err_result = Result.err("error")
        assert err_result.unwrap_or("default") == "default"

    def test_result_map(self):
        """Test Result.map transforms value."""
        result = Result.ok(5).map(lambda x: x * 2)
        assert result.is_ok
        assert result.value == 10

        err_result = Result.err("error").map(lambda x: x * 2)
        assert err_result.is_err

    def test_result_flat_map(self):
        """Test Result.flat_map chains results."""
        def divide_by_two(x):
            if x == 0:
                return Result.err("Cannot divide by zero")
            return Result.ok(x / 2)

        ok_result = Result.ok(10).flat_map(divide_by_two)
        assert ok_result.is_ok
        assert ok_result.value == 5

        zero_result = Result.ok(0).flat_map(divide_by_two)
        assert zero_result.is_err
