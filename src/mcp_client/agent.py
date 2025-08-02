"""
Claude Sonnet 4 + MCP Jira Agent

This is the modern replacement for the LangChain-based agent.
Uses Claude Sonnet 4 through Anthropic's API and connects to Jira via MCP.
"""

import asyncio
import os
from pathlib import Path
from typing import Optional, Dict, List
from dotenv import load_dotenv
import anthropic
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from mcp.types import Tool, Resource


# Load environment variables
env_path = Path.cwd() / ".env"
load_dotenv(dotenv_path=env_path)


class ClaudeJiraAgent:
    """Modern MCP-based Jira agent using Claude Sonnet 4."""

    def __init__(self, model: str = "claude-3-5-sonnet-20241022", temperature: float = 0, verbose: bool = True):
        """
        Initialize the Claude Jira Agent.
        
        Args:
            model: Claude model to use (claude-3-5-sonnet-20241022 is currently the latest)
            temperature: Temperature for Claude responses (0-1)
            verbose: Whether to print debug information
        """
        self.model = model
        self.temperature = temperature
        self.verbose = verbose
        
        # Initialize Anthropic client
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key or api_key == "your_anthropic_api_key_here":
            raise ValueError(
                "ANTHROPIC_API_KEY not found or not set. "
                "Please add your Anthropic API key to the .env file. "
                "Get one at: https://console.anthropic.com/account/keys"
            )
        
        self.anthropic_client = anthropic.Anthropic(api_key=api_key)
        self.mcp_session: Optional[ClientSession] = None
        self.available_tools: List[Tool] = []
        self.available_resources: List[Resource] = []

    async def initialize_mcp(self) -> bool:
        """
        Initialize connection to Atlassian MCP server.
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            if self.verbose:
                print("🔗 Initializing connection to Atlassian MCP server...")
            
            # For now, we'll use our custom MCP server since the official one isn't installed yet
            # TODO: Replace with official Atlassian MCP server when available
            server_params = StdioServerParameters(
                command="python",
                args=[str(Path(__file__).parent.parent / "mcp_server" / "jira_server.py")],
                env=dict(os.environ)  # Pass all environment variables
            )
            
            # Note: We'll create a context manager approach for the MCP session
            self._server_params = server_params
            
            if self.verbose:
                print("✅ MCP server parameters configured")
            
            return True
            
        except Exception as e:
            if self.verbose:
                print(f"❌ Failed to initialize MCP: {str(e)}")
            return False

    async def _execute_with_mcp(self, query: str) -> str:
        """Execute a query using MCP tools and Claude Sonnet 4."""
        try:
            async with stdio_client(self._server_params) as (read, write):
                async with ClientSession(read, write) as session:
                    await session.initialize()
                    
                    # Get available tools
                    tools_response = await session.list_tools()
                    self.available_tools = tools_response.tools
                    
                    # Get available resources
                    resources_response = await session.list_resources()
                    self.available_resources = resources_response.resources
                    
                    if self.verbose:
                        print(f"🔧 Available tools: {[tool.name for tool in self.available_tools]}")
                        print(f"📚 Available resources: {len(self.available_resources)} resources")
                    
                    # Create tool descriptions for Claude
                    tool_descriptions = []
                    for tool in self.available_tools:
                        tool_desc = {
                            "name": tool.name,
                            "description": tool.description,
                            "input_schema": tool.inputSchema
                        }
                        tool_descriptions.append(tool_desc)
                    
                    # Create the system prompt with available tools
                    system_prompt = self._create_system_prompt(tool_descriptions)
                    
                    # Initial Claude response to understand what tools to use
                    claude_response = self.anthropic_client.messages.create(
                        model=self.model,
                        max_tokens=1024,
                        temperature=self.temperature,
                        system=system_prompt,
                        messages=[
                            {"role": "user", "content": query}
                        ]
                    )
                    
                    response_text = claude_response.content[0].text
                    
                    if self.verbose:
                        print(f"🤖 Claude's initial response: {response_text}")
                    
                    # Simple tool detection - look for tool calls in Claude's response
                    # This is a basic implementation; in production, you'd use tool calling APIs
                    tool_results = []
                    
                    # Check if Claude wants to use specific tools
                    for tool in self.available_tools:
                        if tool.name.lower() in response_text.lower():
                            try:
                                if self.verbose:
                                    print(f"🔧 Executing tool: {tool.name}")
                                
                                # Execute the tool with basic parameters
                                # This is simplified - in production, you'd parse Claude's intent better
                                tool_result = await self._execute_tool(session, tool.name, query)
                                tool_results.append(f"Tool '{tool.name}' result: {tool_result}")
                                
                            except Exception as e:
                                tool_results.append(f"Tool '{tool.name}' failed: {str(e)}")
                    
                    # Get final response from Claude with tool results
                    if tool_results:
                        final_query = f"""
