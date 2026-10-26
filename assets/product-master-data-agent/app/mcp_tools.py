"""
MCP tool indirection layer.

This module is the single owned entry point for loading MCP tools.
Tests patch `mcp_tools.get_mcp_tools` to return mock tools from mcp-mock.json.
Agent code imports ONLY from here — never from mcp_providers.agw directly.
"""
import json
import logging
import os
from pathlib import Path

logger = logging.getLogger(__name__)


async def get_mcp_tools() -> list:
    """
    Load MCP tools from the Agent Gateway.

    In test mode (IBD_TESTING=true or IBD_TESTING=1), returns structured tools
    built from mcp-mock.json.
    In production, loads tools from the Agent Gateway via mcp_providers.agw.
    """
    ibd_testing = os.environ.get("IBD_TESTING", "").lower()
    if ibd_testing in ("true", "1"):
        return _load_mock_tools()

    from mcp_providers.agw import get_mcp_tools as _agw_get_mcp_tools
    return await _agw_get_mcp_tools()


def _load_mock_tools() -> list:
    """Load mock tools from mcp-mock.json for local testing."""
    from langchain_core.tools import StructuredTool

    mock_file = Path(__file__).parent.parent / "mcp-mock.json"
    if not mock_file.exists():
        logger.warning("mcp-mock.json not found at %s — returning empty tool list", mock_file)
        return []

    with open(mock_file) as f:
        mock_data = json.load(f)

    tools = []
    for server_slug, server in mock_data.get("servers", {}).items():
        for tool_name, tool_def in server.get("tools", {}).items():
            mock_response = tool_def.get("mock_response", {})

            def make_tool_fn(response=mock_response):
                def tool_fn(**kwargs):
                    return response
                return tool_fn

            tools.append(
                StructuredTool.from_function(
                    func=make_tool_fn(),
                    name=f"mcp_{server_slug}__{tool_name}",
                    description=tool_def.get("description", ""),
                )
            )

    logger.info("Loaded %d mock MCP tools from mcp-mock.json", len(tools))
    return tools
