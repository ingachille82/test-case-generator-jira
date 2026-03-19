import os
import json
import re
import logging
from flask import Flask, render_template, request, jsonify, session, make_response
from anthropic import Anthropic
from dotenv import load_dotenv

# Load environment variables first (needed for log level)
load_dotenv()

# Configure logging BEFORE any imports that use logging
LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO').upper()
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL, logging.INFO),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    force=True  # Force reconfiguration if already configured
)

from jira_client import JiraClient

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')

# Disable Flask's default logger to avoid duplicate logs
log = logging.getLogger('werkzeug')
log.setLevel(logging.WARNING)

logger = logging.getLogger(__name__)

# Configure Claude API
ANTHROPIC_API_KEY = os.environ.get('ANTHROPIC_API_KEY')
CLAUDE_MODEL = os.environ.get('CLAUDE_MODEL', 'claude-sonnet-4-5-20250929')
MAX_TOKENS = int(os.environ.get('MAX_TOKENS', 4000))
TEMPERATURE = float(os.environ.get('TEMPERATURE', 0.3))

# Initialize Anthropic client
if not ANTHROPIC_API_KEY:
    print("WARNING: ANTHROPIC_API_KEY not set. Please configure it in .env file")
    client = None
else:
    client = Anthropic(api_key=ANTHROPIC_API_KEY)

# Initialize Jira client
jira_client = JiraClient()
if jira_client.is_enabled():
    print("INFO: Jira integration enabled")
else:
    print("INFO: Jira integration disabled (configure JIRA_URL and JIRA_API_TOKEN to enable)")

# Jira Labels Configuration
def parse_labels(label_string):
    """Parse comma-separated label string into a list."""
    if not label_string:
        return []
    return [label.strip() for label in label_string.split(',') if label.strip()]

JIRA_DEFAULT_LABELS = parse_labels(os.environ.get('JIRA_DEFAULT_LABELS', ''))
JIRA_REQUIRED_LABELS = parse_labels(os.environ.get('JIRA_REQUIRED_LABELS', ''))

# Prompt Configuration
PROMPTS_DIR = os.path.join(os.path.dirname(__file__), 'prompts')
SYSTEM_PROMPT_FILE = os.environ.get('CLAUDE_SYSTEM_PROMPT_FILE', os.path.join(PROMPTS_DIR, 'system_prompt.txt'))
USER_PROMPT_TEMPLATE_FILE = os.environ.get('CLAUDE_USER_PROMPT_FILE', os.path.join(PROMPTS_DIR, 'user_prompt_template.txt'))


def load_prompt_from_file(file_path, default_content=''):
    """
    Load a prompt from a file. Falls back to default content if file doesn't exist.

    Args:
        file_path (str): Path to the prompt file
        default_content (str): Default content if file doesn't exist

    Returns:
        str: The prompt content
    """
    try:
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                logger.info(f"Loaded prompt from {file_path}")
                return content
        else:
            logger.warning(f"Prompt file not found: {file_path}, using default")
            return default_content
    except Exception as e:
        logger.error(f"Error loading prompt from {file_path}: {str(e)}")
        return default_content


def extract_acceptance_criteria(user_story):
    """
    Extract individual acceptance criteria from the user story.

    Returns a list of tuples: (ac_number, ac_text)
    """
    criteria = []

    # Find the Acceptance Criteria section
    ac_match = re.search(r'Acceptance Criteria[:\s]*(.+)', user_story, re.IGNORECASE | re.DOTALL)
    if not ac_match:
        return criteria

    ac_section = ac_match.group(1)

    # Find all numbered acceptance criteria (supports various formats: "1.", "1)", "AC1", etc.)
    # This regex looks for lines starting with numbers or "AC" followed by number
    ac_pattern = r'(?:^|\n)\s*(?:AC\s*)?(\d+)[.:\)]\s*(.+?)(?=(?:\n\s*(?:AC\s*)?\d+[.:\)])|$)'
    matches = re.findall(ac_pattern, ac_section, re.IGNORECASE | re.DOTALL)

    if matches:
        for num, text in matches:
            criteria.append((int(num), text.strip()))
    else:
        # Fallback: try to find GIVEN/WHEN/THEN patterns without numbering
        patterns = re.findall(r'(\bGIVEN\b.*?\bWHEN\b.*?\bTHEN\b[^\n]*(?:\n(?!\s*\bGIVEN\b)[^\n]*)*)',
                            ac_section, re.IGNORECASE | re.DOTALL)
        for i, pattern in enumerate(patterns, 1):
            criteria.append((i, pattern.strip()))

    return criteria


