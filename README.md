# Test Case Generator

A Flask-based web application that automatically generates test case titles and Gherkin scenarios from API user story acceptance criteria using Claude AI.

## Overview

This tool helps QA engineers quickly convert user story acceptance criteria into structured test cases with:
- Concise Jira-ready test case titles
- Simplified Gherkin scenarios (GIVEN/WHEN/THEN format)
- Side-by-side review and editing interface
- Multiple export formats (clipboard, Markdown, JSON, Excel)

## Prerequisites

**Option 1: Docker (Recommended)**
- Docker and Docker Compose
- Anthropic API key ([Get one here](https://console.anthropic.com/))

**Option 2: Local Python**
- Python 3.8 or higher
- Anthropic API key ([Get one here](https://console.anthropic.com/))

## Installation

### Option 1: Using Docker (Recommended)

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd test-case-generator
   ```

2. **Configure environment variables:**
   ```bash
   cp .env.example .env
   # Edit .env and add your ANTHROPIC_API_KEY
   # Optionally add Jira credentials for Jira integration
   ```

3. **Build and run with Docker Compose:**
   ```bash
   docker-compose up -d
   ```

4. **Access the application:**
   Open `http://localhost:5000` in your browser

5. **View logs (optional):**
   ```bash
   docker-compose logs -f
   ```

6. **Stop the application:**
   ```bash
   docker-compose down
   ```

### Option 2: Local Python Installation

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd test-case-generator
   ```

2. **Create and activate virtual environment:**
   ```bash
   # On Linux/macOS
   python -m venv venv
   source venv/bin/activate

   # On Windows
   python -m venv venv
   venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables:**

   Create a `.env` file in the project root:
   ```env
   ANTHROPIC_API_KEY=your_api_key_here
   CLAUDE_MODEL=claude-sonnet-4-5-20250929
   MAX_TOKENS=4000
   TEMPERATURE=0.3

   # Optional: Jira Integration
   JIRA_URL=https://your-company.atlassian.net
   JIRA_API_TOKEN=your_jira_api_token_here
   ```

## Jira Integration (Optional)

The application supports fetching user stories directly from Jira. To enable this feature:

1. **Generate a Jira API Token:**
   - Log in to https://id.atlassian.com/manage-profile/security/api-tokens
   - Click "Create API token"
   - Give it a name (e.g., "Test Case Generator")
   - Copy the generated token

2. **Configure Jira credentials in `.env`:**
   ```env
   JIRA_URL=https://your-company.atlassian.net
   JIRA_API_TOKEN=your_generated_token_here
   ```

3. **Restart the application** (if already running)

4. **Use Jira integration:**
   - In the web interface, click "Fetch from Jira" tab
   - Enter a Jira issue key (e.g., "PROJ-123")
   - Click "Fetch Story" to retrieve the user story
   - The story description will be populated automatically
   - Click "Generate Test Cases" to proceed

**Note:** If Jira credentials are not configured, the "Fetch from Jira" option will not appear, and you can still use manual input.

## Running the Application

### Development Mode

```bash
flask run --debug
```

The application will be available at `http://127.0.0.1:5000`

### Production Mode

```bash
flask run
```

## Usage

1. **Input User Story:**
   - Navigate to the home page
   - Paste your user story with acceptance criteria
   - Click "Generate Test Cases"

2. **Review Generated Test Cases:**
   - View generated test cases on the left side
   - Edit titles and Gherkin scenarios on the right side
   - Approve or reject individual test cases

3. **Export:**
   - Copy approved test cases to clipboard
   - Download as Markdown, JSON, or Excel format

## User Story Format

Your user stories should follow this structure:

```
**As a** [Role/User Type]
**I want to** [Action/Goal]
**So that** [Business Value]

**Acceptance Criteria:**
1. **GIVEN** [Preconditions] **WHEN** [Action] **THEN** [Expected Result]
2. **GIVEN** [Preconditions] **WHEN** [Action] **THEN** [Expected Result]
...
```

### Example

```
**As a** API user with admin role
**I want to** create new participants
**So that** they can access the system

**Acceptance Criteria:**
1. **GIVEN** I am authenticated with admin role **WHEN** I send a POST /participants request **THEN** the API returns HTTP 201 Created
2. **GIVEN** I am not authenticated **WHEN** I send a POST /participants request **THEN** the API returns HTTP 401 Unauthorized
```

## Project Structure

```
test-case-generator/
├── app.py                 # Flask application entry point
├── jira_client.py        # Jira API client
├── templates/             # HTML templates
│   ├── index.html        # Input page
│   └── review.html       # Review page
├── static/               # CSS, JS, and other static files
│   └── style.css         # Application styling
├── tests/                # Unit tests
│   ├── __init__.py
│   └── test_jira_client.py
├── requirements.txt      # Python dependencies
├── Dockerfile            # Docker image configuration
├── docker-compose.yml    # Docker Compose configuration
├── .env                  # Environment variables (not in git)
├── .env.example          # Example environment variables
├── .gitignore           # Git ignore rules
├── CLAUDE.md            # Claude Code guidance and specifications
└── README.md            # This file
```

## Running Tests

The project includes unit tests for critical components like the Jira client.

### Running All Tests

```bash
# Activate virtual environment first (if using local Python)
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Run all tests
pytest

# Run with verbose output
pytest -v

# Run with coverage report
pytest --cov=. --cov-report=html
```

### Running Specific Tests

```bash
# Run tests for a specific file
pytest tests/test_jira_client.py

# Run tests for a specific class
pytest tests/test_jira_client.py::TestJiraClientExtractACNumber

# Run a specific test
pytest tests/test_jira_client.py::TestJiraClientExtractACNumber::test_extract_ac_number_basic_format
```

### Test Coverage

After running tests with coverage, open `htmlcov/index.html` in your browser to see detailed coverage report.

## Troubleshooting

### Docker Issues

**"Invalid API Key" Error**
- Verify your `ANTHROPIC_API_KEY` is set correctly in `.env`
- Ensure the `.env` file is in the project root directory
- Restart the container: `docker-compose restart`

**Port Already in Use**
- Change the port in `docker-compose.yml`:
  ```yaml
  ports:
    - "5001:5000"  # Change 5000 to 5001
  ```
- Or stop the process using port 5000

**Container Won't Start**
- Check logs: `docker-compose logs`
- Rebuild the image: `docker-compose up -d --build`

### Local Python Issues

**"Invalid API Key" Error**
- Verify your `ANTHROPIC_API_KEY` is set correctly in `.env`
- Ensure the `.env` file is in the project root directory
- Check that you've activated the virtual environment

**"Module Not Found" Errors**
- Make sure you've activated the virtual environment
- Run `pip install -r requirements.txt` again

**Port Already in Use**
- Change the port: `flask run --port 5001`
- Or stop the process using port 5000

## Using Claude Directly (Without This App)

If you prefer to generate test cases directly using Claude (via claude.ai, Claude API, or Claude Code) without running this application, you can use the following prompt:

### Prompt Template

```
You are a QA test case generator specialized in API and UI testing. Your task is to convert user story acceptance criteria into structured test cases with Jira titles, Jira descriptions and Gherkin scenarios.

Follow these rules strictly:
1. Generate one or more test cases per acceptance criterion (depending on the complexity of the AC)
2. Keep titles concise and descriptive (50-80 characters)
3. Keep description concise and descriptive, by and also add AC X (where X is the AC number) at the begininning
4. Simplify Gherkin to focus either on API calls and verifications or UI navigation and actions
5. If a scenario has the string [UI] in title, do not copy the invokes or sent url in the Acceptance Criteria
6. In THEN statements, only include status code and response body validations for APIs, or expected UI elements appearance for UIs
7. Use the exact role names, API endpoints, page sections and parameters from the acceptance criteria
8. Maintain consistent formatting
9. Output in well-formatted Markdown

Analyze the following user story and generate test cases for each acceptance criterion.

USER STORY:
[PASTE YOUR USER STORY HERE]

For each acceptance criterion, provide:
1. A concise Jira test case title
2. The original acceptance criterion text
3. A simplified Gherkin scenario

OUTPUT FORMAT (Markdown):

# Test Cases

## Test Case 1

**Title:** [Test case title]

**Description:** [Test case description]

**Original Acceptance Criterion:**
[Full original AC text]

**Gherkin Scenario:**
```gherkin
GIVEN [preconditions]
AND [additional preconditions]
WHEN [action]
THEN [expected result]
AND [additional validations if needed]
```

---

## Test Case 2

...

GHERKIN FORMAT RULES:
- GIVEN: Start with "I am logged in with <ROLE>" or "I am not authenticated"
- GIVEN: Include all preconditions with AND clauses
- WHEN: WHEN: If title contains API describe the API call (e.g., "I send a POST /participants/{participantId}/credentials request"); If title contains UI describe navigation clearly "I click on the button to submit the credential")
- THEN: Include ONLY status code verification and response body checks (if needed) or expected UI elements appearance for UIs
- Keep it concise and focused on API behavior or UI behavior

TITLE FORMAT RULES:
- 50-80 characters
- Format: "{Story summary} - {action under test}"
- Example: "[UI] Improvement on Applicant dataspace participant user requests for onboarding credentials - Credential issuance"

DESCRIPTION FORMAT RULES:
- Format: "AC {X}: {Brief description of the test}"
- Example: "AC 3: Check if the credentials issuance matches the expected behavior"

Return the output in Markdown format as shown above.
```

### Example Usage

1. Copy the prompt template above
2. Replace `[PASTE YOUR USER STORY HERE]` with your actual user story
3. Send to Claude via:
   - **claude.ai**: Paste in a new conversation
   - **Claude API**: Use as the system + user prompt
   - **Claude Code**: Paste directly in chat
4. Claude will return a Markdown-formatted response with all test cases
5. Copy the output and use it in your test management tool or documentation

### Example Input

```
**As a** API user with admin role
**I want to** create new participants
**So that** they can access the system

**Acceptance Criteria:**
1. **GIVEN** I am authenticated with admin role **WHEN** I send a POST /participants request **THEN** the API returns HTTP 201 Created
2. **GIVEN** I am not authenticated **WHEN** I send a POST /participants request **THEN** the API returns HTTP 401 Unauthorized
```

### Example Output

```markdown
# Test Cases

## Test Case 1

**Title:** Test participant creation - admin role - returns 201 Created

**Original Acceptance Criterion:**
GIVEN I am authenticated with admin role WHEN I send a POST /participants request THEN the API returns HTTP 201 Created

**Gherkin Scenario:**
```gherkin
GIVEN I am logged in with admin role
WHEN I send a POST /participants request
THEN I get a 201 Created response
```

---

## Test Case 2

**Title:** Test participant creation - unauthenticated - returns 401 Unauthorized

**Original Acceptance Criterion:**
GIVEN I am not authenticated WHEN I send a POST /participants request THEN the API returns HTTP 401 Unauthorized

**Gherkin Scenario:**
```gherkin
GIVEN I am not authenticated
WHEN I send a POST /participants request
THEN I get a 401 Unauthorized response
```
```

## Contributing

This is an internal QA tool. For questions or improvements, contact the QA Automation Team.

## License

Internal use only - QA Automation Team

---

**Version**: 1.0
**Last Updated**: 2025-10-27
