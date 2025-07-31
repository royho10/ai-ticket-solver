"""Tests for Jira tools."""

import unittest
from unittest.mock import patch
import sys
import os

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../src"))

from jira.tools import get_jira_issue_summary, get_jira_issue_description, jira_tools


class TestJiraTools(unittest.TestCase):
    """Test cases for Jira tools."""

    @patch("jira.tools.get_jira_issue")
    def test_get_jira_issue_summary_success(self, mock_get_issue):
        """Test successful summary retrieval."""
        # Mock
        mock_get_issue.return_value = {"fields": {"summary": "Test issue summary"}}

        # Test
        result = get_jira_issue_summary("PROJ-123")

        # Assertions
        self.assertEqual(result, "Test issue summary")
        mock_get_issue.assert_called_once_with("PROJ-123")

    @patch("jira.tools.get_jira_issue")
    def test_get_jira_issue_summary_error(self, mock_get_issue):
        """Test error handling in summary retrieval."""
        # Mock error
        mock_get_issue.side_effect = Exception("API Error")

        # Test
        result = get_jira_issue_summary("PROJ-123")

        # Assertions
        self.assertIn("Error fetching issue PROJ-123", result)

    @patch("jira.tools.get_jira_issue")
    def test_get_jira_issue_description_success(self, mock_get_issue):
        """Test successful description retrieval."""
        # Mock
        mock_get_issue.return_value = {"fields": {"description": "Test description"}}

        # Test
        result = get_jira_issue_description("PROJ-123")

        # Assertions
        self.assertEqual(result, "Test description")


if __name__ == "__main__":
    unittest.main()
