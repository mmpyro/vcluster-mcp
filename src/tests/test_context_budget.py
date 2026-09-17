"""Guards on the context cost of the advertised MCP surface.

Every client loads the tool/resource listing into its context before making a
single call, so the size of that listing is a standing tax on every session.
These tests fail when it grows, and when a change reintroduces the duplicated
structured-output payload.
"""

import asyncio
import json

import tools  # noqa: F401  - registers the tools on the shared server
import resources  # noqa: F401  - registers the resources
from utils.mcp import Server

# Measured at 8,868 chars after the reduction, from a 29,035 baseline.
# Headroom is deliberately tight: a new tool should be budgeted for, not absorbed.
MAX_SURFACE_CHARS = 10_000


def _size(items) -> int:
    """Serialized size of a listing, the way it goes over the wire."""
    return len(
        json.dumps(
            [i.model_dump(exclude_none=True, by_alias=True) for i in items],
            separators=(",", ":"),
            default=str,
        )
    )


def _surface():
    """Collect the four advertised listings."""
    mcp = Server().mcp

    async def gather():
        return (
            await mcp.list_tools(),
            await mcp.list_resources(),
            await mcp.list_resource_templates(),
        )

    return asyncio.run(gather())


def test_advertised_surface_within_budget():
    """The whole advertised surface stays under the context budget."""
    tool_list, res, templates = _surface()
    total = _size(tool_list) + _size(res) + _size(templates)

    breakdown = "\n".join(
        f"  {t.name:28} {len(json.dumps(t.model_dump(exclude_none=True, by_alias=True), separators=(',', ':'), default=str)):5}"
        for t in sorted(tool_list, key=lambda t: t.name)
    )

    assert total <= MAX_SURFACE_CHARS, (
        f"advertised surface is {total} chars, budget is {MAX_SURFACE_CHARS}.\n"
        f"Trim a description or drop a tool rather than raising the budget.\n{breakdown}"
    )


def test_no_tool_advertises_an_output_schema():
    """Every tool keeps structured_output=False.

    An outputSchema costs ~300 chars of listing and makes the SDK send each
    response twice, as both `content` and `structuredContent`.
    """
    tool_list, _, _ = _surface()
    offenders = [t.name for t in tool_list if t.output_schema]

    assert not offenders, f"missing structured_output=False on: {offenders}"


def test_no_prompts_are_registered():
    """Prompts were removed; their bodies re-listed the tool schemas."""
    mcp = Server().mcp
    assert asyncio.run(mcp.list_prompts()) == []
