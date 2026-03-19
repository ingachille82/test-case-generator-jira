# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

A Flask-based web application that uses Claude API to automatically generate test case titles and Gherkin scenarios from API user story acceptance criteria. The tool provides a supervised workflow where QA engineers can review and edit generated content before creating Jira tickets.

## Development Setup

This project has not been implemented yet. When implementing:

1. **Initialize Python environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install flask anthropic python-dotenv
   pip freeze > requirements.txt
   ```

2. **Configure environment variables:**
   Create `.env` file with:
   ```
   ANTHROPIC_API_KEY=your_api_key_here
   CLAUDE_MODEL=claude-sonnet-4-5-20250929
   MAX_TOKENS=4000
   TEMPERATURE=0.3
   ```

3. **Run the application:**
   ```bash
   flask run
   # Or for development:
   flask run --debug
   ```

## Architecture Overview

The application follows a linear workflow:

```
User Story Input → Claude API → Generated Test Cases → QA Review/Edit → Export for Jira
```

**Key components to implement:**
- **Input validation**: Parse and validate user story format (GIVEN/WHEN/THEN acceptance criteria)
- **Claude API integration**: Use Anthropic Python SDK to generate test cases
- **Side-by-side UI**: Display generated vs editable test cases for QA review
- **Export module**: Support clipboard, Markdown, JSON, and Excel formats

### Key Features
- Side-by-side view of generated and editable test cases
- Individual test case approval/rejection
- Edit generated content before export
- Export to clipboard or downloadable format

## User Story Format

Our user stories follow this structure:

```
**As a** [Role/User Type]
**I want to** [Action/Goal]
**So that** [Business Value]

**Acceptance Criteria:**
1. **GIVEN** [Preconditions] **WHEN** [Action] **THEN** [Expected Result]
2. **GIVEN** [Preconditions] **WHEN** [Action] **THEN** [Expected Result]
...
```

### Example User Story

**As a** Dataspace Governance Authority end user with the IATTR_M (Tier 2 identity attributes manager) or APPLICANT role  
**I want to** request issuance of a participant credential (and receive the credential content)  
**So that** the participant's agent can install the credential and participate in trusted data exchanges

**Acceptance Criteria:**
1. **GIVEN** I am an authenticated user with the IATTR_M role **AND** the participant with the specified participantId exists **WHEN** I send a POST /participants/{participantId}/credentials request **THEN** the API returns HTTP 200 OK
2. **GIVEN** I am an authenticated user with the APPLICANT role **AND** the specified participantId is the participant I onboarded **AND** the participant does not have an installed credential yet **WHEN** I send a POST /participants/{participantId}/credentials request **THEN** the API returns HTTP 200 OK
3. **GIVEN** I am an authenticated user with the APPLICANT role **AND** the specified participantId is the participant I onboarded **AND** the participant already has an installed credential **WHEN** I send a POST /participants/{participantId}/credentials request (i.e., I try to download/obtain the credential again) **THEN** the API returns HTTP 403 Forbidden
[... more acceptance criteria ...]

## Required Output Format

For each acceptance criterion, generate:

### 1. Jira Test Case Title
- Concise, descriptive title (50-80 characters)
- Should clearly indicate the scenario being tested
- Format: `Test [Action] - [Key Condition] - [Expected Result]`

### 2. Gherkin Scenario
- Simplified GIVEN/WHEN/THEN format
- GIVEN: Authentication state and preconditions
- WHEN: API call with specific parameters
- THEN: Status code verification and response body checks (if applicable)

### Output Structure

```json
{
  "test_cases": [
    {
      "ac_number": 1,
      "original_ac": "[Original acceptance criteria text]",
      "title": "[Jira test case title]",
      "gherkin": "[Formatted Gherkin scenario]"
    },
    ...
  ]
}
```

## Claude API Prompt Template

### System Prompt

You are a QA test case generator specialized in API testing. Your task is to convert user story acceptance criteria into structured test cases with Jira titles and Gherkin scenarios.

Follow these rules strictly:
1. Generate one test case per acceptance criterion
2. Keep titles concise and descriptive
3. Simplify Gherkin to focus on API calls and verifications
4. In THEN statements, only include status code and response body validations
5. Use the exact role names, API endpoints, and parameters from the acceptance criteria
6. Maintain consistent formatting

### User Prompt Template

```
Analyze the following user story and generate test cases for each acceptance criterion.

USER STORY:
{user_story_text}

For each acceptance criterion, provide:
1. A concise Jira test case title
2. A simplified Gherkin scenario

OUTPUT FORMAT (JSON):
{
  "test_cases": [
    {
      "ac_number": <number>,
      "original_ac": "<full original text>",
      "title": "<test case title>",
      "gherkin": "<GIVEN/WHEN/THEN scenario>"
    }
  ]
}

