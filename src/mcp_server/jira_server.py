"""Custom Jira MCP Server

This server provides Jira functionality through the Model Context Protocol.
It reuses the existing Jira service logic but exposes it as MCP tools and resources.
"""

import os
import sys
from pathlib import Path

def setup_imports():
    """Set up imports and return the necessary modules."""
    # Add the project root to Python path
    project_root = Path(__file__).parent.parent.parent
    sys.path.insert(0, str(project_root))
    
    # Load environment variables
    from dotenv import load_dotenv
    env_path = project_root / ".env"
    load_dotenv(dotenv_path=env_path)
    
    # Import required modules
    from mcp.server.fastmcp import FastMCP
    from src.jira.service import JiraService
    
    return FastMCP, JiraService

# Set up imports
FastMCP, JiraService = setup_imports()

# Create the MCP server
mcp = FastMCP("Jira MCP Server")

# Initialize Jira service
jira_service = JiraService()


@mcp.tool()
def get_my_jira_issues() -> str:
    """Get all Jira issues assigned to the current user."""
    try:
        issues = jira_service.search_my_issues()
        if not issues:
            return "No issues found assigned to you."
        
        result = f"Found {len(issues)} issues assigned to you:\n\n"
        for issue in issues:
            status = issue.get("status", "Unknown")
            priority = issue.get("priority", "Unknown")
            result += f"• {issue['key']}: {issue['summary']}\n"
            result += f"  Status: {status} | Priority: {priority}\n\n"
        
        return result
    except Exception as e:
        return f"Error retrieving issues: {str(e)}"


@mcp.tool()
def get_jira_issue_summary(issue_key: str) -> str:
    """Get a summary of a specific Jira issue.
    
    Args:
        issue_key: The Jira issue key (e.g., 'KAN-1')
    """
    try:
        issue = jira_service.get_issue(issue_key)
        if not issue:
            return f"Issue {issue_key} not found."
        
        summary = issue.get("summary", "No summary")
        status = issue.get("status", "Unknown")
        priority = issue.get("priority", "Unknown")
        assignee = issue.get("assignee", "Unassigned")
        
        result = f"Issue: {issue_key}\n"
        result += f"Summary: {summary}\n"
        result += f"Status: {status}\n"
        result += f"Priority: {priority}\n"
        result += f"Assignee: {assignee}\n"
        
        return result
    except Exception as e:
        return f"Error retrieving issue {issue_key}: {str(e)}"


@mcp.tool()
def get_jira_issue_description(issue_key: str) -> str:
    """Get the detailed description of a specific Jira issue.
    
    Args:
        issue_key: The Jira issue key (e.g., 'KAN-1')
    """
    try:
        issue = jira_service.get_issue(issue_key)
        if not issue:
            return f"Issue {issue_key} not found."
        
        description = issue.get("description", "No description available")
        summary = issue.get("summary", "No summary")
        
        result = f"Issue: {issue_key}\n"
        result += f"Summary: {summary}\n\n"
        result += f"Description:\n{description}\n"
        
        return result
    except Exception as e:
        return f"Error retrieving description for issue {issue_key}: {str(e)}"


@mcp.tool()
def get_jira_issue_full_details(issue_key: str) -> str:
    """Get complete details of a specific Jira issue including all fields.
    
    Args:
        issue_key: The Jira issue key (e.g., 'KAN-1')
    """
    try:
        issue = jira_service.get_issue(issue_key)
        if not issue:
            return f"Issue {issue_key} not found."
        
        # Build comprehensive issue details
        result = f"=== COMPLETE DETAILS FOR {issue_key} ===\n\n"
        
        # Basic info
        result += f"Summary: {issue.get('summary', 'No summary')}\n"
        result += f"Status: {issue.get('status', 'Unknown')}\n"
        result += f"Priority: {issue.get('priority', 'Unknown')}\n"
        result += f"Assignee: {issue.get('assignee', 'Unassigned')}\n"
        result += f"Reporter: {issue.get('reporter', 'Unknown')}\n"
        result += f"Issue Type: {issue.get('issue_type', 'Unknown')}\n"
        
        # Dates
        created = issue.get('created')
        updated = issue.get('updated')
        if created:
            result += f"Created: {created}\n"
        if updated:
            result += f"Updated: {updated}\n"
        
        # Description
        description = issue.get('description', 'No description available')
        result += f"\nDescription:\n{description}\n"
        
        # Additional fields if present
        labels = issue.get('labels', [])
        if labels:
            result += f"\nLabels: {', '.join(labels)}\n"
        
        components = issue.get('components', [])
        if components:
            result += f"Components: {', '.join(components)}\n"
        
        return result
        
    except Exception as e:
        return f"Error retrieving full details for issue {issue_key}: {str(e)}"


@mcp.resource("jira://issues/my")
def get_my_issues_resource() -> str:
    """Resource containing all issues assigned to the current user."""
    return get_my_jira_issues()


@mcp.resource("jira://issue/{issue_key}")
def get_issue_resource(issue_key: str) -> str:
    """Resource containing details for a specific Jira issue."""
    return get_jira_issue_full_details(issue_key)


@mcp.prompt()
def analyze_jira_issue(issue_key: str, analysis_type: str = "summary") -> str:
    """Generate a prompt for analyzing a Jira issue.
    
    Args:
        issue_key: The Jira issue key to analyze
        analysis_type: Type of analysis (summary, detailed, actionable)
    """
    analysis_types = {
        "summary": "Please provide a brief summary and status update for this issue",
        "detailed": "Please provide a detailed analysis including potential solutions and next steps", 
        "actionable": "Please identify specific actionable items and recommendations for this issue"
    }
    
    prompt_text = analysis_types.get(analysis_type, analysis_types["summary"])
    
    return f"""Analyze the following Jira issue:

Issue Key: {issue_key}

{prompt_text}.

Focus on:
- Current status and priority
- Key requirements or problems
- Potential blockers or dependencies
- Recommended next actions
"""


def main():
    """Main entry point for the server."""
    try:
        print("🚀 Starting Jira MCP Server...")
        print(f"📍 Jira instance: {os.getenv('JIRA_API_BASE', 'Not configured')}")
        print("🔧 Available tools:")
        print("   - get_my_jira_issues: Get your assigned issues")
        print("   - get_jira_issue_summary: Get issue summary")
        print("   - get_jira_issue_description: Get issue description")
        print("   - get_jira_issue_full_details: Get complete issue details")
        print("\n✅ Server ready for MCP connections")
        
        # Run the server
        mcp.run()
        
    except Exception as e:
        print(f"❌ Error starting server: {str(e)}")
        return 1


if __name__ == "__main__":
    # Run the server
    exit_code = main()
    sys.exit(exit_code or 0)