Original query: {query}

Tool execution results:
{chr(10).join(tool_results)}

Please provide a comprehensive response based on the tool results above.
"""
                        
                        final_response = self.anthropic_client.messages.create(
                            model=self.model,
                            max_tokens=1024,
                            temperature=self.temperature,
                            messages=[
                                {"role": "user", "content": final_query}
                            ]
                        )
                        
                        return final_response.content[0].text
                    
                    return response_text
                    
        except Exception as e:
            error_msg = f"❌ Error executing MCP query: {str(e)}"
            if self.verbose:
                print(error_msg)
            return error_msg

    async def _execute_tool(self, session: ClientSession, tool_name: str, query: str) -> str:
        """Execute a specific MCP tool."""
        try:
            # Extract issue key from query for tools that need it
            def extract_issue_key(text: str) -> str:
                """Extract Jira issue key from text (e.g., KAN-3, PROJ-123)."""
                import re
                # Look for pattern like KAN-3, PROJ-123, etc.
                pattern = r'\b[A-Z]+-\d+\b'
                matches = re.findall(pattern, text.upper())
                return matches[0] if matches else None
            
            if tool_name == "get_my_jira_issues":
                result = await session.call_tool(tool_name, arguments={})
            
            elif tool_name in ["get_jira_issue_summary", "get_jira_issue_description", "get_jira_issue_full_details"]:
                # These tools require an issue_key parameter
                issue_key = extract_issue_key(query)
                if not issue_key:
                    return f"Error: Could not find a valid Jira issue key in the query. Please specify an issue key like 'KAN-3'."
                
                result = await session.call_tool(tool_name, arguments={"issue_key": issue_key})
            
            else:
                # For any other tools, try with no arguments first
                result = await session.call_tool(tool_name, arguments={})
            
            # Extract text content from result
            if result.content and len(result.content) > 0:
                return result.content[0].text if hasattr(result.content[0], 'text') else str(result.content[0])
            
            return "No result returned"
            
        except Exception as e:
            return f"Tool execution failed: {str(e)}"

    def _create_system_prompt(self, tool_descriptions: List[Dict]) -> str:
        """Create system prompt for Claude with available tools."""
        tools_text = "\n".join([
            f"- {tool['name']}: {tool['description']}"
            for tool in tool_descriptions
        ])
        
        return f"""You are a helpful Jira assistant powered by Claude Sonnet 4. You can help users manage their Jira tickets, search for issues, get ticket details, and perform various Jira operations.

Available tools:
{tools_text}

IMPORTANT INSTRUCTIONS:
1. NEVER provide specific Jira issue details, counts, or status information without first using the appropriate tools
2. When asked about issues, tickets, or Jira data, you MUST use the tools to get current information
3. Do not make assumptions about issue counts, statuses, or content - always rely on tool results
4. Wait for tool execution results before providing specific details
5. Be accurate with numbers and counts - double-check your math when summarizing results

When a user asks about Jira issues:
1. Identify which tools to use (mention them by name)
2. Execute the tools to get current data  
3. Provide accurate information based ONLY on the tool results
4. Count carefully and be precise with numbers

You have access to the Jira instance at royho10.atlassian.net. Be helpful, accurate, and concise in your responses, but always use tools for current data."""

    async def run(self, query: str) -> str:
        """
        Run a query through the Claude Jira agent.
        
        Args:
            query: The user's question or request
            
        Returns:
            str: The agent's response
        """
        try:
            if not hasattr(self, '_server_params'):
                success = await self.initialize_mcp()
                if not success:
                    return "❌ Failed to initialize MCP connection. Please check your configuration."
            
            return await self._execute_with_mcp(query)
            
        except Exception as e:
            error_msg = f"❌ Error processing query: {str(e)}"
            if self.verbose:
                print(error_msg)
            return error_msg

    def run_sync(self, query: str) -> str:
        """
        Synchronous wrapper for the async run method.
        
        Args:
            query: The user's question or request
            
        Returns:
            str: The agent's response
        """
        return asyncio.run(self.run(query))


def create_claude_jira_agent(**kwargs) -> ClaudeJiraAgent:
    """
    Create a Claude Jira agent instance.
    
    Args:
        **kwargs: Arguments to pass to ClaudeJiraAgent constructor
        
    Returns:
        ClaudeJiraAgent: A new agent instance
    """
    return ClaudeJiraAgent(**kwargs)


# For backward compatibility with the old agent interface
def create_jira_agent():
    """Create a Jira agent instance (legacy compatibility)."""
    return create_claude_jira_agent()
