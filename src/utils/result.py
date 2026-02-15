"""Type-safe Result type for operation outcomes."""

from dataclasses import dataclass
from typing import TypeVar, Generic, Optional, Callable, Union

T = TypeVar('T')
U = TypeVar('U')


class ResultState:
    """Enum-like class for result states."""
    SUCCESS = "success"
    FAILURE = "failure"


@dataclass(frozen=True)
class Result(Generic[T]):
    """A type-safe Result type for operation outcomes.

    This provides an alternative to exceptions for operations where
    returning failure is more appropriate than raising an exception.
    """
    _state: str
    _value: Optional[T]
    _error: Optional[str]

    def __post_init__(self):
        if self._state not in (ResultState.SUCCESS, ResultState.FAILURE):
            raise ValueError(f"Invalid state: {self._state}")
        if self._state == ResultState.SUCCESS and self._error is not None:
            raise ValueError("Cannot have error on success state")
        if self._state == ResultState.FAILURE and self._value is not None:
            raise ValueError("Cannot have value on failure state")

    @classmethod
    def ok(cls, value: T) -> 'Result[T]':
        """Create a successful result."""
        return cls(_state=ResultState.SUCCESS, _value=value, _error=None)

    @classmethod
    def err(cls, error: str) -> 'Result[T]':
        """Create an error result."""
        return cls(_state=ResultState.FAILURE, _value=None, _error=error)

    @property
    def is_ok(self) -> bool:
        """Check if result is successful."""
        return self._state == ResultState.SUCCESS

    @property
    def is_err(self) -> bool:
        """Check if result is an error."""
        return self._state == ResultState.FAILURE

    @property
    def value(self) -> Optional[T]:
        """Get the value if successful, None otherwise."""
        return self._value

    @property
    def error(self) -> Optional[str]:
        """Get the error message if failed, None otherwise."""
        return self._error

    def unwrap(self) -> T:
        """Get the value, raising an exception if error."""
        if self.is_err:
            raise ValueError(f"Cannot unwrap error result: {self._error}")
        return self._value

    def unwrap_or(self, default: T) -> T:
        """Get the value or a default if error."""
        return self._value if self.is_ok else default

    def unwrap_err(self) -> str:
        """Get the error message, raising if not an error."""
        if self.is_ok:
            raise ValueError("Cannot unwrap_err on success result")
        return self._error

    def map(self, fn: Callable[[T], U]) -> 'Result[U]':
        """Transform the value if successful."""
        if self.is_ok:
            try:
                return Result.ok(fn(self._value))
            except Exception as e:
                return Result.err(f"Map transformation failed: {e}")
        return Result.err(self._error)

    def map_err(self, fn: Callable[[str], str]) -> 'Result[T]':
        """Transform the error message if failed."""
        if self.is_err:
            return Result.err(fn(self._error))
        return self

    def flat_map(self, fn: Callable[[T], 'Result[U]']) -> 'Result[U]':
        """Chain another result-returning function."""
        if self.is_ok:
            return fn(self._value)
        return Result.err(self._error)

    def __repr__(self) -> str:
        if self.is_ok:
            return f"Result.ok({self._value!r})"
        return f"Result.err({self._error!r})"


# Type alias for convenience
Ok = Result.ok
Err = Result.err
