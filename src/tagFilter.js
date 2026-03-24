/**
 * tagFilter.js
 *
 * Legge il file tags.ignore dalla root del progetto e restituisce
 * una funzione per filtrare i tag da ignorare.
 *
 * Formato del file tags.ignore:
 *   - Una riga per tag (senza il simbolo @)
 *   - Le righe che iniziano con # sono commenti
 *   - Le righe vuote vengono ignorate
 */

const fs   = require('fs');
const path = require('path');

const IGNORE_FILE = path.resolve(process.cwd(), 'tags.ignore');

/**
 * Legge il file tags.ignore e restituisce un Set di tag da ignorare.
 * Se il file non esiste, restituisce un Set vuoto.
 */
function loadIgnoredTags() {
  if (!fs.existsSync(IGNORE_FILE)) {
    console.warn(`[tagFilter] File tags.ignore non trovato in ${IGNORE_FILE} — nessun tag verrà ignorato.`);
    return new Set();
  }

  const lines = fs.readFileSync(IGNORE_FILE, 'utf-8').split('\n');
  const tags = lines
    .map(l => l.trim())
    .filter(l => l.length > 0 && !l.startsWith('#'))
    .map(l => l.replace(/^@/, '')); // normalizza rimuovendo @ se presente

  console.log(`[tagFilter] Tag ignorati: ${tags.length > 0 ? tags.join(', ') : '(nessuno)'}`);
  return new Set(tags);
}

/**
 * Filtra i tag di uno scenario rimuovendo quelli nella blacklist.
 *
 * @param {string[]} tags        - Array di tag (es. ['@AC1', '@Automated_UI'])
 * @param {Set}      ignoredTags - Set di tag da ignorare (senza @)
 * @returns {string[]}           - Tag filtrati
 */
function filterTags(tags, ignoredTags) {
  return tags.filter(tag => {
    const clean = tag.replace(/^@/, '');
    return !ignoredTags.has(clean);
  });
}

/**
 * Applica il filtro a tutti gli scenari.
 * Modifica i tag in-place e aggiunge ignoredTags per il reporting.
 *
 * @param {Array}  scenarios
 * @returns {Array} scenari con tag filtrati
 */
function applyTagFilter(scenarios) {
  const ignoredTags = loadIgnoredTags();

  return scenarios.map(scenario => {
    const originalTags = scenario.tags;
    const filteredTags = filterTags(originalTags, ignoredTags);
    const removedTags  = originalTags.filter(t => !filteredTags.includes(t));

    if (removedTags.length > 0) {
      console.log(`[tagFilter] Scenario "${scenario.title}": rimossi tag ${removedTags.join(', ')}`);
    }

    return {
      ...scenario,
      tags: filteredTags,
      ignoredTags: removedTags,
    };
  });
}

module.exports = { applyTagFilter, loadIgnoredTags };
