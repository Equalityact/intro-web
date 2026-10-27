'use strict';

const { test } = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const { parseCsv, parseTimelineCsv, fetchSheetCsv, sheetCsvUrl } = require('../lib/timeline.cjs');
const { createHandler } = require('../api/timeline');
const { timeline } = require('../content/manuscript.json');
const template = fs.readFileSync(path.join(__dirname, '../content/timeline-sheet.csv'), 'utf8');
const source = 'https://docs.google.com/spreadsheets/d/e/example/pub?gid=0&single=true&output=csv';
const csv = (...rows) => rows.map(row => row.map(value => '"' + value.replaceAll('"', '""') + '"').join(',')).join('\r\n');
const head = ['시기', '제목', '본문', '공개'];

test('import template retains all 11 events and all 37 bracket-specific links verbatim', () => {
  const result = parseTimelineCsv(template, timeline);
  const expected = timeline.map(period => ({ ...period, items: period.items.map(item => ({
    title: item.title,
    ...(item.meta ? { meta: item.meta } : {}),
    paragraphs: item.paragraphs,
    paragraph_links: item.paragraph_links || item.paragraphs.map(() => []),
  })) }));
  assert.deepEqual(result, expected);
  const items = result.flatMap(period => period.items);
  assert.equal(items.length, 11);
  assert.equal(items.flatMap(item => item.paragraph_links.flat()).length, 37);
});

test('CSV accepts Korean, BOM, quoted commas/newlines, and escaped quotes', () => {
  assert.deepEqual(parseCsv('\uFEFF이름,본문\r\n"한,글","첫 줄\n""둘째"" 줄"\r\n'), [
    ['이름', '본문'], ['한,글', '첫 줄\n"둘째" 줄'],
  ]);
  assert.throws(() => parseCsv('"unclosed'));
  assert.throws(() => parseCsv('"closed"oops'));
});

test('new periods follow sheet row order and keep stable anchors after reordering', () => {
  const first = ['23대 국회', '새 사건', '새 본문', '예'];
  const second = ['24대 국회', '다음 사건', '다음 본문', '예'];
  const a = parseTimelineCsv(csv(head, first, second));
  const b = parseTimelineCsv(csv(head, second, first));
  assert.equal(a[0].title, '23대 국회');
  assert.equal(b[0].title, '24대 국회');
  assert.equal(a[0].id, b[1].id);
});

test('optional metadata supports sheet classifications while old four-column sheets still work', () => {
  const legacy = parseTimelineCsv(csv(head, ['22대 국회', timeline[5].items[0].title, '본문', '예']), timeline);
  assert.equal(legacy[0].years, '2024~');
  assert.equal(legacy[0].items[0].meta.kind, '입법');
  const updated = parseTimelineCsv(csv(['시기', '분류', '제목', '본문', '공개', '기간'], ['23대 국회', '권고', '국가인권위원회(2028) - 새 권고', '본문', '예', '2028~2032']));
  assert.equal(updated[0].years, '2028~2032');
  assert.deepEqual(updated[0].items[0].meta, { date: '2028', actor: '국가인권위원회', kind: '권고' });
  const hidden = parseTimelineCsv(csv(['시기', '분류', '제목', '본문', '공개'], ['22대 국회', '', timeline[5].items[0].title, '본문', '예']), timeline);
  assert.equal(hidden[0].items[0].meta.kind, undefined);
});

test('published rows support multiline paragraphs and exact HTTP/HTTPS links', () => {
  const result = parseTimelineCsv(csv(head, ['22대 국회', '사건', '앞 [｢](http://example.com/a)[법안](https://example.com/b)[｣](https://example.com/c) 뒤\n\n둘째 문단', 'TRUE']), timeline);
  assert.equal(result[0].id, 'p22');
  assert.deepEqual(result[0].items[0].paragraphs, ['앞 ｢법안｣ 뒤', '둘째 문단']);
  assert.deepEqual(result[0].items[0].paragraph_links[0].map(link => link.text), ['｢', '법안', '｣']);
  assert.equal(result[0].items[0].paragraph_links[0][0].url, 'http://example.com/a');
});

test('hidden rows stay off the site and blank 공개 means visible', () => {
  const result = parseTimelineCsv(csv(head,
    ['22대 국회', '', '[bad](javascript:alert(1))', 'FALSE'],
    ['22대 국회', '공개 사건', '본문', ''],
  ));
  assert.equal(result[0].items.length, 1);
  assert.equal(result[0].items[0].title, '공개 사건');
});

test('unused empty spreadsheet columns do not prevent publication', () => {
  const result = parseTimelineCsv(csv([...head, '', ''], ['22대 국회', '새 사건', '', '예', '', '']));
  assert.equal(result[0].items[0].title, '새 사건');
  assert.deepEqual(result[0].items[0].paragraphs, []);
});

