async function updateLabels({ jiraBaseUrl, jiraToken, issueKey, newLabels }) {
  const existing = await fetchCurrentLabels({ jiraBaseUrl, jiraToken, issueKey });

  // controlla se ci sono label nuove da aggiungere
  const hasNewLabels = newLabels.some(l => !existing.includes(l));
  if (!hasNewLabels) {
    return { issueKey, labels: existing, changed: false };
  }

  // merge: aggiunge le nuove senza rimuovere le esistenti
  const merged = [...new Set([...existing, ...newLabels])];

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