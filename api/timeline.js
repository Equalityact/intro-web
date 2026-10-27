'use strict';

const { parseTimelineCsv, fetchSheetCsv } = require('../lib/timeline.cjs');
const { timeline } = require('../content/manuscript.json');
const configuredSource = require('../content/timeline-source.json');

function createHandler({ source = () => process.env.TIMELINE_SHEET_CSV_URL || configuredSource.csvUrl, fetchCsv = fetchSheetCsv } = {}) {
  return async function timelineHandler(req, res) {
    res.setHeader('Content-Type', 'application/json; charset=utf-8');
    res.setHeader('X-Content-Type-Options', 'nosniff');
    res.setHeader('Cache-Control', 'no-store');
    function send(status, data) {
      res.statusCode = status;
      res.end(req.method === 'HEAD' ? undefined : JSON.stringify(data));
    }
    if (!['GET', 'HEAD'].includes(req.method)) {
      res.setHeader('Allow', 'GET, HEAD');
      return send(405, { error: 'METHOD_NOT_ALLOWED' });
    }
    if (!source()) return send(503, { error: 'TIMELINE_NOT_CONFIGURED' });
    try {
      const periods = parseTimelineCsv(await fetchCsv(source()), timeline);
      res.setHeader('Cache-Control', 'public, max-age=0, s-maxage=60, stale-while-revalidate=300');
      send(200, { version: 1, periods });
    } catch {
      send(503, { error: 'TIMELINE_UNAVAILABLE' });
    }
  };
}

module.exports = createHandler();
module.exports.createHandler = createHandler;
