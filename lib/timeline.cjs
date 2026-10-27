'use strict';

const { createHash } = require('node:crypto');
const MAX_BYTES = 1024 * 1024;

function parseCsv(input) {
  const text = input.replace(/^\uFEFF/, '').replace(/\r\n?/g, '\n');
  const rows = [];
  let row = [], field = '', quoted = false, closed = false;
  function finishField() { row.push(field); field = ''; closed = false; }
  function finishRow() { finishField(); rows.push(row); row = []; }
  for (let i = 0; i < text.length; i++) {
    const char = text[i];
    if (quoted) {
      if (char !== '"') field += char;
      else if (text[i + 1] === '"') { field += '"'; i++; }
      else { quoted = false; closed = true; }
    } else if (char === ',') finishField();
    else if (char === '\n') finishRow();
    else if (closed) throw new Error('Unexpected text after quoted CSV field');
    else if (char === '"') {
      if (field) throw new Error('Unexpected quote in CSV field');
      quoted = true;
    } else field += char;
  }
  if (quoted) throw new Error('Unclosed CSV field');
  if (field || row.length || closed) finishRow();
  return rows;
}

function safeLink(value) {
  if (!/^https?:\/\//i.test(value)) throw new Error('Links must use HTTP or HTTPS');
  const url = new URL(value);
  if (url.username || url.password) throw new Error('Link credentials are not supported');
  return value;
}

function parseParagraph(value) {
  const links = [];
  const pattern = /\[([^\]\n]+)\]\(([^)\s]+)\)/g;
  let text = '', cursor = 0;
  for (const match of value.matchAll(pattern)) {
    text += value.slice(cursor, match.index);
    const start = text.length;
    text += match[1];
    links.push({ start, end: text.length, text: match[1], url: safeLink(match[2]) });
    cursor = match.index + match[0].length;
  }
  text += value.slice(cursor);
  return { text, links };
}

function parseTimelineCsv(csv, knownPeriods = []) {
  if (typeof csv !== 'string' || Buffer.byteLength(csv) > MAX_BYTES) throw new Error('CSV is too large');
  const [head, ...rows] = parseCsv(csv);
  if (!head || rows.length > 1000) throw new Error('Invalid timeline row count');
  const headers = head.map(value => value.trim());
  const namedHeaders = headers.filter(Boolean);
  if (new Set(namedHeaders).size !== namedHeaders.length) throw new Error('Duplicate column headings');
  const columns = ['시기', '제목', '본문'].map(name => headers.indexOf(name));
  if (columns.includes(-1)) throw new Error('Required columns: 시기, 제목, 본문');
  const visibilityColumn = headers.indexOf('공개');
  const knownIds = new Map(knownPeriods.map(period => [period.title, period.id]));
  const known = new Map(knownPeriods.map(period => [period.title, period]));
  function optional(row, column, fallback) {
    const index = headers.indexOf(column);
    const value = index < 0 ? fallback : row[index].trim();
    if (value && value.length > 200) throw new Error('Timeline metadata is too long');
    return value;
  }
  const periods = new Map();
  for (const row of rows) {
    if (row.every(value => !value.trim())) continue;
    if (row.length !== headers.length) throw new Error('CSV row has a different number of columns');
    const visibility = visibilityColumn < 0 ? '' : row[visibilityColumn].trim().toLowerCase();
    if (['false', '아니오', '숨김', '0'].includes(visibility)) continue;
    if (!['', 'true', '예', '공개', '1'].includes(visibility)) throw new Error('Invalid 공개 value');
    const [periodTitle, title, body] = columns.map(index => row[index].trim());
    if (!periodTitle || !title || periodTitle.length > 200 || title.length > 500 || body.length > 100000) {
      throw new Error('Visible rows need a period and title');
    }
    if (!periods.has(periodTitle)) {
      const id = knownIds.get(periodTitle) || 'p-' + createHash('sha256').update(periodTitle).digest('hex').slice(0, 12);
      const years = optional(row, '기간') || known.get(periodTitle)?.years;
      periods.set(periodTitle, { id, title: periodTitle, ...(years ? { years } : {}), items: [] });
    }
    const suppliedYears = optional(row, '기간');
    if (suppliedYears && periods.get(periodTitle).years !== suppliedYears) throw new Error('Conflicting period dates');
    const existing = known.get(periodTitle)?.items.find(item => item.title === title)?.meta || {};
    const prefix = title.match(/^(.*?)\((\d{4}[^)]*)\) - /);
    const meta = {};
    for (const [key, column, fallback] of [
      ['date', '연도', existing.date || prefix?.[2]],
      ['actor', '주체', existing.actor || prefix?.[1]],
      ['kind', '분류', existing.kind],
    ]) {
      const value = optional(row, column, fallback);
      if (value) meta[key] = value;
    }
    const paragraphs = body.split(/\n\s*\n/).filter(value => value.trim()).map(parseParagraph);
    periods.get(periodTitle).items.push({
      title,
      ...(Object.keys(meta).length ? { meta } : {}),
      paragraphs: paragraphs.map(paragraph => paragraph.text),
      paragraph_links: paragraphs.map(paragraph => paragraph.links),
    });
  }
  if (!periods.size || periods.size > 100) throw new Error('Timeline needs 1–100 visible periods');
  return [...periods.values()];
}

function sheetCsvUrl(value) {
  const url = new URL(value);
  const published = /^\/spreadsheets\/d\/e\/[\w-]+\/pub$/.test(url.pathname) && url.searchParams.get('output') === 'csv';
  const exported = /^\/spreadsheets\/d\/[\w-]+\/export$/.test(url.pathname) && url.searchParams.get('format') === 'csv';
  if (url.protocol !== 'https:' || url.hostname !== 'docs.google.com' || url.port || url.username || url.password || (!published && !exported)) {
    throw new Error('Use a Google Sheets published CSV URL');
  }
  return url;
}

async function fetchSheetCsv(source, fetchImpl = fetch) {
  let url = sheetCsvUrl(source);
  const signal = AbortSignal.timeout(8000);
  for (let redirects = 0; redirects <= 3; redirects++) {
    const response = await fetchImpl(url.href, { redirect: 'manual', signal, headers: { Accept: 'text/csv' } });
    if ([301, 302, 303, 307, 308].includes(response.status)) {
      await response.body?.cancel();
      const location = response.headers.get('location');
      if (!location) throw new Error('Missing CSV redirect location');
      const next = new URL(location, url);
      if (next.protocol !== 'https:' || next.port || next.username || next.password || !(next.hostname === 'docs.google.com' || next.hostname.endsWith('.googleusercontent.com'))) {
        throw new Error('Untrusted CSV redirect');
      }
      url = next;
      continue;
    }
    if (!response.ok || /text\/html/i.test(response.headers.get('content-type') || '')) {
      await response.body?.cancel();
      throw new Error('Sheet is not publicly readable as CSV');
    }
    if (Number(response.headers.get('content-length')) > MAX_BYTES) {
      await response.body?.cancel();
      throw new Error('CSV is too large');
    }
    const parts = [];
    let size = 0;
    for await (const part of response.body) {
      size += part.byteLength;
      if (size > MAX_BYTES) throw new Error('CSV is too large');
      parts.push(Buffer.from(part));
    }
    return Buffer.concat(parts).toString('utf8');
  }
  throw new Error('Too many CSV redirects');
}

module.exports = { parseCsv, parseTimelineCsv, fetchSheetCsv, sheetCsvUrl };
