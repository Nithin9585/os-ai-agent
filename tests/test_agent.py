#!/usr/bin/env python3
"""
Unit tests for OpenSource AI Agent
"""

import json
import os
import sys
import unittest
from unittest.mock import patch, mock_open, MagicMock

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import agent


class TestAgentHelpers(unittest.TestCase):
    """Test helper functions"""
    
    def test_validate_environment_success(self):
        """Test environment validation with all vars set"""
        with patch.dict(os.environ, {
            'GITHUB_EVENT_PATH': '/tmp/event.json',
            'GITHUB_TOKEN': 'test_token',
            'AI_API_KEY': 'test_key',
            'X_BEARER_TOKEN': 'test_bearer'
        }):
            # Should not raise
            try:
                agent.validate_environment()
            except SystemExit:
                self.fail("validate_environment raised SystemExit unexpectedly")
    
    def test_validate_environment_missing_vars(self):
        """Test environment validation with missing vars"""
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaises(SystemExit):
                agent.validate_environment()
    
    def test_extract_event_data_pr(self):
        """Test extracting PR event data"""
        event = {
            "pull_request": {
                "html_url": "https://github.com/test/repo/pull/1",
                "title": "Test PR",
                "body": "Test description",
                "url": "https://api.github.com/repos/test/repo/pulls/1"
            },
            "repository": {
                "full_name": "test/repo"
            }
        }
        
        with patch('agent.fetch_pr_diff', return_value="diff content"):
            result = agent.extract_event_data(event)
            self.assertIsNotNone(result)
            event_type, repo, link, title, body, diff = result
            self.assertEqual(event_type, "PR")
            self.assertEqual(repo, "test/repo")
            self.assertEqual(title, "Test PR")
    
    def test_extract_event_data_issue(self):
        """Test extracting Issue event data"""
        event = {
            "issue": {
                "html_url": "https://github.com/test/repo/issues/1",
                "title": "Test Issue",
                "body": "Test description"
            },
            "repository": {
                "full_name": "test/repo"
            }
        }
        
        result = agent.extract_event_data(event)
        self.assertIsNotNone(result)
        event_type, repo, link, title, body, diff = result
        self.assertEqual(event_type, "Issue")
        self.assertEqual(diff, "")
    
    def test_extract_event_data_invalid(self):
        """Test extracting data from invalid event"""
        event = {
            "repository": {
                "full_name": "test/repo"
            }
        }
        
        result = agent.extract_event_data(event)
        self.assertIsNone(result)


class TestAIInteraction(unittest.TestCase):
    """Test AI API interaction"""
    
    @patch('agent.requests.post')
    def test_call_ai_success(self, mock_post):
        """Test successful AI API call"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [{
                "message": {
                    "content": "Test tweet content"
                }
            }]
        }
        mock_post.return_value = mock_response
        
        result = agent.call_ai("system prompt", "user prompt")
        self.assertEqual(result, "Test tweet content")
    
    @patch('agent.requests.post')
    def test_call_ai_skip(self, mock_post):
        """Test AI deciding to skip"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [{
                "message": {
                    "content": "SKIP"
                }
            }]
        }
        mock_post.return_value = mock_response
        
        result = agent.call_ai("system prompt", "user prompt")
        self.assertEqual(result, "SKIP")


class TestXPosting(unittest.TestCase):
    """Test X API posting"""
    
    @patch('agent.requests.post')
    def test_post_to_x_success(self, mock_post):
        """Test successful tweet posting"""
        mock_response = MagicMock()
        mock_response.status_code = 201
        mock_response.json.return_value = {
            "data": {
                "id": "1234567890"
            }
        }
        mock_post.return_value = mock_response
        
        result = agent.post_to_x("Test tweet")
        self.assertTrue(result)
    
    @patch('agent.requests.post')
    def test_post_to_x_failure(self, mock_post):
        """Test failed tweet posting"""
        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_response.text = "Error message"
        mock_post.return_value = mock_response
        
        result = agent.post_to_x("Test tweet")
        self.assertFalse(result)


if __name__ == '__main__':
    unittest.main()