def validate_user_story(user_story):
    """Validate that the user story has the required format."""
    if not user_story or len(user_story.strip()) < 50:
        return False, "User story is too short or empty"

    if "Acceptance Criteria" not in user_story:
        return False, "User story must contain 'Acceptance Criteria' section"

    # Check for at least one GIVEN/WHEN/THEN pattern
    if not re.search(r'\bGIVEN\b.*\bWHEN\b.*\bTHEN\b', user_story, re.IGNORECASE | re.DOTALL):
        return False, "User story must contain at least one acceptance criterion with GIVEN/WHEN/THEN structure"

    return True, "Valid"


def generate_test_cases(user_story):
    """Call Claude API to generate test cases from user story."""
    if not client:
        raise Exception("Anthropic API client not initialized. Please check your API key.")

    # Load prompts from configured files
    system_prompt = load_prompt_from_file(SYSTEM_PROMPT_FILE)
    user_prompt_template = load_prompt_from_file(USER_PROMPT_TEMPLATE_FILE)

    if not system_prompt:
        raise Exception(f"System prompt file not found: {SYSTEM_PROMPT_FILE}")
    if not user_prompt_template:
        raise Exception(f"User prompt template file not found: {USER_PROMPT_TEMPLATE_FILE}")

    # Format the user prompt with the actual user story
    user_prompt = user_prompt_template.format(user_story=user_story)

    try:
        message = client.messages.create(
            model=CLAUDE_MODEL,
            max_tokens=MAX_TOKENS,
            temperature=TEMPERATURE,
            system=system_prompt,
            messages=[
                {
                    "role": "user",
                    "content": user_prompt
                }
            ]
        )

        response_text = message.content[0].text

        # Try to extract JSON if there's extra text
        json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
        if json_match:
            response_text = json_match.group(0)

        test_cases = json.loads(response_text)
        return test_cases

    except json.JSONDecodeError as e:
        raise Exception(f"Failed to parse Claude API response as JSON: {str(e)}")
    except Exception as e:
        raise Exception(f"Error calling Claude API: {str(e)}")


@app.route('/')
def index():
    """Render the input page."""
    return render_template('index.html',
                         jira_enabled=jira_client.is_enabled(),
                         claude_enabled=(client is not None))


