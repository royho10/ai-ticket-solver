"""
Atlassian MCP Server Adapter.

This adapter provides Atlassian-specific functionality for Jira and Confluence
using the official Atlassian MCP server.
"""

import re
import json
from typing import List, Optional, Dict, Any

from mcp import ClientSession
from .base_client import BaseMCPServerAdapter, MCPServerConfig, MCPTransportType


class AtlassianMCPAdapter(BaseMCPServerAdapter):
    """
    Adapter for the official Atlassian MCP server.

    Provides Jira and Confluence functionality through the official
    mcp.atlassian.com/v1/sse server.
    """

    def __init__(self, verbose: bool = True, mcp_verbose: bool = False):
        config = MCPServerConfig(
            name="Atlassian",
            transport_type=MCPTransportType.HTTP_SSE,
            url="https://mcp.atlassian.com/v1/sse",
        )
        super().__init__(config, verbose, mcp_verbose)
        self._atlassian_cloud_id: Optional[str] = None

    async def initialize_connection(self) -> bool:
        """Initialize connection to Atlassian MCP server."""
        try:
            # Server params are now set by the GenericMCPClient with verbosity control
            return True
        except Exception as e:
            if self.verbose:
                print(f"❌ Failed to initialize Atlassian MCP: {str(e)}")
            return False

    def parse_query_intent(self, query: str) -> List[tuple]:
        """
        Parse user query for Atlassian-specific intents.

        Returns list of (tool_name, parameters) tuples.
        """
        query_lower = query.lower()
        tools_to_execute = []

        # Create Issue Intent
        if self._is_create_issue_intent(query_lower):
            tools_to_execute.append(("createJiraIssue", query))

        # My Issues Intent (assigned OR reported)
        elif self._is_my_issues_intent(query_lower):
            jql = "assignee = currentUser() OR reporter = currentUser() ORDER BY updated DESC"
            tools_to_execute.append(("searchJiraIssuesUsingJql", jql))

        # All Issues Intent
        elif self._is_all_issues_intent(query_lower):
            tools_to_execute.append(
                ("searchJiraIssuesUsingJql", "ORDER BY updated DESC")
            )

        # Assigned to Me Intent
        elif self._is_assigned_to_me_intent(query_lower):
            jql = "assignee = currentUser() ORDER BY updated DESC"
            tools_to_execute.append(("searchJiraIssuesUsingJql", jql))

        # Specific Issue Key Intent
        issue_keys = self._extract_jira_issue_keys(query)
        if issue_keys:
            for issue_key in issue_keys[:3]:  # Limit to first 3
                tools_to_execute.append(("getJiraIssue", issue_key))

        # Search Intent
        elif self._is_search_intent(query_lower):
            search_terms = self._extract_search_terms(query, query_lower)
            jql = f'text ~ "{search_terms}" OR summary ~ "{search_terms}" ORDER BY updated DESC'
            tools_to_execute.append(("searchJiraIssuesUsingJql", jql))

        # General Jira Intent (fallback)
        elif self._is_general_jira_intent(query_lower):
            jql = "assignee = currentUser() OR reporter = currentUser() ORDER BY updated DESC"
            tools_to_execute.append(("searchJiraIssuesUsingJql", jql))

        # Confluence Intents
        elif self._is_confluence_spaces_intent(query_lower):
            tools_to_execute.append(("getConfluenceSpaces", {}))

        elif self._is_confluence_search_intent(query_lower):
            search_terms = self._extract_search_terms(query, query_lower)
            tools_to_execute.append(("searchConfluenceUsingCql", search_terms))

        return tools_to_execute

    def _is_create_issue_intent(self, query_lower: str) -> bool:
        """Check if query intends to create a new issue."""
        return any(
            phrase in query_lower
            for phrase in [
                "create",
                "new ticket",
                "new issue",
                "add ticket",
                "add issue",
            ]
        )

    def _is_my_issues_intent(self, query_lower: str) -> bool:
        """Check if query asks for user's issues (assigned OR reported)."""
        return any(
            phrase in query_lower
            for phrase in [
                "what jira issues i have",
                "what issues i have",
                "my jira issues",
                "issues i have",
                "what tickets do i have",
                "my tickets",
            ]
        )

    def _is_all_issues_intent(self, query_lower: str) -> bool:
        """Check if query asks for all issues."""
        return any(
            phrase in query_lower
            for phrase in [
                "all issues",
                "all my issues",
                "list all",
                "project issues",
                "all tickets",
                "everything",
                "show me all",
                "recent issues",
                "latest issues",
            ]
        )

    def _is_assigned_to_me_intent(self, query_lower: str) -> bool:
        """Check if query asks for issues assigned to user."""
        return any(
            phrase in query_lower
            for phrase in [
                "assigned to me",
                "what am i working on",
                "currently assigned",
                "my assigned",
                "working on",
            ]
        )

    def _is_search_intent(self, query_lower: str) -> bool:
        """Check if query is a search request."""
        return any(word in query_lower for word in ["search", "find", "related to"])

    def _is_general_jira_intent(self, query_lower: str) -> bool:
        """Check if query is generally about Jira."""
        return any(word in query_lower for word in ["issue", "ticket", "task", "jira"])

    def _is_confluence_spaces_intent(self, query_lower: str) -> bool:
        """Check if query asks for Confluence spaces."""
        return any(
            phrase in query_lower
            for phrase in ["confluence spaces", "what spaces", "list spaces"]
        )

    def _is_confluence_search_intent(self, query_lower: str) -> bool:
        """Check if query is about searching Confluence."""
        return any(
            phrase in query_lower
            for phrase in ["confluence", "search confluence", "find in confluence"]
        )

    def _extract_jira_issue_keys(self, query: str) -> List[str]:
        """Extract Jira issue keys (e.g., KAN-7) from query."""
        return re.findall(r"\b[A-Z]+-\d+\b", query.upper())

    def _extract_search_terms(self, original_query: str, query_lower: str) -> str:
        """Extract search terms from query."""
        # Remove common search words
        search_terms = original_query
        for word in ["find", "search", "related to", "confluence"]:
            search_terms = search_terms.replace(word, "").replace(word.capitalize(), "")

        return search_terms.strip()

    async def execute_server_specific_tool(
        self, session: ClientSession, tool_name: str, parameters: Any, **kwargs
    ) -> str:
        """Execute Atlassian-specific MCP tools with proper parameter handling."""

        # Get cloud ID if needed
        cloud_id = await self._get_atlassian_cloud_id(session)

        if tool_name == "searchJiraIssuesUsingJql":
            return await self._execute_jira_search(session, parameters, cloud_id)

        elif tool_name == "getJiraIssue":
            return await self._execute_get_jira_issue(session, parameters, cloud_id)

        elif tool_name == "createJiraIssue":
            return await self._execute_create_jira_issue(session, parameters, cloud_id)

        elif tool_name == "getConfluenceSpaces":
            return await self._execute_get_confluence_spaces(session, cloud_id)

        elif tool_name == "searchConfluenceUsingCql":
            return await self._execute_confluence_search(session, parameters, cloud_id)

        else:
            # Generic tool execution
            return await self._execute_generic_atlassian_tool(
                session, tool_name, parameters, cloud_id
            )

    async def _get_atlassian_cloud_id(self, session: ClientSession) -> Optional[str]:
        """Get Atlassian cloud ID for API routing."""
        if self._atlassian_cloud_id:
            return self._atlassian_cloud_id

        try:
            result = await session.call_tool("getAccessibleAtlassianResources", {})
            if hasattr(result, "content") and result.content:
                data = result.content[0].text
                resources = json.loads(data)
                if isinstance(resources, list) and len(resources) > 0:
                    self._atlassian_cloud_id = resources[0].get("id")
                    return self._atlassian_cloud_id
        except Exception as e:
            if self.verbose:
                print(f"⚠️ Could not get Atlassian cloud ID: {e}")

        return None

    async def _execute_jira_search(
        self, session: ClientSession, jql: str, cloud_id: Optional[str]
    ) -> str:
        """Execute JQL search with proper parameters."""
        args = {"jql": jql, "maxResults": 20}
        if cloud_id:
            args["cloudId"] = cloud_id

        result = await session.call_tool("searchJiraIssuesUsingJql", args)
        return self._extract_tool_result_content(result)

    async def _execute_get_jira_issue(
        self, session: ClientSession, issue_key: str, cloud_id: Optional[str]
    ) -> str:
        """Get specific Jira issue details."""
        args = {"issueIdOrKey": issue_key}
        if cloud_id:
            args["cloudId"] = cloud_id

        result = await session.call_tool("getJiraIssue", args)
        return self._extract_tool_result_content(result)

    async def _execute_create_jira_issue(
        self, session: ClientSession, query: str, cloud_id: Optional[str]
    ) -> str:
        """Create new Jira issue with parsed parameters."""
        args = await self._parse_atlassian_create_issue_request(
            session, query, cloud_id
        )
        result = await session.call_tool("createJiraIssue", args)
        return self._extract_tool_result_content(result)

    async def _execute_get_confluence_spaces(
        self, session: ClientSession, cloud_id: Optional[str]
    ) -> str:
        """Get available Confluence spaces."""
        args = {}
        if cloud_id:
            args["cloudId"] = cloud_id

        result = await session.call_tool("getConfluenceSpaces", args)
        return self._extract_tool_result_content(result)

    async def _execute_confluence_search(
        self, session: ClientSession, search_terms: str, cloud_id: Optional[str]
    ) -> str:
        """Search Confluence using CQL."""
        args = {"cql": f'text ~ "{search_terms}"'}
        if cloud_id:
            args["cloudId"] = cloud_id

        result = await session.call_tool("searchConfluenceUsingCql", args)
        return self._extract_tool_result_content(result)

    async def _execute_generic_atlassian_tool(
        self,
        session: ClientSession,
        tool_name: str,
        parameters: Any,
        cloud_id: Optional[str],
    ) -> str:
        """Execute any other Atlassian tool generically."""
        if isinstance(parameters, str):
            args = {"query": parameters}
        elif isinstance(parameters, dict):
            args = parameters
        else:
            args = {"input": str(parameters)}

        if cloud_id:
            args["cloudId"] = cloud_id

        result = await session.call_tool(tool_name, args)
        return self._extract_tool_result_content(result)

    async def _parse_atlassian_create_issue_request(
        self, session: ClientSession, query: str, cloud_id: Optional[str]
    ) -> Dict[str, Any]:
        """Parse create issue request for Atlassian/Jira format."""

        # Extract issue details from query
        title_match = re.search(r'title[:\s]+"([^"]+)"', query, re.IGNORECASE)
        if not title_match:
            title_match = re.search(r'summary[:\s]+"([^"]+)"', query, re.IGNORECASE)
        summary = title_match.group(1) if title_match else "New Issue"

        desc_match = re.search(r'description[:\s]+"([^"]+)"', query, re.IGNORECASE)
        description = desc_match.group(1) if desc_match else "No description provided"

        type_match = re.search(r'(?:issue )?type[:\s]+"([^"]+)"', query, re.IGNORECASE)
        issue_type = type_match.group(1) if type_match else "Task"

        # Get available project
        project_key = await self._get_atlassian_default_project_key(session)

        args = {
            "projectKey": project_key,
            "summary": summary,
            "description": description,
            "issueType": issue_type,
        }

        if cloud_id:
            args["cloudId"] = cloud_id

        return args

    async def _get_atlassian_default_project_key(self, session: ClientSession) -> str:
        """Get the first available Jira project key."""
        try:
            result = await session.call_tool("getVisibleJiraProjects", {})
            if hasattr(result, "content") and result.content:
                data = result.content[0].text
                projects = json.loads(data)
                if isinstance(projects, list) and len(projects) > 0:
                    return projects[0].get("key", "KAN")
        except Exception:
            pass

        return "KAN"  # Fallback project key

    def _extract_tool_result_content(self, result) -> str:
        """Extract content from MCP tool result."""
        if hasattr(result, "content") and result.content:
            return (
                result.content[0].text
                if result.content[0].text
                else str(result.content)
            )
        return str(result)

    def format_capabilities_summary(self) -> str:
        """Format Atlassian-specific capabilities."""
        base_summary = super().format_capabilities_summary()

        # Add Atlassian-specific categorization
        jira_tools = [
            tool for tool in self.available_tools if "jira" in tool.name.lower()
        ]
        confluence_tools = [
            tool for tool in self.available_tools if "confluence" in tool.name.lower()
        ]

        if jira_tools or confluence_tools:
            base_summary += "\n**Tool Categories:**\n"
            base_summary += f"- Jira Tools: {len(jira_tools)}\n"
            base_summary += f"- Confluence Tools: {len(confluence_tools)}\n"
            base_summary += f"- Other Tools: {len(self.available_tools) - len(jira_tools) - len(confluence_tools)}\n"

        return base_summary


def create_atlassian_adapter(
    verbose: bool = True, mcp_verbose: bool = False
) -> AtlassianMCPAdapter:
    """
    Create an Atlassian MCP adapter instance.

    Args:
        verbose: Whether to enable verbose logging
        mcp_verbose: Whether to show verbose MCP protocol output (False = quieter operation)
    """
    return AtlassianMCPAdapter(verbose=verbose, mcp_verbose=mcp_verbose)
