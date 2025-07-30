"""Tests for Jira service layer."""

import unittest
from unittest.mock import patch, MagicMock
import sys
import os

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../src"))

from jira.service import JiraService, get_jira_issue


class TestJiraService(unittest.TestCase):
    """Test cases for JiraService."""

    def setUp(self):
        """Set up test fixtures."""
        self.service = JiraService()

    @patch("jira.service.requests.get")
    def test_get_issue_success(self, mock_get):
        """Test successful issue retrieval."""
        # Mock response
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "key": "PROJ-123",
            "fields": {"summary": "Test issue"},
        }
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        # Test
        result = self.service.get_issue("PROJ-123")

        # Assertions
        self.assertEqual(result["key"], "PROJ-123")
        self.assertEqual(result["fields"]["summary"], "Test issue")
        mock_get.assert_called_once()

    @patch("jira.service.requests.get")
    def test_get_jira_issue_function(self, mock_get):
        """Test the convenience function."""
        # Mock response
        mock_response = MagicMock()
        mock_response.json.return_value = {"key": "PROJ-123"}
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        # Test
        result = get_jira_issue("PROJ-123")

        # Assertions
        self.assertEqual(result["key"], "PROJ-123")


if __name__ == "__main__":
    unittest.main()