@app.route('/jira/fetch', methods=['POST'])
def fetch_jira_story():
    """Fetch user story from Jira."""
    try:
        if not jira_client.is_enabled():
            logger.warning("Jira fetch attempted but Jira integration is not configured")
            return jsonify({'error': 'Jira integration is not configured'}), 400

        data = request.get_json()
        issue_key = data.get('issue_key', '').strip().upper()

        if not issue_key:
            logger.warning("Jira fetch attempted without issue key")
            return jsonify({'error': 'Issue key is required'}), 400

        logger.info(f"Fetching Jira story for issue: {issue_key}")

        # Fetch user story from Jira
        user_story = jira_client.extract_user_story(issue_key)
        metadata = jira_client.get_issue_metadata(issue_key)
        existing_test_cases = jira_client.get_tested_by_issues(issue_key)

        # Store only the issue key in session (existing test cases will be fetched fresh on review page)
        session['jira_issue_key'] = issue_key

        logger.info(f"Successfully fetched {issue_key}. Found {len(existing_test_cases)} existing test cases")

        return jsonify({
            'user_story': user_story,
            'metadata': metadata,
            'existing_test_cases_count': len(existing_test_cases)
        })

    except Exception as e:
        logger.error(f"Error fetching Jira story: {str(e)}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@app.route('/jira/test-plans', methods=['GET'])
def get_test_plans():
    """Fetch available test plans using configured JQL."""
    try:
        if not jira_client.is_enabled():
            logger.warning("Test plans fetch attempted but Jira integration is not configured")
            return jsonify({'error': 'Jira integration is not configured'}), 400

        logger.info("Fetching test plans")
        test_plans = jira_client.search_test_plans()

        logger.info(f"Successfully fetched {len(test_plans)} test plans")
        return jsonify({'test_plans': test_plans})

    except Exception as e:
        logger.error(f"Error fetching test plans: {str(e)}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@app.route('/generate', methods=['POST'])
def generate():
    """Generate test cases from user story (or create empty ones for manual mode)."""
    try:
        data = request.get_json()
        user_story = data.get('user_story', '')

        # Validate input
        is_valid, message = validate_user_story(user_story)
        if not is_valid:
            return jsonify({'error': message}), 400

        # If Claude is enabled, generate test cases with AI
        if client:
            test_cases = generate_test_cases(user_story)
        else:
            # Manual mode: create empty test case structure with original acceptance criteria
            logger.info("Claude API not available - creating empty test cases for manual entry")

            # Extract acceptance criteria from the user story
            criteria = extract_acceptance_criteria(user_story)

            if not criteria:
                # Fallback: if extraction fails, create at least one empty test case
                logger.warning("Could not extract acceptance criteria, creating one empty test case")
                criteria = [(1, '')]

            test_cases = {
                'test_cases': [
                    {
                        'ac_number': ac_num,
                        'original_ac': ac_text,
                        'title': '',
                        'description': '',
                        'gherkin': ''
                    }
                    for ac_num, ac_text in criteria
                ]
            }
            logger.info(f"Created {len(criteria)} empty test cases with original acceptance criteria")

        # Store in session for later use
        session['test_cases'] = test_cases
        session['user_story'] = user_story

        return jsonify(test_cases)

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/review')
def review():
    """Render the review page with generated test cases."""
    test_cases = session.get('test_cases')
    if not test_cases:
        logger.warning("Review page accessed without test cases in session")
        return "No test cases found. Please generate test cases first.", 400

    jira_issue_key = session.get('jira_issue_key')

    logger.info(f"Rendering review page with {len(test_cases.get('test_cases', []))} generated test cases")

    # Fetch existing test cases fresh from Jira every time
    existing_test_cases = []
    if jira_client.is_enabled() and jira_issue_key:
        try:
            logger.info(f"Fetching fresh existing test cases for {jira_issue_key}")
            existing_test_cases = jira_client.get_tested_by_issues(jira_issue_key)
            logger.info(f"Found {len(existing_test_cases)} existing test cases from Jira")
        except Exception as e:
            logger.error(f"Failed to fetch existing test cases: {str(e)}", exc_info=True)
            # Continue without existing test cases if fetch fails

    # Create a mapping of AC number to existing test cases for easy lookup
    existing_by_ac = {}
    for tc in existing_test_cases:
        ac_num = tc.get('ac_number')
        if ac_num:
            if ac_num not in existing_by_ac:
                existing_by_ac[ac_num] = []
            existing_by_ac[ac_num].append(tc)

    logger.info(f"Mapped existing test cases to {len(existing_by_ac)} different AC numbers")
    if existing_by_ac:
        logger.info(f"ACs with existing test cases: {sorted(existing_by_ac.keys())}")

    # Fetch available test plans if Jira is enabled
    test_plans = []
    if jira_client.is_enabled():
        try:
            logger.info("Fetching test plans for review page")
            test_plans = jira_client.search_test_plans()
            logger.info(f"Loaded {len(test_plans)} test plans")
        except Exception as e:
            logger.error(f"Failed to fetch test plans: {str(e)}", exc_info=True)
            # Continue without test plans if fetch fails

    return render_template(
        'review.html',
        test_cases=test_cases,
        existing_test_cases=existing_by_ac,
        jira_issue_key=jira_issue_key,
        default_labels=JIRA_DEFAULT_LABELS,
        required_labels=JIRA_REQUIRED_LABELS,
        test_plans=test_plans
    )


@app.route('/jira/create-test', methods=['POST'])
def create_jira_test():
    """Create a new test case in Jira."""
    try:
        if not jira_client.is_enabled():
            return jsonify({'error': 'Jira integration is not configured'}), 400

        data = request.get_json()
        title = data.get('title')
        description = data.get('description')
        gherkin = data.get('gherkin')
        ac_number = data.get('ac_number')
        selected_labels = data.get('labels', [])
        test_plan_key = data.get('test_plan_key')

        if not title or not gherkin:
            return jsonify({'error': 'Title and Gherkin are required'}), 400

        # Validate that at least one required label is selected
        if JIRA_REQUIRED_LABELS and not any(label in selected_labels for label in JIRA_REQUIRED_LABELS):
            return jsonify({'error': 'At least one required label must be selected'}), 400

        # Validate that a test plan is selected
        if not test_plan_key:
            return jsonify({'error': 'Test plan selection is required'}), 400

        # Combine default labels with selected labels
        all_labels = list(set(JIRA_DEFAULT_LABELS + selected_labels))

        # Get the parent issue key from session
        parent_issue_key = session.get('jira_issue_key')
        if not parent_issue_key:
            return jsonify({'error': 'No parent issue found in session'}), 400

        logger.info(f"Creating test case for parent issue: {parent_issue_key}")
        logger.info(f"Labels to apply: {all_labels}")
        logger.info(f"Test plan: {test_plan_key}")

        # Create the test case in Jira with test plan as a list
        result = jira_client.create_test_case(
            parent_issue_key=parent_issue_key,
            title=title,
            description=description,
            gherkin=gherkin,
            ac_number=ac_number,
            labels=all_labels,
            test_plan_keys=[test_plan_key]
        )

        logger.info(f"Test case created successfully: {result.get('key')}")
        return jsonify(result)

    except Exception as e:
        logger.error(f"Error creating Jira test case: {str(e)}", exc_info=True)
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    app.run(debug=True)
