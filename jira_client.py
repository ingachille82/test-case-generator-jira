"""
Jira API client for fetching user story details.
"""
import os
import re
import logging
from atlassian import Jira

# Configure logging
logger = logging.getLogger(__name__)


class JiraClient:
    """Client for interacting with Jira API v2."""

    def __init__(self):
        """Initialize Jira client with credentials from environment."""
        self.jira_url = os.environ.get('JIRA_URL')
        self.jira_api_token = os.environ.get('JIRA_API_TOKEN')

        # Load Jira field configurations
        self.project_key = os.environ.get('JIRA_PROJECT_KEY', 'TEST')
        self.component_id = os.environ.get('JIRA_COMPONENT_ID', '10201')
        self.component_name = os.environ.get('JIRA_COMPONENT_NAME', 'IAA')
        self.customfield_10107 = os.environ.get('JIRA_CUSTOMFIELD_10107', '10')
        self.customfield_10223 = os.environ.get('JIRA_CUSTOMFIELD_10223', '/Onboarding and Authentication')
        self.customfield_10247_id = os.environ.get('JIRA_CUSTOMFIELD_10247_ID', '10122')
        self.customfield_10247_value = os.environ.get('JIRA_CUSTOMFIELD_10247_VALUE', 'Comp.int Test')
        self.customfield_10214_id = os.environ.get('JIRA_CUSTOMFIELD_10214_ID', '10116')
        self.customfield_10214_value = os.environ.get('JIRA_CUSTOMFIELD_10214_VALUE', 'Cucumber')
        self.gherkin_field = os.environ.get('JIRA_GHERKIN_FIELD', 'customfield_10215')
        self.test_plan_field = os.environ.get('JIRA_TEST_PLAN_FIELD', 'customfield_10221')
        self.test_plan_jql = os.environ.get('JIRA_TEST_PLAN_JQL', 'type = "Test Plan" AND summary ~ "IAA test plan" and labels in ("Onboarding+Authentication") order by created desc')

        # Only initialize if credentials are provided
        if self.jira_url and self.jira_api_token:
            self.client = Jira(
                url=self.jira_url,
                token=self.jira_api_token
            )
            self.enabled = True
        else:
            self.client = None
            self.enabled = False

    def is_enabled(self):
        """Check if Jira integration is enabled."""
        return self.enabled

    def fetch_issue(self, issue_key):
        """
        Fetch a Jira issue by key.

        Args:
            issue_key (str): Jira issue key (e.g., 'PROJ-123')

        Returns:
            dict: Issue data with fields

        Raises:
            Exception: If issue cannot be fetched
        """
        if not self.enabled:
            raise Exception("Jira integration is not configured. Please set JIRA_URL and JIRA_API_TOKEN in .env")

        try:
            # Fetch issue with all fields
            issue = self.client.issue(issue_key)
            return issue
        except Exception as e:
            raise Exception(f"Failed to fetch Jira issue {issue_key}: {str(e)}")

    def extract_user_story(self, issue_key):
        """
        Extract user story text from a Jira issue.

        Args:
            issue_key (str): Jira issue key (e.g., 'PROJ-123')

        Returns:
            str: Formatted user story with acceptance criteria

        Raises:
            Exception: If issue cannot be fetched or parsed
        """
        issue = self.fetch_issue(issue_key)
        fields = issue.get('fields', {})

        # Extract basic information
        summary = fields.get('summary', 'No summary')
        description = fields.get('description', '')
        issue_type = fields.get('issuetype', {}).get('name', 'Unknown')

        # Build user story text
        user_story = f"**Issue:** {issue_key}\n"
        user_story += f"**Type:** {issue_type}\n"
        user_story += f"**Summary:** {summary}\n\n"

        # Add description (which should contain the user story format)
        if description:
            user_story += description
        else:
            user_story += "**Description:** No description provided\n"

        return user_story

    def parse_acceptance_criteria(self, description):
        """
        Parse acceptance criteria from Jira description text.

        This is a helper method to extract acceptance criteria if they're
        formatted in a specific way in the Jira description.

        Args:
            description (str): Jira issue description

        Returns:
            list: List of acceptance criteria strings
        """
        # This is a basic implementation - you may need to customize
        # based on your Jira formatting conventions
        criteria = []
        lines = description.split('\n')
        in_ac_section = False

        for line in lines:
            line_lower = line.lower().strip()

            # Detect start of acceptance criteria section
            if 'acceptance criteria' in line_lower or 'acceptance criterion' in line_lower:
                in_ac_section = True
                continue

            # Stop if we hit another section
            if in_ac_section and line.startswith('**') and line.endswith('**'):
                break

            # Collect criteria lines
            if in_ac_section and line.strip():
                criteria.append(line.strip())

        return criteria

    def get_issue_metadata(self, issue_key):
        """
        Get metadata about a Jira issue.

        Args:
            issue_key (str): Jira issue key

        Returns:
            dict: Metadata including assignee, reporter, status, etc.
        """
        issue = self.fetch_issue(issue_key)
        fields = issue.get('fields', {})

        metadata = {
            'key': issue.get('key'),
            'summary': fields.get('summary'),
            'status': fields.get('status', {}).get('name'),
            'issue_type': fields.get('issuetype', {}).get('name'),
            'assignee': fields.get('assignee', {}).get('displayName') if fields.get('assignee') else 'Unassigned',
            'reporter': fields.get('reporter', {}).get('displayName') if fields.get('reporter') else 'Unknown',
            'created': fields.get('created'),
            'updated': fields.get('updated'),
        }

        return metadata

    def get_tested_by_issues(self, issue_key):
        """
        Get all test case issues that are linked with 'tested by' relationship.

        Args:
            issue_key (str): Jira issue key

        Returns:
            list: List of test case dictionaries with key, summary, description, and AC number
        """
        logger.info(f"Fetching 'tested by' issues for {issue_key}")

        issue = self.fetch_issue(issue_key)
        fields = issue.get('fields', {})
        issue_links = fields.get('issuelinks', [])

        logger.info(f"Found {len(issue_links)} total issue links for {issue_key}")

        test_cases = []

        for link in issue_links:
            # Check if this is an inward 'tested by' link
            link_type = link.get('type', {})
            inward_desc = link_type.get('inward', '').lower()

            logger.debug(f"Processing link with type: {inward_desc}")

            if 'tested by' in inward_desc or 'tests' in inward_desc:
                # Get the linked issue (inward issue)
                linked_issue = link.get('inwardIssue')

                if linked_issue:
                    linked_key = linked_issue.get('key')

                    # Fetch the complete issue to get the description
                    try:
                        complete_issue = self.fetch_issue(linked_key)
                        linked_fields = complete_issue.get('fields', {})
                        linked_summary = linked_fields.get('summary', '')
                        if "PSO" in linked_summary:
                            continue
                        linked_description = linked_fields.get('description', '')
                        linked_status = linked_fields.get('status', {}).get('name', 'Unknown')
                        linked_gherkin = linked_fields.get('customfield_10215', '')

                        logger.info(f"parsing issue {linked_key}: {linked_summary}")
                        logger.debug(f"parsing issue {linked_key}: {linked_description}")
                        # Extract AC number from description (format: AC1, AC2, etc.)
                        ac_number = self._extract_ac_number(linked_description)

                        logger.info(f"Found test case: {linked_key} (Status: {linked_status}, AC: {ac_number if ac_number else 'N/A'})")

                        test_case = {
                            'key': linked_key,
                            'summary': linked_summary,
                            'description': linked_description,
                            'gherkin': linked_gherkin,
                            'status': linked_status,
                            'ac_number': ac_number,
                            'url': f"{self.jira_url}/browse/{linked_key}"
                        }

                        test_cases.append(test_case)
                    except Exception as e:
                        logger.error(f"Failed to fetch complete issue {linked_key}: {str(e)}")
                        continue
                else:
                    logger.warning(f"Link type '{inward_desc}' matched but no inwardIssue found")

        logger.info(f"Total 'tested by' test cases found for {issue_key}: {len(test_cases)}")
        return test_cases

    def _extract_ac_number(self, description):
        """
        Extract AC number from test case description.

        Args:
            description (str): Test case description

        Returns:
            int or None: AC number if found, None otherwise
        """
        if not description:
            logger.debug("No description provided for AC extraction")
            return None

        logger.info(f"searching ac number in: {description}")
        # Look for patterns like "AC1", "AC2", "AC 1", "AC-1", etc.
        match = re.search(r'\bAC[\s-]?(\d+)\b', description, re.IGNORECASE)

        if match:
            ac_num = int(match.group(1))
            logger.info(f"Extracted AC number: {ac_num} from pattern: {match.group(0)}")
            return ac_num
        else:
            logger.info(f"No AC number pattern found in description (searched first 100 chars): {description[:100]}...")

        return None

    def search_test_plans(self):
        """
        Search for test plan issues using the configured JQL query.

        Returns:
            list: List of test plan dictionaries with key and summary

        Raises:
            Exception: If search fails
        """
        if not self.enabled:
            raise Exception("Jira integration is not configured")

        try:
            logger.info(f"Searching for test plans with JQL: {self.test_plan_jql}")

            # Use JQL to search for test plans
            issues = self.client.jql(self.test_plan_jql, fields='key,summary')

            test_plans = []
            for issue in issues.get('issues', []):
                key = issue.get('key')
                summary = issue.get('fields', {}).get('summary', '')
                test_plans.append({
                    'key': key,
                    'summary': summary,
                    'display': f"{key} - {summary}"
                })

            logger.info(f"Found {len(test_plans)} test plans")
            return test_plans

        except Exception as e:
            logger.error(f"Failed to search test plans: {str(e)}", exc_info=True)
            raise Exception(f"Failed to search test plans: {str(e)}")

    def create_test_case(self, parent_issue_key, title, description, gherkin, ac_number=None, labels=None, test_plan_keys=None):
        """
        Create a new test case in Jira.

        Args:
            parent_issue_key (str): The parent user story issue key
            title (str): Test case title
            description (str): Test case description in format "AC X\n{description}"
            gherkin (str): Gherkin scenario
            ac_number (int, optional): Acceptance criterion number (kept for backwards compatibility)
            labels (list, optional): List of labels to apply to the test case
            test_plan_keys (list, optional): List of test plan issue keys

        Returns:
            dict: Created issue data with key

        Raises:
            Exception: If test case creation fails
        """
        if not self.enabled:
            raise Exception("Jira integration is not configured")

        try:
            # Build the issue data with the configured structure
            issue_data = {
                "fields": {
                    "project": {"key": self.project_key},
                    "summary": title,
                    "description": description,
                    "issuetype": {"name": "Test"},
                    "components": [
                        {
                            "self": f"{self.jira_url}/rest/api/2/component/{self.component_id}",
                            "id": self.component_id,
                            "name": self.component_name
                        }
                    ],
                    "customfield_10107": self.customfield_10107,
                    "customfield_10223": self.customfield_10223,
                    "customfield_10247": {
                        "self": f"{self.jira_url}/rest/api/2/customFieldOption/{self.customfield_10247_id}",
                        "value": self.customfield_10247_value,
                        "id": self.customfield_10247_id,
                        "disabled": False
                    },
                    "customfield_10214": {
                        "self": f"{self.jira_url}/rest/api/2/customFieldOption/{self.customfield_10214_id}",
                        "value": self.customfield_10214_value,
                        "id": self.customfield_10214_id,
                        "disabled": False
                    },
                    self.gherkin_field: gherkin
                }
            }

            # Add labels if provided
            if labels:
                issue_data["fields"]["labels"] = labels

            # Add test plan if provided
            if test_plan_keys:
                issue_data["fields"][self.test_plan_field] = test_plan_keys

            # Create the issue
            logger.info(f"Creating test case with data: {issue_data}")
            created_issue = self.client.issue_create(fields=issue_data['fields'])

            issue_key = created_issue.get('key')
            logger.info(f"Created test case: {issue_key}")

            # Link the test case to the parent issue with "tests" relationship
            try:
                link_data = {
                    "inwardIssue": {
                        "key": issue_key
                    },
                    "outwardIssue": {
                        "key": parent_issue_key
                    },
                    "type": {
                        "name": "Tests"
                    }
                }
                logger.info(f"Creating link from {issue_key} to {parent_issue_key} with data: {link_data}")
                self.client.post('rest/api/2/issueLink', data=link_data)
                logger.info(f"Successfully linked {issue_key} to {parent_issue_key} with 'Tests' relationship")
            except Exception as link_error:
                logger.error(f"Failed to create link: {str(link_error)}", exc_info=True)
                # Don't fail the entire operation if linking fails
                logger.warning(f"Test case {issue_key} was created but could not be linked to {parent_issue_key}")

            return {
                "key": issue_key,
                "url": f"{self.jira_url}/browse/{issue_key}",
                "success": True
            }

        except Exception as e:
            logger.error(f"Failed to create test case: {str(e)}", exc_info=True)
            raise Exception(f"Failed to create test case in Jira: {str(e)}")

