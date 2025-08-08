"""
Example GitHub MCP Server Adapter.

This is an example of how to create adapters for other MCP servers.
This demonstrates the extensibility of the Multi-MCP architecture.

NOTE: This is a placeholder example - actual GitHub MCP server would need
to be implemented or use an existing one.
"""

import re
from typing import List, Optional, Dict, Any

from mcp import ClientSession
from .base_client import BaseMCPServerAdapter, MCPServerConfig, MCPTransportType


class GitHubMCPAdapter(BaseMCPServerAdapter):
    """
    Example adapter for a hypothetical GitHub MCP server.

    This demonstrates how to extend the Multi-MCP architecture with new servers.
    """

    def __init__(self, verbose: bool = True):
        # Example configuration for a hypothetical GitHub MCP server
        config = MCPServerConfig(
            name="GitHub",
            transport_type=MCPTransportType.STDIO,
            command="npx",
            args=["-y", "@github/mcp-server"],  # Hypothetical package
        )
        super().__init__(config, verbose)
        self._github_token: Optional[str] = None

    async def initialize_connection(self) -> bool:
        """Initialize connection to GitHub MCP server."""
        try:
            self._server_params = self.config.to_server_params()
            return True
        except Exception as e:
            if self.verbose:
                print(f"❌ Failed to initialize GitHub MCP: {str(e)}")
            return False

    def parse_query_intent(self, query: str) -> List[tuple]:
        """
        Parse user query for GitHub-specific intents.

        Returns list of (tool_name, parameters) tuples.
        """
        query_lower = query.lower()
        tools_to_execute = []

        # Example GitHub-specific intents
        if self._is_list_repos_intent(query_lower):
            tools_to_execute.append(("listRepositories", {}))

        elif self._is_create_issue_intent(query_lower):
            tools_to_execute.append(("createIssue", query))

        elif self._is_list_prs_intent(query_lower):
            tools_to_execute.append(("listPullRequests", {}))

        # Extract repository references
        repo_refs = self._extract_repo_references(query)
        if repo_refs:
            for repo_ref in repo_refs[:3]:  # Limit to first 3
                tools_to_execute.append(("getRepository", repo_ref))

        return tools_to_execute

    def _is_list_repos_intent(self, query_lower: str) -> bool:
        """Check if query asks for GitHub repositories."""
        return any(
            phrase in query_lower
            for phrase in [
                "github repos",
                "my repositories",
                "list repos",
                "github repositories",
            ]
        )

    def _is_create_issue_intent(self, query_lower: str) -> bool:
        """Check if query intends to create a GitHub issue."""
        return (
            any(
                phrase in query_lower
                for phrase in [
                    "create github issue",
                    "new github issue",
                    "github issue",
                ]
            )
            and "create" in query_lower
        )

    def _is_list_prs_intent(self, query_lower: str) -> bool:
        """Check if query asks for pull requests."""
        return any(
            phrase in query_lower
            for phrase in ["pull requests", "prs", "github prs", "my pull requests"]
        )

    def _extract_repo_references(self, query: str) -> List[str]:
        """Extract GitHub repository references (owner/repo format)."""
        return re.findall(r"\\b[a-zA-Z0-9_.-]+/[a-zA-Z0-9_.-]+\\b", query)

    async def execute_server_specific_tool(
        self, session: ClientSession, tool_name: str, parameters: Any, **kwargs
    ) -> str:
        """Execute GitHub-specific MCP tools with proper parameter handling."""

        if tool_name == "listRepositories":
            return await self._execute_list_repositories(session, parameters)

        elif tool_name == "createIssue":
            return await self._execute_create_issue(session, parameters)

        elif tool_name == "listPullRequests":
            return await self._execute_list_pull_requests(session, parameters)

        elif tool_name == "getRepository":
            return await self._execute_get_repository(session, parameters)

        else:
            # Generic tool execution
            return await self._execute_generic_github_tool(
                session, tool_name, parameters
            )

    async def _execute_list_repositories(
        self, session: ClientSession, parameters: Any
    ) -> str:
        """List user's GitHub repositories."""
        args = {"type": "owner", "sort": "updated"}
        result = await session.call_tool("listRepositories", args)
        return self._extract_tool_result_content(result)

    async def _execute_create_issue(self, session: ClientSession, query: str) -> str:
        """Create new GitHub issue with parsed parameters."""
        args = await self._parse_github_create_issue_request(query)
        result = await session.call_tool("createIssue", args)
        return self._extract_tool_result_content(result)

    async def _execute_list_pull_requests(
        self, session: ClientSession, parameters: Any
    ) -> str:
        """List pull requests."""
        args = {"state": "open", "sort": "updated"}
        result = await session.call_tool("listPullRequests", args)
        return self._extract_tool_result_content(result)

    async def _execute_get_repository(
        self, session: ClientSession, repo_ref: str
    ) -> str:
        """Get specific repository details."""
        owner, repo = repo_ref.split("/") if "/" in repo_ref else ("", repo_ref)
        args = {"owner": owner, "repo": repo}
        result = await session.call_tool("getRepository", args)
        return self._extract_tool_result_content(result)

    async def _execute_generic_github_tool(
        self, session: ClientSession, tool_name: str, parameters: Any
    ) -> str:
        """Execute any other GitHub tool generically."""
        if isinstance(parameters, str):
            args = {"query": parameters}
        elif isinstance(parameters, dict):
            args = parameters
        else:
            args = {"input": str(parameters)}

        result = await session.call_tool(tool_name, args)
        return self._extract_tool_result_content(result)

    async def _parse_github_create_issue_request(self, query: str) -> Dict[str, Any]:
        """Parse create issue request for GitHub format."""

        # Extract issue details from query
        title_match = re.search(r'title[:\\s]+"([^"]+)"', query, re.IGNORECASE)
        title = title_match.group(1) if title_match else "New Issue"

        body_match = re.search(
            r'(?:body|description)[:\\s]+"([^"]+)"', query, re.IGNORECASE
        )
        body = body_match.group(1) if body_match else "No description provided"

        repo_match = re.search(r'repo[:\\s]+"([^"]+)"', query, re.IGNORECASE)
        if repo_match:
            repo_ref = repo_match.group(1)
            owner, repo = repo_ref.split("/") if "/" in repo_ref else ("", repo_ref)
        else:
            owner, repo = "user", "default-repo"  # Would need actual logic here

        return {"owner": owner, "repo": repo, "title": title, "body": body}

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
        """Format GitHub-specific capabilities."""
        base_summary = super().format_capabilities_summary()

        # Add GitHub-specific categorization
        if self.available_tools:
            repo_tools = [
                tool for tool in self.available_tools if "repo" in tool.name.lower()
            ]
            issue_tools = [
                tool for tool in self.available_tools if "issue" in tool.name.lower()
            ]
            pr_tools = [
                tool for tool in self.available_tools if "pull" in tool.name.lower()
            ]

            base_summary += "\\n**Tool Categories:**\\n"
            base_summary += f"- Repository Tools: {len(repo_tools)}\\n"
            base_summary += f"- Issue Tools: {len(issue_tools)}\\n"
            base_summary += f"- Pull Request Tools: {len(pr_tools)}\\n"
            base_summary += f"- Other Tools: {len(self.available_tools) - len(repo_tools) - len(issue_tools) - len(pr_tools)}\\n"

        return base_summary


def create_github_adapter(verbose: bool = True) -> GitHubMCPAdapter:
    """Create a GitHub MCP adapter instance."""
    return GitHubMCPAdapter(verbose=verbose)


# Example usage in an extended agent:
#
# from .github_adapter import create_github_adapter
#
# class ExtendedMultiMCPAgent(MultiMCPAgent):
#     def __init__(self, enable_github: bool = False, **kwargs):
#         super().__init__(**kwargs)
#
#         if enable_github:
#             github_adapter = create_github_adapter()
#             self.add_mcp_server_adapter(github_adapter)
