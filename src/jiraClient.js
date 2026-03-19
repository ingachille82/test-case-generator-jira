/**
 * Jira REST API v3 client.
 *
 * Responsibilities:
 *  1. Create a Jira issue of type "Test" for each Gherkin scenario.
 *  2. Set the description to the Gherkin steps (plain text / ADF).
 *  3. Link the Test to the parent User Story via an "is tested by" / "tests" link.
 *
 * Notes on issue type:
 *  - Jira Software: use issuetype name "Test" (requires Zephyr Scale / Xray / or a custom type).
 *  - If your project uses Xray, the type name is "Test" and the Gherkin steps can also be stored
 *    in the custom field "cucumber" (see XRAY_CUCUMBER_TYPE below).
 *  - Adjust ISSUE_TYPE and LINK_TYPE to match your Jira configuration.
 */

const ISSUE_TYPE = process.env.JIRA_TEST_ISSUE_TYPE || 'Test';           // e.g. "Test", "Task"
const LINK_TYPE  = process.env.JIRA_LINK_TYPE        || 'is tested by';  // outward direction from Story→Test

/**
 * Build an Atlassian Document Format (ADF) document from plain text.
 * This gives nicely formatted descriptions inside Jira.
 */
function buildADF(scenario) {
  const paragraphs = scenario.steps.map(step => ({
    type: 'paragraph',
    content: [{ type: 'text', text: step }],
  }));

  return {
    type: 'doc',
    version: 1,
    content: [
      {
        type: 'heading',
        attrs: { level: 3 },
        content: [{ type: 'text', text: `Feature: ${scenario.featureTitle || 'N/A'}` }],
      },
      {
        type: 'codeBlock',
        attrs: { language: 'gherkin' },
        content: [{ type: 'text', text: scenario.rawText }],
      },
      ...paragraphs.length > 0 ? [] : [],
    ],
  };
}

/**
 * Create a single Jira issue of type Test.
 */
async function createTestIssue({ jiraBaseUrl, jiraToken, projectKey, scenario }) {
  const url = `${jiraBaseUrl}/rest/api/3/issue`;

  const body = {
    fields: {
      project: { key: projectKey },
      summary: scenario.title,
      issuetype: { name: ISSUE_TYPE },
      description: buildADF(scenario),
      // Labels from Gherkin tags (strip the @ prefix)
      labels: scenario.tags.map(t => t.replace(/^@/, '')),
    },
  };

  const response = await fetch(url, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Authorization: jiraToken,
    },
    body: JSON.stringify(body),
  });

  if (!response.ok) {
    const err = await response.text();
    throw new Error(`Jira createIssue failed (${response.status}): ${err}`);
  }

  return response.json(); // { id, key, self }
}

/**
 * Link a Test issue back to the User Story.
 * Direction: User Story  --[is tested by]--> Test
 */
async function linkToUserStory({ jiraBaseUrl, jiraToken, userStoryKey, testKey }) {
  const url = `${jiraBaseUrl}/rest/api/3/issueLink`;

  const body = {
    type: { name: LINK_TYPE },
    inwardIssue:  { key: testKey },
    outwardIssue: { key: userStoryKey },
  };

  const response = await fetch(url, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Authorization: jiraToken,
    },
    body: JSON.stringify(body),
  });

  if (!response.ok) {
    const err = await response.text();
    throw new Error(`Jira linkIssue failed (${response.status}): ${err}`);
  }
  // 201 No Content on success
}

/**
 * Main entry point: create all Test issues and link them to the User Story.
 *
 * @returns {Array<{scenarioTitle, testKey, testUrl}>}
 */
async function createJiraTests({ jiraBaseUrl, jiraToken, projectKey, userStoryKey, scenarios }) {
  const results = [];

  for (const scenario of scenarios) {
    console.log(`Creating Test for scenario: "${scenario.title}"`);

    const issue = await createTestIssue({ jiraBaseUrl, jiraToken, projectKey, scenario });

    console.log(`  → Created ${issue.key}. Linking to ${userStoryKey}...`);
    await linkToUserStory({ jiraBaseUrl, jiraToken, userStoryKey, testKey: issue.key });

    results.push({
      scenarioTitle: scenario.title,
      testKey: issue.key,
      testUrl: `${jiraBaseUrl}/browse/${issue.key}`,
    });
  }

  return results;
}

module.exports = { createJiraTests };
