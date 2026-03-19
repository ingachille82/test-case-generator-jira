/**
 * Minimal Gherkin parser.
 * Supports: Feature, Background, Scenario, Scenario Outline, Given/When/Then/And/But, tags (@tag).
 * Returns an array of scenario objects ready to be turned into Jira Tests.
 */

const STEP_KEYWORDS = /^(Given|When|Then|And|But)\s+/i;
const SCENARIO_KEYWORDS = /^(Scenario|Scenario Outline|Example):/i;
const BACKGROUND_KEYWORD = /^Background:/i;
const FEATURE_KEYWORD = /^Feature:/i;
const TAG_KEYWORD = /^@/;

/**
 * @param {string} content - Raw .feature file text
 * @returns {Array<{title: string, tags: string[], steps: string[], rawText: string}>}
 */
function parseGherkin(content) {
  const lines = content.split('\n').map(l => l.trim()).filter(l => l.length > 0 && !l.startsWith('#'));

  const scenarios = [];
  let currentScenario = null;
  let currentTags = [];
  let featureTitle = '';

  for (let i = 0; i < lines.length; i++) {
    const line = lines[i];

    // Feature title
    if (FEATURE_KEYWORD.test(line)) {
      featureTitle = line.replace(FEATURE_KEYWORD, '').trim();
      continue;
    }

    // Tags accumulation
    if (TAG_KEYWORD.test(line)) {
      const tags = line.split(/\s+/).filter(t => t.startsWith('@'));
      currentTags.push(...tags);
      continue;
    }

    // Background – skip its steps but don't create a scenario
    if (BACKGROUND_KEYWORD.test(line)) {
      currentScenario = null; // steps will be absorbed and ignored
      continue;
    }

    // New scenario
    if (SCENARIO_KEYWORDS.test(line)) {
      // Save previous scenario
      if (currentScenario) scenarios.push(finalise(currentScenario));

      const title = line.replace(SCENARIO_KEYWORDS, '').trim();
      currentScenario = {
        title,
        tags: [...currentTags],
        steps: [],
        featureTitle,
      };
      currentTags = [];
      continue;
    }

    // Steps
    if (STEP_KEYWORDS.test(line) && currentScenario) {
      currentScenario.steps.push(line);
      continue;
    }

    // Examples table for Scenario Outline – keep as raw text
    if (/^Examples:/i.test(line) && currentScenario) {
      currentScenario.steps.push('Examples:');
      continue;
    }

    // Table rows (|...|) – attach to current scenario
    if (line.startsWith('|') && currentScenario) {
      currentScenario.steps.push(line);
    }
  }

  // Don't forget the last scenario
  if (currentScenario) scenarios.push(finalise(currentScenario));

  return scenarios;
}

function finalise(scenario) {
  const rawText = [
    `Scenario: ${scenario.title}`,
    ...scenario.steps,
  ].join('\n');

  return {
    title: scenario.title,
    tags: scenario.tags,
    featureTitle: scenario.featureTitle,
    steps: scenario.steps,
    rawText,
  };
}

module.exports = { parseGherkin };
