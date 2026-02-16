.PHONY: sync sync-dev unittest test-cov test-integration dev help lint typecheck check

help:
	@echo "Available commands:"
	@echo "  sync             - Install production dependencies"
	@echo "  sync-dev         - Install all dependencies including development"
	@echo "  unittest         - Run only unit tests (excluding integration)"
	@echo "  test-cov         - Run all tests with coverage report"
	@echo "  test-integration - Run only integration tests"
	@echo "  lint             - Run flake8 linting"
	@echo "  typecheck        - Run mypy type checking"
	@echo "  check            - Run both linting and type checking"
	@echo "  dev              - Start MCP server in development mode"

sync:
	uv sync --no-dev

sync-dev:
	uv sync

unittest:
	uv run pytest

test-cov:
	uv run pytest --cov=src --cov-report=term-missing --cov-report=xml --junit-xml=test-results.xml

lint:
	uv run flake8 src

typecheck:
	uv run mypy src

check: lint typecheck

dev:
	uv run mcp dev ./src/server.py