GHERKIN FORMAT RULES:
- GIVEN: Start with "I am logged in with <ROLE>" or "I am not authenticated"
- GIVEN: Include all preconditions with AND clauses
- WHEN: Describe the API call clearly (e.g., "I send a POST /participants/{participantId}/credentials request")
- THEN: Include ONLY status code verification and response body checks (if needed)
- Keep it concise and focused on API behavior

TITLE FORMAT RULES:
- 50-80 characters
- Format: "Test [action] - [condition] - [expected result]"
- Example: "Test credential issuance - IATTR_M role - returns 200 OK"
```

## Example Expected Output

For the acceptance criterion:
> **GIVEN** I am an authenticated user with the IATTR_M role **AND** the participant with the specified participantId exists **WHEN** I send a POST /participants/{participantId}/credentials request **THEN** the API returns HTTP 200 OK

Expected output:

```json
{
  "ac_number": 1,
  "original_ac": "GIVEN I am an authenticated user with the IATTR_M role AND the participant with the specified participantId exists WHEN I send a POST /participants/{participantId}/credentials request THEN the API returns HTTP 200 OK",
  "title": "Test credential issuance - IATTR_M role with valid participant - returns 200 OK",
  "gherkin": "GIVEN I am logged in with IATTR_M role\nAND the participant with the specified participantId exists\nWHEN I send a POST /participants/{participantId}/credentials request\nTHEN I get a 200 OK response"
}
```

More examples:

### AC 2:
```json
{
  "ac_number": 2,
  "original_ac": "GIVEN I am an authenticated user with the APPLICANT role AND the specified participantId is the participant I onboarded AND the participant does not have an installed credential yet WHEN I send a POST /participants/{participantId}/credentials request THEN the API returns HTTP 200 OK",
  "title": "Test credential issuance - APPLICANT first-time request - returns 200 OK",
  "gherkin": "GIVEN I am logged in with APPLICANT role\nAND the specified participantId is the participant I onboarded\nAND the participant does not have an installed credential yet\nWHEN I send a POST /participants/{participantId}/credentials request\nTHEN I get a 200 OK response"
}
```

### AC 6:
```json
{
  "ac_number": 6,
  "original_ac": "GIVEN I am not authenticated WHEN I send a POST /participants/{participantId}/credentials request THEN the API returns HTTP 401 Unauthorized",
  "title": "Test credential issuance - unauthenticated user - returns 401 Unauthorized",
  "gherkin": "GIVEN I am not authenticated\nWHEN I send a POST /participants/{participantId}/credentials request\nTHEN I get a 401 Unauthorized response"
}
```

### AC 9:
```json
{
  "ac_number": 9,
  "original_ac": "GIVEN I am an authenticated user with one of the permitted roles AND a prerequisite for issuance is missing or invalid (e.g., no CSR available or participant state invalid for issuance) WHEN I send a POST /participants/{participantId}/credentials request THEN the API returns HTTP 422 Unprocessable Entity",
  "title": "Test credential issuance - missing prerequisites - returns 422 Unprocessable Entity",
  "gherkin": "GIVEN I am logged in with a permitted role\nAND a prerequisite for issuance is missing or invalid\nWHEN I send a POST /participants/{participantId}/credentials request\nTHEN I get a 422 Unprocessable Entity response\nAND the response body contains error details about the missing prerequisite"
}
```

## Flask Application Pages

### 1. Input Page (`/`)
- Textarea for user story input
- "Generate Test Cases" button
- Loading indicator during API call

### 2. Review Page (`/review`)
Side-by-side layout:
- Left: Generated test cases (read-only)
- Right: Editable versions with approve/reject buttons per test case

### 3. Export Endpoints
- `/export/clipboard` - Copy approved test cases
- `/export/markdown` - Download as .md file
- `/export/json` - Download as .json file
- `/export/excel` - Download as .xlsx file (optional)

## Claude API Integration

### API Configuration
- **Model**: `claude-sonnet-4-5-20250929`
- **Max Tokens**: 4000
- **Temperature**: 0.3 (for consistent, deterministic output)

### Implementation Pattern
```python
import anthropic

client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

message = client.messages.create(
    model="claude-sonnet-4-5-20250929",
    max_tokens=4000,
    temperature=0.3,
    system="You are a QA test case generator specialized in API testing...",
    messages=[
        {
            "role": "user",
            "content": f"Analyze the following user story and generate test cases...\n\n{user_story}"
        }
    ]
)

response_text = message.content[0].text
test_cases = json.loads(response_text)
```

## Input Validation Rules

Before sending to Claude API, validate:
- User story contains "Acceptance Criteria" section
- At least one acceptance criterion is present
- Each AC follows GIVEN/WHEN/THEN structure

## Error Handling Strategies

1. **Malformed JSON Response**: Parse with error handling; retry if needed
2. **Missing Acceptance Criteria**: Display validation error to user
3. **API Rate Limits**: Implement exponential backoff
4. **Invalid API Key**: Show clear error message with setup instructions

---

**Version**: 1.0
**Last Updated**: 2025-10-27
**Maintained By**: QA Automation Team