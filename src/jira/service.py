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
        
        # Process the raw Jira response into a simplified format
        raw_issue = response.json()
        return self._process_issue(raw_issue)

    def search_my_issues(self) -> list:
        """Search for issues assigned to the current user or reported by them."""
        # JQL query to find issues assigned to current user OR reported by current user
        jql = "(assignee = currentUser() OR reporter = currentUser()) ORDER BY updated DESC"
        url = f"{self.base_url}/search"
        params = {
            "jql": jql,
            "maxResults": 50,  # Increased to get more issues
            "fields": "summary,status,priority,updated,assignee,reporter,description,issuetype,created,labels,components",
        }
        response = requests.get(url, headers=self.headers, params=params)
        response.raise_for_status()
        
        # Process the search results
        raw_response = response.json()
        issues = raw_response.get('issues', [])
        
        # Convert each issue to our simplified format
        processed_issues = []
        for raw_issue in issues:
            processed_issue = self._process_issue(raw_issue)
            processed_issues.append(processed_issue)
        
        return processed_issues
    
    def _process_issue(self, raw_issue: dict) -> dict:
        """Convert a raw Jira issue to our simplified format."""
        fields = raw_issue.get('fields', {})
        
        # Safely extract status
        status = fields.get('status', {})
        status_name = status.get('name') if isinstance(status, dict) else str(status)
        
        # Safely extract priority
        priority = fields.get('priority', {})
        priority_name = priority.get('name') if isinstance(priority, dict) else str(priority)
        
        # Safely extract assignee
        assignee = fields.get('assignee', {})
        assignee_name = assignee.get('displayName') if isinstance(assignee, dict) else str(assignee) if assignee else 'Unassigned'
        
        # Safely extract reporter
        reporter = fields.get('reporter', {})
        reporter_name = reporter.get('displayName') if isinstance(reporter, dict) else str(reporter) if reporter else 'Unknown'
        
        # Safely extract issue type
        issue_type = fields.get('issuetype', {})
        issue_type_name = issue_type.get('name') if isinstance(issue_type, dict) else str(issue_type)
        
        # Extract labels and components
        labels = fields.get('labels', [])
        components = fields.get('components', [])
        component_names = [comp.get('name', str(comp)) if isinstance(comp, dict) else str(comp) for comp in components]
        
        # Process description (handle both string and Atlassian Document Format)
        description = fields.get('description', 'No description available')
        if isinstance(description, dict):
            # Atlassian Document Format - extract text content
            description_text = self._extract_text_from_adf(description)
        else:
            description_text = str(description) if description else 'No description available'
        
        return {
            'key': raw_issue.get('key', 'Unknown'),
            'summary': fields.get('summary', 'No summary'),
            'description': description_text,
            'status': status_name,
            'priority': priority_name,
            'assignee': assignee_name,
            'reporter': reporter_name,
            'issue_type': issue_type_name,
            'created': fields.get('created'),
            'updated': fields.get('updated'),
            'labels': labels,
            'components': component_names
        }
    
    def _extract_text_from_adf(self, adf_content: dict) -> str:
        """Extract plain text from Atlassian Document Format."""
        if not isinstance(adf_content, dict):
            return str(adf_content)
        
        def extract_text_recursive(node):
            """Recursively extract text from ADF nodes."""
            text_parts = []
            
            if isinstance(node, dict):
                # If this node has text, add it
                if node.get('type') == 'text':
                    text_parts.append(node.get('text', ''))
                
                # Process content array
                content = node.get('content', [])
                if isinstance(content, list):
                    for child in content:
                        text_parts.append(extract_text_recursive(child))
            
            return ' '.join(filter(None, text_parts))
        
        extracted_text = extract_text_recursive(adf_content).strip()
        return extracted_text if extracted_text else 'No description available'


# Convenience function for backward compatibility
def get_jira_issue(issue_id: str) -> Dict:
    """Get a Jira issue by its ID."""
    service = JiraService()
    return service.get_issue(issue_id)
