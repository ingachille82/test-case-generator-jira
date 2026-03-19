/**
 * jiraLabelUpdater.js
 *
 * Per ogni scenario nel feature file che ha un tag con una Jira issue key
 * (es. @SCRUM-14), recupera le label esistenti dell'issue e le aggiorna
 * aggiungendo i nuovi tag (senza rimuovere quelli già presenti).
 *
 * Tag Jira key: qualsiasi tag che corrisponde al pattern PROJECTKEY-NUMBER
 */

const JIRA_KEY_PATTERN = /^[A-Z]+-\d+$/;

/**
 * Determina se un tag è una Jira issue key (es. SCRUM-14)
 */
function isJiraKey(tag) {
  return JIRA_KEY_PATTERN.test(tag.replace(/^@/, ''));
}

/**
 * Recupera le label attuali di un issue Jira
 */
async function fetchCurrentLabels({ jiraBaseUrl, jiraToken, issueKey }) {
  const url = `${jiraBaseUrl}/rest/api/3/issue/${issueKey}?fields=labels`;

  const response = await fetch(url, {
    headers: {
      Authorization: jiraToken,
      Accept: 'application/json',
    },
  });

  if (!response.ok) {
    const err = await response.text();
    throw new Error(`Jira fetchIssue(${issueKey}) failed (${response.status}): ${err}`);
  }

  const data = await response.json();
  return (data.fields.labels || []);
}

/**
 * Aggiorna le label di un issue Jira (merge: aggiunge senza rimuovere)
 */
async function updateLabels({ jiraBaseUrl, jiraToken, issueKey, newLabels }) {
  const existing = await fetchCurrentLabels({ jiraBaseUrl, jiraToken, issueKey });

  // merge: unione senza duplicati
  const merged = [...new Set([...existing, ...newLabels])];

  // nessuna modifica necessaria
  if (merged.length === existing.length &&
      merged.every(l => existing.includes(l))) {
    return { issueKey, labels: merged, changed: false };
  }

  const url = `${jiraBaseUrl}/rest/api/3/issue/${issueKey}`;
  const response = await fetch(url, {
    method: 'PUT',
    headers: {
      Authorization: jiraToken,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      fields: { labels: merged },
    }),
  });

  if (!response.ok) {
    const err = await response.text();
    throw new Error(`Jira updateLabels(${issueKey}) failed (${response.status}): ${err}`);
  }

  return { issueKey, labels: merged, changed: true };
}

/**
 * Entry point principale.
 * Elabora tutti gli scenari del feature file che hanno un tag Jira key.
 *
 * @param {object} params
 * @param {string} params.jiraBaseUrl
 * @param {string} params.jiraToken
 * @param {Array}  params.scenarios  - output di parseGherkin()
 * @returns {Array<{issueKey, scenarioTitle, labels, changed, skipped}>}
 */
async function updateJiraLabels({ jiraBaseUrl, jiraToken, scenarios }) {
  const results = [];

  for (const scenario of scenarios) {
    // cerca il tag che è una Jira key (es. @SCRUM-14)
    const jiraKeyTag = scenario.tags.find(t => isJiraKey(t));

    if (!jiraKeyTag) {
      results.push({
        scenarioTitle: scenario.title,
        skipped: true,
        reason: 'Nessun tag Jira key trovato (es. @SCRUM-14)',
      });
      continue;
    }

    const issueKey = jiraKeyTag.replace(/^@/, '');

    // tutti gli altri tag diventano label (esclusa la jira key stessa)
    const newLabels = scenario.tags
      .filter(t => !isJiraKey(t))
      .map(t => t.replace(/^@/, ''));

    console.log(`Aggiornamento label per ${issueKey}: +[${newLabels.join(', ')}]`);

    try {
      const result = await updateLabels({ jiraBaseUrl, jiraToken, issueKey, newLabels });
      results.push({
        issueKey,
        scenarioTitle: scenario.title,
        labels: result.labels,
        changed: result.changed,
        skipped: false,
      });
    } catch (err) {
      results.push({
        issueKey,
        scenarioTitle: scenario.title,
        error: err.message,
        skipped: false,
      });
    }
  }

  return results;
}

module.exports = { updateJiraLabels };
