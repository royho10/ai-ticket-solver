"""
Atlassian MCP Server Adapter.

This adapter implements the MCPServerAdapter interface for Atlassian MCP server.
Only contains Atlassian-specific server connection configuration.
"""

import os
from typing import Dict, Any, Optional
from mcp import StdioServerParameters

from .mcp_adapter import MCPServerAdapter

# Load environment variables from .env file
try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    # dotenv not available, assume environment variables are set
    pass


class AtlassianMCPAdapter(MCPServerAdapter):
    """Adapter for Atlassian MCP server."""

    def __init__(self, config: Dict[str, Any] = None):
        # Use environment variables for Jira configuration
        if config is None:
            config = {}
        super().__init__("Atlassian", config)
        self._cloud_id: Optional[str] = None

    def create_server_params(self) -> StdioServerParameters:
        """Create server parameters for official remote Atlassian MCP server."""

        # Prepare environment variables for API Token authentication
        env = {
            "ATLASSIAN_API_TOKEN": os.getenv("ATLASSIAN_API_TOKEN"),
            "ATLASSIAN_EMAIL": os.getenv("ATLASSIAN_EMAIL"),
            "ATLASSIAN_INSTANCE_URL": os.getenv("ATLASSIAN_INSTANCE_URL"),
        }

        # Remove None values
        env = {k: v for k, v in env.items() if v is not None}

        # Use the official remote Atlassian MCP server
        return StdioServerParameters(
            command="npx",
            args=["-y", "mcp-remote", "https://mcp.atlassian.com/v1/sse"],
            env=env,
        )

    def parse_tool_input(self, tool_name: str, raw_input: Any) -> Dict[str, Any]:
        """Parse tool input and add authentication parameters for Atlassian tools."""

        # Convert raw input to dict if it's a string
        if isinstance(raw_input, str):
            if tool_name in [
                "searchJiraIssuesUsingJql",
                "Atlassian_searchJiraIssuesUsingJql",
            ]:
                parsed_input = {"jql": raw_input}
            elif tool_name in ["getJiraIssue", "Atlassian_getJiraIssue"]:
                parsed_input = {"issueIdOrKey": raw_input}
            else:
                parsed_input = {"query": raw_input}
        elif isinstance(raw_input, dict):
            parsed_input = raw_input.copy()
        else:
            parsed_input = {"input": str(raw_input)}

        return parsed_input


def create_atlassian_adapter() -> AtlassianMCPAdapter:
    """Create Atlassian MCP adapter using environment variables."""
    return AtlassianMCPAdapter()
