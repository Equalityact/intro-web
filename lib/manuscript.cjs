'use strict';
const { parseDocument, DomUtils } = require('htmlparser2');
const { createHash } = require('node:crypto');
const MAX_BYTES = 2 * 1024 * 1024;
const hash = text => createHash('sha256').update(text).digest('hex').slice(0, 12);
const normal = text => text.replace(/\s+/g, '').replace(/[!！]/g, '');
function safeUrl(value) {
  let url = new URL(value);
  if (url.hostname === 'www.google.com' && url.pathname === '/url') url = new URL(url.searchParams.get('q') || url.searchParams.get('url') || '');
  if (url.username || url.password || !['https:', 'http:', 'mailto:'].includes(url.protocol)) throw new Error('Unsafe manuscript link');
  if (url.protocol === 'mailto:' && !/^[^\s@]+@[^\s@]+$/.test(url.pathname)) throw new Error('Invalid email link');
  return url.href;
}
function inline(node) {
  let text = ''; const links = [];
  function walk(child) {
    if (child.type === 'text') { text += child.data.replace(/\u00a0/g, ' '); return; }
    if (['script', 'style', 'iframe', 'object', 'ul', 'ol'].includes(child.name)) return;
    if (child.name === 'br') { text += '\n'; return; }
    const start = text.length;
    for (const item of child.children || []) walk(item);
    if (child.name === 'a' && child.attribs?.href && text.slice(start).trim()) {
      const raw = child.attribs.href;
      if (!raw.startsWith('#')) links.push({ start, end: text.length, text: text.slice(start), url: safeUrl(raw) });
    }
  }
  walk(node);
  const leading = text.length - text.trimStart().length; text = text.trim();
  return { text, links: links.map(link => {
    const start = Math.max(0, link.start - leading), end = Math.min(text.length, link.end - leading);
    return { start, end, text: text.slice(start, end), url: link.url };
  }).filter(link => link.end > link.start).sort((a, b) => a.start - b.start) };
}
function sectionKey(title) {
  const numbered = title.match(/^\s*([0-6])[.．]\s*/);
  if (numbered) return ['home', 'about', 'scenes', 'why', 'qna', 'timeline', 'resources'][Number(numbered[1])];
  if (/^(메인페이지|메인 페이지)$/.test(title.trim())) return 'home';
  if (/^더 보기/.test(title.trim())) return 'resources';
  if (title.trim() === '정보') return 'info';
  return null;
}
function cleanTitle(title) {
  return title.replace(/^\s*[0-6][.．]\s*/, '').replace(/\s*\((?:사진 추가|각 자료 썸네일 추가)[^)]*\)/g, '').replace(/\s*👈.*$/, '').trim();
}
function parseManuscriptHtml(html, known = {}) {
  if (typeof html !== 'string' || Buffer.byteLength(html) > MAX_BYTES) throw new Error('Invalid manuscript size');
  const dom = parseDocument(html, { decodeEntities: true });
  const body = DomUtils.findOne(node => node.name === 'body', dom.children, true);
  if (!body) throw new Error('Missing document body');
  const records = [];
  const listGroups = new WeakMap(); let nextListGroup = 0;
  function visit(node) {
    if (['script', 'style', 'nav'].includes(node.name)) return;
    if (['h1', 'h2', 'h3', 'p', 'li'].includes(node.name)) {
      const value = inline(node);
      let list;
      if (node.name === 'li') {
        const parent = node.parent;
        if (parent && ['ul', 'ol'].includes(parent.name)) {
          if (!listGroups.has(parent)) listGroups.set(parent, `list-${nextListGroup++}`);
          let depth = 0;
          for (let ancestor = parent.parent; ancestor; ancestor = ancestor.parent) if (['ul', 'ol'].includes(ancestor.name)) depth++;
          const start = Math.max(1, Math.min(10000, Number(parent.attribs?.start) || 1));
          list = { kind: parent.name, depth, group: listGroups.get(parent), start };
        }
      }
      if (value.text) records.push({ level: /^h[123]$/.test(node.name) ? Number(node.name[1]) : 0, ...value, ...(list ? {list} : {}) });
      if (node.name === 'li') for (const nested of node.children || []) if (['ul', 'ol'].includes(nested.name)) visit(nested);
    } else for (const child of node.children || []) visit(child);
  }
  visit(body);
  if (records.length > 4000) throw new Error('Too many document paragraphs');
  const pages = {}; let section, block, child;
  for (const record of records) {
    if (record.level === 1) {
      const key = sectionKey(record.text);
      if (!key || pages[key]) throw new Error('Unknown or duplicate page heading');
      section = pages[key] = { title: cleanTitle(record.text), intro: [], blocks: [] }; block = child = null;
    } else if (!section) throw new Error('Text outside page headings');
    else if (record.level === 2) {
      block = { title: cleanTitle(record.text).replace(/^\[|\]$/g, '').trim(), paragraphs: [], children: [] };
      section.blocks.push(block); child = null;
    } else if (record.level === 3) {
      if (!block) throw new Error('Subheading outside section');
      child = { title: record.text, paragraphs: [] }; block.children.push(child);
    } else {
      if (/^\[(?:편집메모|사진|썸네일)/.test(record.text)) continue;
      (child ? child.paragraphs : block ? block.paragraphs : section.intro).push({ text: record.text, links: record.links, ...(record.list ? { list: record.list } : {}) });
    }
  }
  for (const key of ['about', 'scenes', 'why', 'qna', 'timeline', 'resources', 'info']) {
    if (!pages[key]) throw new Error(`Missing ${key} page`);
    if (key !== 'info' && !pages[key].blocks.length) throw new Error(`Empty ${key} page`);
  }
  for (const key of ['about', 'scenes', 'why']) {
    const originals = known[key] || [];
    pages[key].blocks.forEach(item => {
      const original = originals.find(entry => normal(entry.title) === normal(item.title));
      item.id = original?.id || `${key}-${hash(item.title)}`;
      if (key === 'why' && original?.label) item.label = original.label;
      if (key === 'why' && original?.callout) item.callout = original.callout;
      if (key === 'scenes') item.children.forEach(caseItem => {
        const at = original?.items.indexOf(caseItem.title) ?? -1;
        if (at >= 0) caseItem.before = original.before[at];
      });
    });
  }
  const questions = pages.qna.blocks.map(item => {
    if (!item.paragraphs.length || item.children.length) throw new Error('Every question needs an answer');
    const at = (known.questions || []).findIndex(q => q.question === item.title);
    return { id: at >= 0 ? `q${at + 1}` : `q-${hash(item.title)}`, question: item.title, paragraphs: item.paragraphs };
  });
  if (questions.length > 500 || new Set(questions.map(q => q.id)).size !== questions.length) throw new Error('Duplicate or excessive questions');
  const periods = pages.timeline.blocks.map(period => {
    const original = (known.timeline || []).find(p => normal(p.title) === normal(period.title));
    const years = period.paragraphs.find(p => /^\[기간:/.test(p.text))?.text.match(/^\[기간:\s*([^\]]+)\]$/)?.[1] || original?.years;
    if (!period.children.length) throw new Error('Empty timeline period');
    return { id: original?.id || `p-${hash(period.title)}`, title: period.title, ...(years ? { years } : {}), items: period.children.map(item => {
      const originalItem = original?.items.find(event => event.title === item.title);
      const paragraphs = item.paragraphs.filter(p => !/^\[(색상|분류|연도|주체):/.test(p.text));
      const metadata = { ...(originalItem?.meta || {}) };
      const date = item.title.match(/^(.*?)\((\d{4}[^)]*)\) - /);
      if (date) { metadata.actor = date[1]; metadata.date = date[2]; }
      const colors = new Map([['핑크','pink'], ['옐로','yellow'], ['퍼플','purple']]);
      let color;
      for (const p of item.paragraphs) {
        const match = p.text.match(/^\[(색상|분류|연도|주체):\s*([^\]]*)\]$/);
        if (!match) continue;
        if (match[1] === '색상') color = colors.get(match[2].trim());
        else metadata[{분류:'kind',연도:'date',주체:'actor'}[match[1]]] = match[2].trim();
      }
      return { title: item.title, meta: metadata, ...(color ? { color } : {}), paragraphs: paragraphs.map(p=>p.text), paragraph_links: paragraphs.map(p=>p.links), paragraph_lists: paragraphs.map(p=>p.list || null) };
    }) };
  });
  const resources = pages.resources.blocks.map(item => {
    const by = item.paragraphs.find(p => /^_\s*/.test(p.text));
    const button = item.paragraphs.find(p => /^(링크|자료 보기)$/.test(p.text));
    if (!button?.links.length) throw new Error('Resource needs a linked button');
    return { title: item.title, by: by?.text.replace(/^_\s*/, '') || '', paragraphs: item.paragraphs.filter(p=>p!==by && p!==button), url: button.links[0].url };
  });
  if (pages.home) {
    const surveys = pages.home.blocks.find(block => block.title === '여론조사');
    if (surveys) for (const item of surveys.children) {
      const values = ['찬성한다', '잘 모르겠다', '반대한다'].map(label => {
        const p = item.paragraphs.find(p => p.text.startsWith(label + ' '));
        const value = Number(p?.text.match(/(\d+(?:\.\d+)?)%/)?.[1]);
        if (!Number.isFinite(value) || value < 0 || value > 100) throw new Error('Invalid survey value');
        return value;
      });
      if (values.reduce((a, b) => a + b, 0) > 100.5) throw new Error('Invalid survey total');
    }
  }
  const info = pages.info.intro.map(p => {
    const split = p.text.indexOf(':');
    if (split < 0) throw new Error('Info rows need a label and colon');
    return { label: p.text.slice(0,split).trim(), paragraph: { text: p.text.slice(split+1).trim(), links: p.links.map(link=>{const offset=split+1+(p.text.slice(split+1).length-p.text.slice(split+1).trimStart().length);return {...link,start:link.start-offset,end:link.end-offset};}) } };
  });
  return { version: 1, pages, questions, periods, resources, info };
}
function documentUrl(value) {
  const url = new URL(value);
  if (url.protocol !== 'https:' || url.hostname !== 'docs.google.com' || url.port || url.username || url.password || !/^\/document\/d\/[\w-]+\/export$/.test(url.pathname) || url.searchParams.get('format') !== 'html') throw new Error('Use a Google Docs HTML export URL');
  return url;
}
async function fetchDocumentHtml(source, fetchImpl = fetch) {
  let url = documentUrl(source); const signal = AbortSignal.timeout(10000);
  for(let i=0;i<4;i++) {
    const response = await fetchImpl(url.href,{redirect:'manual',signal,headers:{Accept:'text/html'}});
    if([301,302,303,307,308].includes(response.status)) {
      await response.body?.cancel();
      const next = new URL(response.headers.get('location') || '',url);
      if(!response.headers.get('location') || next.protocol!=='https:' || next.port || next.username || next.password || !(next.hostname==='docs.google.com' || next.hostname.endsWith('.googleusercontent.com'))) throw new Error('Untrusted document redirect');
      url=next; continue;
    }
    if(!response.ok || !/text\/html/i.test(response.headers.get('content-type') || '') || Number(response.headers.get('content-length'))>MAX_BYTES) { await response.body?.cancel(); throw new Error('Document is not readable'); }
    const parts=[];let bytes=0;
    try { for await(const part of response.body) { bytes+=part.byteLength;if(bytes>MAX_BYTES)throw new Error('Document is too large');parts.push(Buffer.from(part));} }
    catch(error) { await response.body?.cancel().catch(()=>{});throw error; }
    return Buffer.concat(parts).toString('utf8');
  }
  throw new Error('Too many redirects');
}
module.exports={parseManuscriptHtml,fetchDocumentHtml,documentUrl,safeUrl};
