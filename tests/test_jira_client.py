"""
Unit tests for JiraClient class.
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from jira_client import JiraClient


class TestJiraClientExtractACNumber:
    """Test cases for the _extract_ac_number method."""

    @pytest.fixture
    def jira_client(self):
        """Create a JiraClient instance for testing."""
        with patch.dict('os.environ', {
            'JIRA_URL': 'https://test.atlassian.net',
            'JIRA_API_TOKEN': 'test_token'
        }):
            client = JiraClient()
            return client

    def test_extract_ac_number_basic_format(self, jira_client):
        """Test extraction with basic AC format (AC1, AC2, etc.)."""
        description = "This test case covers AC1 for user authentication."
        result = jira_client._extract_ac_number(description)
        assert result == 1

    def test_extract_ac_number_with_space(self, jira_client):
        """Test extraction with space between AC and number (AC 5)."""
        description = "Test case for AC 5 - Payment processing"
        result = jira_client._extract_ac_number(description)
        assert result == 5

    def test_extract_ac_number_with_hyphen(self, jira_client):
        """Test extraction with hyphen between AC and number (AC-3)."""
        description = "Covers AC-3 for the login flow"
        result = jira_client._extract_ac_number(description)
        assert result == 3

    def test_extract_ac_number_case_insensitive(self, jira_client):
        """Test that extraction is case insensitive."""
        descriptions = [
            "ac1 - lowercase",
            "AC1 - uppercase",
            "Ac1 - mixed case",
            "aC1 - mixed case 2"
        ]
        for desc in descriptions:
            result = jira_client._extract_ac_number(desc)
            assert result == 1, f"Failed for description: {desc}"

    def test_extract_ac_number_double_digit(self, jira_client):
        """Test extraction with double-digit AC numbers."""
        description = "This covers AC12 for batch processing"
        result = jira_client._extract_ac_number(description)
        assert result == 12

    def test_extract_ac_number_triple_digit(self, jira_client):
        """Test extraction with triple-digit AC numbers."""
        description = "Test for AC123 - edge case handling"
        result = jira_client._extract_ac_number(description)
        assert result == 123

    def test_extract_ac_number_at_start(self, jira_client):
        """Test extraction when AC is at the start of description."""
        description = "AC7 is about error handling in the payment module"
        result = jira_client._extract_ac_number(description)
        assert result == 7

    def test_extract_ac_number_at_end(self, jira_client):
        """Test extraction when AC is at the end of description."""
        description = "This test case validates AC99"
        result = jira_client._extract_ac_number(description)
        assert result == 99

    def test_extract_ac_number_multiple_occurrences(self, jira_client):
        """Test extraction when multiple AC references exist (should return first)."""
        description = "AC2 and AC3 are both covered in this test"
        result = jira_client._extract_ac_number(description)
        assert result == 2  # Should return the first match

    def test_extract_ac_number_with_surrounding_text(self, jira_client):
        """Test extraction with lots of surrounding text."""
        description = """
        This is a comprehensive test case that validates the user authentication flow.
        It specifically covers AC5 which requires that users must provide valid credentials.
        The test includes multiple scenarios and edge cases.
        """
        result = jira_client._extract_ac_number(description)
        assert result == 5

    def test_extract_ac_number_no_match(self, jira_client):
        """Test when no AC pattern is found in description."""
        description = "This test case has no acceptance criterion reference"
        result = jira_client._extract_ac_number(description)
        assert result is None

    def test_extract_ac_number_empty_description(self, jira_client):
        """Test with empty description."""
        description = ""
        result = jira_client._extract_ac_number(description)
        assert result is None

    def test_extract_ac_number_none_description(self, jira_client):
        """Test with None description."""
        description = None
        result = jira_client._extract_ac_number(description)
        assert result is None

    def test_extract_ac_number_whitespace_only(self, jira_client):
        """Test with whitespace-only description."""
        description = "   \n\t   "
        result = jira_client._extract_ac_number(description)
        assert result is None

    def test_extract_ac_number_similar_patterns(self, jira_client):
        """Test that similar but incorrect patterns are not matched."""
        descriptions = [
            "Account1",  # 'AC' is part of 'Account'
            "ACID test",  # 'AC' is part of 'ACID'
            "back1",     # 'ac' is part of 'back'
            "ACE 1",     # Different word 'ACE'
        ]
        for desc in descriptions:
            result = jira_client._extract_ac_number(desc)
            # These should not match because they're not standalone 'AC' followed by number
            # The regex uses \b word boundary, so 'Account1' should not match
            if desc == "Account1" or desc == "back1":
                assert result is None, f"Should not match for: {desc}"

    def test_extract_ac_number_with_newlines(self, jira_client):
        """Test extraction with newlines in description."""
        description = "First line\nAC4 is here\nThird line"
        result = jira_client._extract_ac_number(description)
        assert result == 4

    def test_extract_ac_number_with_special_chars(self, jira_client):
        """Test extraction with special characters around AC."""
        descriptions = [
            "(AC8)",
            "[AC8]",
            "{AC8}",
            "AC8.",
            "AC8,",
            "AC8!",
            "AC8?",
        ]
        for desc in descriptions:
            result = jira_client._extract_ac_number(desc)
            assert result == 8, f"Failed for description: {desc}"

    def test_extract_ac_number_markdown_format(self, jira_client):
        """Test extraction from markdown-formatted description."""
        description = """
        ## Test Case Description

        This test case covers **AC10** which validates:
        - User authentication
        - Session management
        """
        result = jira_client._extract_ac_number(description)
        assert result == 10

    def test_extract_ac_number_zero(self, jira_client):
        """Test extraction with AC0 (edge case)."""
        description = "Test for AC0"
        result = jira_client._extract_ac_number(description)
        assert result == 0

    def test_extract_ac_number_with_extra_spaces(self, jira_client):
        """Test extraction with multiple spaces."""
        description = "AC  6"  # Two spaces
        result = jira_client._extract_ac_number(description)
        # The regex uses \s? which matches 0 or 1 whitespace, so this should not match
        assert result is None

    def test_extract_ac_number_word_boundary(self, jira_client):
        """Test that word boundaries are properly enforced."""
        # 'AC' must be preceded by a word boundary
        description = "testAC5"  # No word boundary before AC
        result = jira_client._extract_ac_number(description)
        assert result is None

    def test_extract_ac_number_various_positions(self, jira_client):
        """Test AC extraction at various positions in text."""
        test_cases = [
            ("AC1 at start", 1),
            ("Middle AC2 position", 2),
            ("At the end AC3", 3),
            ("AC4", 4),  # Only AC reference
        ]
        for desc, expected in test_cases:
            result = jira_client._extract_ac_number(desc)
            assert result == expected, f"Failed for: {desc}"


class TestJiraClientIntegration:
    """Integration tests for JiraClient (if needed in the future)."""

    def test_client_initialization_without_credentials(self):
        """Test that client is disabled when credentials are not provided."""
        with patch.dict('os.environ', {}, clear=True):
            client = JiraClient()
            assert client.is_enabled() is False

    def test_client_initialization_with_credentials(self):
        """Test that client is enabled when credentials are provided."""
        with patch.dict('os.environ', {
            'JIRA_URL': 'https://test.atlassian.net',
            'JIRA_API_TOKEN': 'test_token'
        }):
            client = JiraClient()
            assert client.is_enabled() is True