test('malformed, empty, or unsafe source is rejected rather than partially published', () => {
  for (const data of [
    'not,a,timeline', csv(head), csv(head, ['국회', '', '본문', '예']),
    csv(head, ['국회', '제목', '본문', '오타']), csv(head, ['국회', '제목', '[bad](javascript:alert(1))', '예']),
    csv(['시기', '제목', '본문', '본문'], ['국회', '제목', '본문', '본문']),
    csv(head, ['국회', '제목', '[bad](https://user:password@example.com)', '예']),
    '시기,제목,본문,공개\n국회,제목,본문',
  ]) assert.throws(() => parseTimelineCsv(data));
});

test('only published/exported Google Sheets CSV URLs are accepted', () => {
  assert.equal(sheetCsvUrl(source).hostname, 'docs.google.com');
  assert.equal(sheetCsvUrl('https://docs.google.com/spreadsheets/d/example/export?format=csv').hostname, 'docs.google.com');
  for (const url of ['http://docs.google.com/spreadsheets/d/e/example/pub?output=csv', 'https://example.com/data.csv', 'https://docs.google.com/spreadsheets/d/example/edit', 'https://docs.google.com/url?url=http://127.0.0.1', 'https://user@docs.google.com/spreadsheets/d/e/example/pub?output=csv']) {
    assert.throws(() => sheetCsvUrl(url));
  }
});

test('CSV fetch follows Google download redirects but refuses external redirects', async () => {
  let calls = 0;
  assert.equal(await fetchSheetCsv(source, async (url, options) => {
    assert.equal(options.redirect, 'manual');
    assert(options.signal);
    return ++calls === 1
      ? new Response(null, { status: 302, headers: { location: 'https://doc-example-sheets.googleusercontent.com/pub/data.csv' } })
      : new Response('시기,제목,본문\n국회,제목,본문', { headers: { 'Content-Type': 'text/csv' } });
  }), '시기,제목,본문\n국회,제목,본문');
  await assert.rejects(fetchSheetCsv(source, async () => new Response(null, { status: 302, headers: { location: 'http://127.0.0.1/private' } })));
  await assert.rejects(fetchSheetCsv(source, async () => new Response(null, { status: 302, headers: { location: source } })));
});

test('login pages, failed downloads, and excessive responses are rejected', async () => {
  await assert.rejects(fetchSheetCsv(source, async () => new Response('<html>Sign in</html>', { headers: { 'Content-Type': 'text/html' } })));
  await assert.rejects(fetchSheetCsv(source, async () => new Response('error', { status: 403 })));
  await assert.rejects(fetchSheetCsv(source, async () => new Response('too big', { headers: { 'Content-Length': String(2 ** 21) } })));
  await assert.rejects(fetchSheetCsv(source, async () => new Response('x'.repeat(2 ** 20 + 1))));
});

async function response(handler, method = 'GET') {
  const result = { headers: {}, setHeader(name, value) { this.headers[name] = value; }, end(value) { this.body = value; } };
  await handler({ method }, result);
  return result;
}

test('unconfigured API preserves fallback with an uncacheable unavailable response', async () => {
  const res = await response(createHandler({ source: () => '' }));
  assert.equal(res.statusCode, 503);
  assert.equal(res.headers['Cache-Control'], 'no-store');
  assert.equal(JSON.parse(res.body).error, 'TIMELINE_NOT_CONFIGURED');
});

test('API returns validated data with cache headers, supports HEAD, and rejects writes', async () => {
  const handler = createHandler({ source: () => source, fetchCsv: async () => template });
  const res = await response(handler);
  assert.equal(res.statusCode, 200);
  assert.match(res.headers['Cache-Control'], /s-maxage=60/);
  assert.equal(JSON.parse(res.body).periods.length, 6);
  assert.equal(JSON.parse(res.body).version, 1);
  const head = await response(handler, 'HEAD');
  assert.equal(head.statusCode, 200);
  assert.equal(head.body, undefined);
  assert.equal((await response(handler, 'POST')).statusCode, 405);
});

test('API does not replace a valid timeline with malformed data or leak source errors', async () => {
  for (const fetchCsv of [async () => 'invalid CSV', async () => { throw new Error('private source detail'); }]) {
    const res = await response(createHandler({ source: () => source, fetchCsv }));
    assert.equal(res.statusCode, 503);
    assert.equal(res.headers['Cache-Control'], 'no-store');
    assert.equal(JSON.parse(res.body).error, 'TIMELINE_UNAVAILABLE');
    assert(!res.body.includes('private'));
  }
});
