"""
Simple MCP Client Manager - Completely Generic.

This module provides a clean, simple way to connect to MCP servers and
dynamically fetch tools without any server-specific code.
"""

from typing import List
from langchain.tools import Tool

from .mcp_adapter import MCPServerAdapter


class MCPClientManager:
    """Completely generic MCP client that works with any MCP server adapter."""

    def __init__(self):
        self.adapters: List[MCPServerAdapter] = []

    def register_adapter(self, adapter: MCPServerAdapter):
        """
        Register an MCP server adapter.

        Args:
            adapter: An instance of MCPServerAdapter
        """
        self.adapters.append(adapter)
        print(f"📝 Registered MCP server: {adapter.name}")

    async def get_tools(self) -> List[Tool]:
        """Fetch tools dynamically from all registered MCP server adapters."""
        all_tools = []

        for adapter in self.adapters:
            print(f"🔧 Fetching tools from {adapter.name}...")
            try:
                # Use the adapter's fetch_tools method
                tools_info = await adapter.fetch_tools()

                # Wrap each tool using the adapter's wrap_tool method
                for tool_meta in tools_info:
                    langchain_tool = adapter.wrap_tool(tool_meta)
                    all_tools.append(langchain_tool)

                print(f"✅ Loaded {len(tools_info)} tools from {adapter.name}")

            except Exception as e:
                print(f"❌ Failed to fetch tools from {adapter.name}: {e}")

        print(f"🎯 Total tools available: {len(all_tools)}")
        return all_tools
