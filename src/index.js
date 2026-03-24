require('dotenv').config();
const express = require('express');
const app = express();
app.use(express.json());
app.use(express.static('public'));

const { parseGherkin }     = require('./gherkinParser');
const { createJiraTests }  = require('./jiraClient');
const { updateJiraLabels } = require('./jiraLabelUpdater');
const { applyTagFilter }   = require('./tagFilter');

/**
 * POST /api/gherkin-to-jira
 * Crea Test su Jira a partire da un feature file e li linka alla User Story.
 * I tag presenti in tags.ignore vengono esclusi dalle label.
 */
app.post('/api/gherkin-to-jira', async (req, res) => {
  const jiraBaseUrl    = req.body.jiraBaseUrl  || process.env.JIRA_BASE_URL;
  const jiraToken      = req.body.jiraToken    || process.env.JIRA_TOKEN;
  const projectKey     = req.body.projectKey   || process.env.JIRA_PROJECT_KEY;
  const userStoryKey   = req.body.userStoryKey;
  const gherkinContent = req.body.gherkinContent;

  if (!jiraBaseUrl || !jiraToken || !projectKey || !userStoryKey || !gherkinContent) {
    return res.status(400).json({
      error: 'Missing required fields: userStoryKey, gherkinContent',
    });
  }

  try {
    const rawScenarios = parseGherkin(gherkinContent);
    if (rawScenarios.length === 0) {
      return res.status(422).json({ error: 'No scenarios found in the provided Gherkin content.' });
    }

    // applica il filtro tag (legge tags.ignore)
    const scenarios = applyTagFilter(rawScenarios);

    const results = await createJiraTests({ jiraBaseUrl, jiraToken, projectKey, userStoryKey, scenarios });

    return res.status(201).json({
      message: `Successfully created ${results.length} test(s) in Jira.`,
      userStoryKey,
      tests: results,
    });
  } catch (err) {
    console.error(err);
    return res.status(500).json({ error: err.message });
  }
});

/**
 * POST /api/update-labels
 * Aggiorna le label dei Test Jira in base ai tag del feature file.
 * I tag presenti in tags.ignore vengono esclusi.
 */
app.post('/api/update-labels', async (req, res) => {
  const jiraBaseUrl    = req.body.jiraBaseUrl || process.env.JIRA_BASE_URL;
  const jiraToken      = req.body.jiraToken   || process.env.JIRA_TOKEN;
  const gherkinContent = req.body.gherkinContent;

  if (!jiraBaseUrl || !jiraToken || !gherkinContent) {
    return res.status(400).json({
      error: 'Missing required fields: gherkinContent',
    });
  }

  try {
    const rawScenarios = parseGherkin(gherkinContent);
    if (rawScenarios.length === 0) {
      return res.status(422).json({ error: 'No scenarios found in the provided Gherkin content.' });
    }

    // applica il filtro tag (legge tags.ignore)
    const scenarios = applyTagFilter(rawScenarios);

    const results = await updateJiraLabels({ jiraBaseUrl, jiraToken, scenarios });

    const updated = results.filter(r => !r.skipped && !r.error && r.changed).length;
    const skipped = results.filter(r => r.skipped).length;
    const errors  = results.filter(r => r.error).length;

    return res.status(200).json({
      message: `Elaborati ${results.length} scenari: ${updated} aggiornati, ${skipped} saltati, ${errors} errori.`,
      results,
    });
  } catch (err) {
    console.error(err);
    return res.status(500).json({ error: err.message });
  }
});

// Health check
app.get('/health', (_req, res) => res.json({ status: 'ok' }));

const PORT = process.env.PORT || 3000;
app.listen(PORT, () => console.log(`Gherkin→Jira API listening on port ${PORT}`));
