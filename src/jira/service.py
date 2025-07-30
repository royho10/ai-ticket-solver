import requests
import os
import base64
from typing import Dict
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables from .env file (look for it in project root)
env_path = Path.cwd() / ".env"
load_dotenv(dotenv_path=env_path)

# Get environment variables first, then fall back to config file
JIRA_API_BASE = os.getenv("JIRA_API_BASE", "").strip("\"'")
JIRA_API_TOKEN = os.getenv("JIRA_API_TOKEN", "").strip("\"'")
JIRA_EMAIL = os.getenv("JIRA_EMAIL", "").strip("\"'")


class JiraService:
    """Service layer for Jira API interactions."""

    def __init__(self):
        self.base_url = JIRA_API_BASE
        # Proper Basic Auth for Jira API token
        auth_string = f"{JIRA_EMAIL}:{JIRA_API_TOKEN}"
        auth_bytes = auth_string.encode("ascii")
        auth_base64 = base64.b64encode(auth_bytes).decode("ascii")

        self.headers = {
            "Authorization": f"Basic {auth_base64}",
            "Accept": "application/json",
        }

    def get_issue(self, issue_id: str) -> Dict:
        """Get a Jira issue by its ID."""
        url = f"{self.base_url}/issue/{issue_id}"
        response = requests.get(url, headers=self.headers)
        response.raise_for_status()
        return response.json()

    def search_my_issues(self) -> Dict:
        """Search for issues assigned to the current user or reported by them."""
        # JQL query to find issues assigned to current user OR reported by current user
        jql = "(assignee = currentUser() OR reporter = currentUser()) ORDER BY updated DESC"
        url = f"{self.base_url}/search"
        params = {
            "jql": jql,
            "maxResults": 10,
            "fields": "summary,status,priority,updated,assignee,reporter",
        }
        response = requests.get(url, headers=self.headers, params=params)
        response.raise_for_status()
        return response.json()


# Convenience function for backward compatibility
def get_jira_issue(issue_id: str) -> Dict:
    """Get a Jira issue by its ID."""
    service = JiraService()
    return service.get_issue(issue_id)
