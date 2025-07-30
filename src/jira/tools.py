from langchain.agents import Tool
from .service import get_jira_issue, JiraService, JIRA_EMAIL


def get_my_jira_issues() -> str:
    """Get Jira issues assigned to the current user."""
    try:
        service = JiraService()
        search_result = service.search_my_issues()

        if not search_result.get("issues"):
            return "No issues found assigned to you."

        issues_list = []
        for issue in search_result["issues"]:
            key = issue["key"]
            summary = issue["fields"]["summary"]
            status = issue["fields"]["status"]["name"]
            priority = issue["fields"].get("priority")
            priority_name = priority.get("name") if priority else "None"

            # Check if assigned to you or reported by you
            assignee = issue["fields"].get("assignee")
            reporter = issue["fields"].get("reporter")

            role = ""
            if assignee and assignee.get("emailAddress") == JIRA_EMAIL:
                role = " [Assigned to you]"
            elif reporter and reporter.get("emailAddress") == JIRA_EMAIL:
                role = " [Reported by you]"

            issues_list.append(
                f"• {key}: {summary} (Status: {status}, Priority: {priority_name}){role}"
            )

        return "Your Jira issues:\n" + "\n".join(issues_list)
    except Exception as e:
        return f"Error fetching your issues: {str(e)}"


def get_jira_issue_summary(issue_id: str) -> str:
    """Get the summary of a Jira issue."""
    try:
        issue_data = get_jira_issue(issue_id)
        return issue_data["fields"]["summary"]
    except Exception as e:
        return f"Error fetching issue {issue_id}: {str(e)}"


def get_jira_issue_description(issue_id: str) -> str:
    """Get the description of a Jira issue."""
    try:
        issue_data = get_jira_issue(issue_id)
        description = issue_data["fields"].get("description")
        if description:
            # Handle different description formats (ADF, plain text, etc.)
            if isinstance(description, dict) and "content" in description:
                # Atlassian Document Format
                return str(description["content"])
            elif isinstance(description, str):
                return description
            else:
                return str(description)
        return "No description available"
    except Exception as e:
        return f"Error fetching description for issue {issue_id}: {str(e)}"


def get_jira_issue_full_details(issue_id: str) -> str:
    """Get full details of a Jira issue."""
    try:
        issue_data = get_jira_issue(issue_id)
        fields = issue_data["fields"]

        details = {
            "key": issue_data["key"],
            "summary": fields["summary"],
            "status": fields["status"]["name"],
            "assignee": fields.get("assignee", {}).get("displayName", "Unassigned")
            if fields.get("assignee")
            else "Unassigned",
            "reporter": fields.get("reporter", {}).get("displayName", "Unknown")
            if fields.get("reporter")
            else "Unknown",
            "priority": fields.get("priority", {}).get("name", "Unknown")
            if fields.get("priority")
            else "Unknown",
            "project": fields["project"]["name"],
        }

        return f"""Issue Details:
                    Key: {details["key"]}
                    Summary: {details["summary"]}
                    Status: {details["status"]}
                    Assignee: {details["assignee"]}
                    Reporter: {details["reporter"]}
                    Priority: {details["priority"]}
                    Project: {details["project"]}"""
    except Exception as e:
        return f"Error fetching details for issue {issue_id}: {str(e)}"


jira_tools = [
    Tool(
        name="get_my_jira_issues",
        func=get_my_jira_issues,
        description="Get all Jira issues assigned to me/current user. Use this when user asks about 'my issues', 'my tickets', or 'issues assigned to me'.",
    ),
    Tool(
        name="get_jira_issue_summary",
        func=get_jira_issue_summary,
        description="Get the summary of a Jira issue using its ID like PROJ-123.",
    ),
    Tool(
        name="get_jira_issue_description",
        func=get_jira_issue_description,
        description="Get the description of a Jira issue using its ID like PROJ-123.",
    ),
    Tool(
        name="get_jira_issue_details",
        func=get_jira_issue_full_details,
        description="Get comprehensive details of a Jira issue including summary, status, assignee, etc. Use issue ID like PROJ-123.",
    ),
]
