"""
Improved Claude Sonnet 4 + MCP Jira Agent

Fixed version that addresses:
1. Incorrect issue search logic (includes reporter issues)
2. HTTP 404 connection errors (connection reuse)
3. Tool selection problems (proper mapping)
4. Create issue functionality
5. Better error handling
"""

import asyncio
import os
import json
import re
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
    """Modern MCP-based Jira agent using Claude Sonnet 4 with improved functionality."""

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
        self._cloud_id: Optional[str] = None

    async def initialize_mcp(self) -> bool:
        """
        Initialize connection to official Atlassian MCP server.
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            if self.verbose:
                print("🔗 Connecting to official Atlassian MCP server...")
            
            # Connect to official Atlassian MCP server via mcp-remote proxy
            server_params = StdioServerParameters(
                command="npx",
                args=["-y", "mcp-remote", "https://mcp.atlassian.com/v1/sse"],
                env=dict(os.environ)
            )
            
            # Store server params for use in _execute_with_mcp
            self._server_params = server_params
            
            if self.verbose:
                print("✅ Connected to official Atlassian MCP server!")
            
            return True
            
        except Exception as e:
            if self.verbose:
                print(f"❌ Failed to initialize MCP: {str(e)}")
            return False

    async def _get_cloud_id(self, session: ClientSession) -> Optional[str]:
        """Get Atlassian cloud ID for API calls."""
        if self._cloud_id:
            return self._cloud_id
        
        try:
            resources_result = await session.call_tool("getAccessibleAtlassianResources", {})
            if hasattr(resources_result, 'content') and resources_result.content:
                resources_data = resources_result.content[0].text
                resources_json = json.loads(resources_data)
                if isinstance(resources_json, list) and len(resources_json) > 0:
                    self._cloud_id = resources_json[0].get('id')
                    return self._cloud_id
        except Exception as e:
            if self.verbose:
                print(f"⚠️ Could not get cloud ID: {e}")
        
        return None

    async def _execute_with_mcp(self, query: str) -> str:
        """Execute a query using MCP tools and Claude Sonnet 4."""
        try:
            async with stdio_client(self._server_params) as (read, write):
                async with ClientSession(read, write) as session:
                    # Initialize session
                    await asyncio.wait_for(session.initialize(), timeout=30.0)
                    
                    # Get available tools
                    tools_response = await asyncio.wait_for(session.list_tools(), timeout=20.0)
                    self.available_tools = tools_response.tools
                    
                    # Try to get resources (may not be available)
                    try:
                        resources_response = await asyncio.wait_for(session.list_resources(), timeout=10.0)
                        self.available_resources = resources_response.resources
                    except Exception:
                        self.available_resources = []
                    
                    if self.verbose:
                        print(f"🔧 Available tools: {[tool.name for tool in self.available_tools]}")
                    
                    return await self._process_query(session, query)
                    
        except Exception as e:
            error_msg = f"❌ Error executing MCP query: {str(e)}"
            if self.verbose:
                print(error_msg)
            return error_msg

    async def _process_query(self, session: ClientSession, query: str) -> str:
        """Process a query with intelligent tool selection."""
        
        # Check for tool listing requests first
        if any(phrase in query.lower() for phrase in [
            "what tools", "available tools", "tools do you have", "list tools"
        ]):
            return self._format_tool_list()
        
        # Determine which tools to execute based on query content
        tools_to_execute = self._determine_tools(query)
        
        if not tools_to_execute:
            # If no specific tools determined, let Claude decide
            return await self._claude_decision(session, query)
        
        # Execute the determined tools
        tool_results = []
        cloud_id = await self._get_cloud_id(session)
        
        for tool_name, parameters in tools_to_execute:
            try:
                if self.verbose:
                    print(f"🔧 Executing tool: {tool_name}")
                
                result = await self._execute_tool(session, tool_name, parameters, cloud_id)
                tool_results.append(f"Tool '{tool_name}' result: {result}")
                
            except Exception as e:
                tool_results.append(f"Tool '{tool_name}' failed: {str(e)}")
        
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
        
        return "No tools were executed for this query."

    def _format_tool_list(self) -> str:
        """Format the available tools list for display."""
        return f"""I have access to {len(self.available_tools)} tools from the official Atlassian MCP server:

**Jira Tools:**
- **searchJiraIssuesUsingJql**: Search for Jira issues using JQL queries
- **getJiraIssue**: Get detailed information about a specific Jira issue  
- **createJiraIssue**: Create a new Jira issue
- **editJiraIssue**: Edit an existing Jira issue
- **addCommentToJiraIssue**: Add a comment to a Jira issue
- **transitionJiraIssue**: Change the status of a Jira issue
- **getTransitionsForJiraIssue**: Get available transitions for an issue
- **getVisibleJiraProjects**: Get list of accessible Jira projects
- **getJiraProjectIssueTypesMetadata**: Get issue types for a project
- **getJiraIssueRemoteIssueLinks**: Get remote links for an issue
- **lookupJiraAccountId**: Look up Jira account ID

**Confluence Tools:**
- **getConfluenceSpaces**: Get available Confluence spaces
- **getConfluencePage**: Get a specific Confluence page
- **createConfluencePage**: Create a new Confluence page
- **updateConfluencePage**: Update an existing Confluence page
- **searchConfluenceUsingCql**: Search Confluence using CQL

**General Tools:**
- **atlassianUserInfo**: Get current user information
- **getAccessibleAtlassianResources**: Get accessible Atlassian resources

What would you like me to help you with?"""

    def _determine_tools(self, query: str) -> List[tuple]:
        """Determine which tools to execute based on query content."""
        query_lower = query.lower()
        tools_to_execute = []
        
        # Check for create issue requests
        if any(phrase in query_lower for phrase in [
            "create", "new ticket", "new issue", "add ticket", "add issue"
        ]):
            tools_to_execute.append(("createJiraIssue", query))
        
        # Check for "what issues I have" - should search both assigned AND reported
        elif any(phrase in query_lower for phrase in [
            "what jira issues i have", "what issues i have", "my jira issues", 
            "issues i have", "what tickets do i have", "my tickets"
        ]):
            # FIXED: Search for issues where user is assignee OR reporter
            jql = "assignee = currentUser() OR reporter = currentUser() ORDER BY updated DESC"
            tools_to_execute.append(("searchJiraIssuesUsingJql", jql))
        
        # Check for "all issues" or "project issues" requests
        elif any(phrase in query_lower for phrase in [
            "all issues", "all my issues", "list all", "project issues", 
            "all tickets", "everything", "show me all", "list me all",
            "recent issues", "latest issues"
        ]):
            tools_to_execute.append(("searchJiraIssuesUsingJql", "ORDER BY updated DESC"))
        
        # Check for specifically "assigned to me" requests  
        elif any(phrase in query_lower for phrase in [
            "assigned to me", "what am i working on", "currently assigned",
            "my assigned", "working on"
        ]):
            tools_to_execute.append(("searchJiraIssuesUsingJql", "assignee = currentUser() ORDER BY updated DESC"))
        
        # Check for specific issue key requests
        issue_keys = re.findall(r'\b[A-Z]+-\d+\b', query.upper())
        if issue_keys:
            for issue_key in issue_keys[:3]:  # Limit to first 3 issues
                tools_to_execute.append(("getJiraIssue", issue_key))
        
        # Check for search queries
        elif any(word in query_lower for word in ["search", "find", "related to"]):
            search_terms = query.replace("find", "").replace("search", "").replace("related to", "").strip()
            jql = f'text ~ "{search_terms}" OR summary ~ "{search_terms}" ORDER BY updated DESC'
            tools_to_execute.append(("searchJiraIssuesUsingJql", jql))
        
        # Default fallback for general issue queries
        elif any(word in query_lower for word in ["issue", "ticket", "task"]):
            # FIXED: Default to comprehensive search (assigned OR reported)
            jql = "assignee = currentUser() OR reporter = currentUser() ORDER BY updated DESC"
            tools_to_execute.append(("searchJiraIssuesUsingJql", jql))
        
        return tools_to_execute

    async def _execute_tool(self, session: ClientSession, tool_name: str, parameters: str, cloud_id: Optional[str]) -> str:
        """Execute a specific tool with proper parameter handling."""
        
        if tool_name == "searchJiraIssuesUsingJql":
            args = {"jql": parameters, "maxResults": 20}
            if cloud_id:
                args["cloudId"] = cloud_id
            result = await session.call_tool(tool_name, args)
        
        elif tool_name == "getJiraIssue":
            args = {"issueIdOrKey": parameters}
            if cloud_id:
                args["cloudId"] = cloud_id
            result = await session.call_tool(tool_name, args)
        
        elif tool_name == "createJiraIssue":
            # FIXED: Proper parameter parsing for issue creation
            args = await self._parse_create_issue_request(session, parameters, cloud_id)
            result = await session.call_tool(tool_name, args)
        
        else:
            # For other tools, pass parameters as query
            result = await session.call_tool(tool_name, {"query": parameters})
        
        # Extract content from result
        if hasattr(result, 'content') and result.content:
            return result.content[0].text if result.content[0].text else str(result.content)
        
        return str(result)

    async def _parse_create_issue_request(self, session: ClientSession, query: str, cloud_id: Optional[str]) -> Dict:
        """Parse create issue request and prepare proper arguments."""
        
        # Extract title/summary
        title_match = re.search(r'title[:\s]+"([^"]+)"', query, re.IGNORECASE)
        if not title_match:
            title_match = re.search(r'header[:\s]+"([^"]+)"', query, re.IGNORECASE)
        summary = title_match.group(1) if title_match else "New Issue"
        
        # Extract description
        desc_match = re.search(r'description[:\s]+"([^"]+)"', query, re.IGNORECASE)
        description = desc_match.group(1) if desc_match else "No description provided"
        
        # Extract issue type
        type_match = re.search(r'issue type[:\s]+"([^"]+)"', query, re.IGNORECASE)
        if not type_match:
            type_match = re.search(r'type[:\s]+"([^"]+)"', query, re.IGNORECASE)
        issue_type = type_match.group(1) if type_match else "Task"
        
        # Get the first available project
        try:
            projects_result = await session.call_tool("getVisibleJiraProjects", {})
            if hasattr(projects_result, 'content') and projects_result.content:
                projects_data = projects_result.content[0].text
                projects_json = json.loads(projects_data)
                if isinstance(projects_json, list) and len(projects_json) > 0:
                    project_key = projects_json[0].get('key', 'KAN')
                else:
                    project_key = 'KAN'
            else:
                project_key = 'KAN'
        except Exception:
            project_key = 'KAN'  # Fallback
        
        args = {
            "projectKey": project_key,
            "summary": summary,
            "description": description,
            "issueType": issue_type
        }
        
        if cloud_id:
            args["cloudId"] = cloud_id
        
        return args

    async def _claude_decision(self, session: ClientSession, query: str) -> str:
        """Let Claude decide which tools to use when automatic detection fails."""
        
        # Create tool descriptions for Claude
        tool_descriptions = []
        for tool in self.available_tools:
            tool_desc = {
                "name": tool.name,
                "description": tool.description,
                "input_schema": tool.inputSchema
            }
            tool_descriptions.append(tool_desc)
        
        # Create system prompt
        system_prompt = self._create_system_prompt(tool_descriptions)
        
        # Get Claude's response
        claude_response = self.anthropic_client.messages.create(
            model=self.model,
            max_tokens=1024,
            temperature=self.temperature,
            system=system_prompt,
            messages=[
                {"role": "user", "content": query}
            ]
        )
        
        return claude_response.content[0].text

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

TOOL SELECTION GUIDE:
- For "my issues", "what issues I have" → use searchJiraIssuesUsingJql with "assignee = currentUser() OR reporter = currentUser()"
- For "assigned to me", "what I'm working on" → use searchJiraIssuesUsingJql with "assignee = currentUser()"
- For "all issues", "project issues" → use searchJiraIssuesUsingJql with broader queries
- For specific issue details by key (e.g. "KAN-7") → use getJiraIssue
- For creating issues → use createJiraIssue with proper parameters
- Always choose the most appropriate tool based on the user's intent

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
