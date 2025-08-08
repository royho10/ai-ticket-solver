"""
Multi-MCP Client Package

Provides scalable MCP client architecture with support for multiple MCP servers:
- Generic MCP client framework
- Server-specific adapters (Atlassian, future servers)
- Clean separation between generic and server-specific functionality
"""

from .agent import (
    MultiMCPAgent,
    ClaudeJiraAgent,
    create_multi_mcp_agent,
    create_claude_jira_agent,
    create_jira_agent,
)

from .base_client import (
    GenericMCPClient,
    BaseMCPServerAdapter,
    MCPServerConfig,
    MCPTransportType,
)

from .atlassian_adapter import AtlassianMCPAdapter, create_atlassian_adapter

# Backward compatibility
__all__ = [
    # Main agent classes
    "MultiMCPAgent",
    "ClaudeJiraAgent",
    # Factory functions
    "create_multi_mcp_agent",
    "create_claude_jira_agent",
    "create_jira_agent",
    # Core framework classes
    "GenericMCPClient",
    "BaseMCPServerAdapter",
    "MCPServerConfig",
    "MCPTransportType",
    # Adapter classes
    "AtlassianMCPAdapter",
    "create_atlassian_adapter",
]
