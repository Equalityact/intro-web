(() => {
  'use strict';

  const container = document.querySelector('[data-timeline]');
  const toc = document.querySelector('[data-timeline-toc]');
  if (!container || !toc) return;
  let inFlight = false;
  let previous = '';

  function element(tag, className, text) {
    const node = document.createElement(tag);
    if (className) node.className = className;
    if (text !== undefined) node.textContent = text;
    return node;
  }

  function paragraph(text, links) {
    if (typeof text !== 'string' || !Array.isArray(links)) throw new Error('Invalid paragraph');
    const node = element('p');
    let cursor = 0;
    links.forEach(link => {
      if (!Number.isInteger(link.start) || !Number.isInteger(link.end) || link.start < cursor || link.end <= link.start || link.end > text.length || text.slice(link.start, link.end) !== link.text) {
        throw new Error('Invalid link range');
      }
      const url = new URL(link.url);
      if (!/^https?:\/\//i.test(link.url) || !['http:', 'https:'].includes(url.protocol) || url.username || url.password) throw new Error('Invalid link');
      node.append(document.createTextNode(text.slice(cursor, link.start)));
      const anchor = element('a', '', link.text);
      anchor.href = link.url;
      anchor.target = '_blank';
      anchor.rel = 'noopener noreferrer';
      anchor.setAttribute('data-manuscript-link', '');
      node.append(anchor);
      cursor = link.end;
    });
    node.append(document.createTextNode(text.slice(cursor)));
    return node;
  }

  function build(periods) {
    if (!Array.isArray(periods) || !periods.length || periods.length > 100) throw new Error('Invalid periods');
    const fragment = document.createDocumentFragment();
    const navigation = document.createDocumentFragment();
    const ids = new Set();
    let count = 0;
    periods.forEach((period, index) => {
      if (!/^[a-z][a-z0-9-]*$/.test(period.id) || ids.has(period.id) || typeof period.title !== 'string' || !period.title.trim() || !Array.isArray(period.items) || !period.items.length) throw new Error('Invalid period');
      ids.add(period.id);
      const section = element('section', 'period');
      section.id = period.id;
      section.setAttribute('aria-labelledby', `${period.id}-title`);
      const head = element('div', 'period-head');
      const heading = element('h2', '', period.title);
      heading.id = `${period.id}-title`;
      const number = element('span', 'period-number', String(index + 1).padStart(2, '0'));
      number.setAttribute('aria-hidden', 'true');
      head.append(number, heading);
      if (period.years) {
        if (typeof period.years !== 'string') throw new Error('Invalid period dates');
        head.append(element('span', 'years', period.years));
      }
      const list = element('ol', 'timeline');
      period.items.forEach(item => {
        if (++count > 1000 || typeof item.title !== 'string' || !item.title.trim() || !Array.isArray(item.paragraphs) || !Array.isArray(item.paragraph_links) || item.paragraph_links.length !== item.paragraphs.length) throw new Error('Invalid event');
        const row = element('li', 'timeline-item');
        if (['pink', 'yellow', 'purple'].includes(item.color)) row.classList.add(`timeline-color-${item.color}`);
        const card = element('article', 'timeline-card');
        const meta = item.meta || {};
        const metadata = element('div', 'timeline-meta');
        ['date', 'actor', 'kind'].forEach(key => {
          if (!meta[key]) return;
          if (typeof meta[key] !== 'string') throw new Error('Invalid event metadata');
          metadata.append(element('span', `timeline-${key}`, meta[key]));
        });
        const prefix = meta.actor && meta.date ? `${meta.actor}(${meta.date}) - ` : '';
        const title = prefix && item.title.startsWith(prefix) ? item.title.slice(prefix.length) : item.title;
        card.append(metadata, element('h3', '', title));
        item.paragraphs.forEach((text, index) => card.append(paragraph(text, item.paragraph_links[index])));
        row.append(card);
        list.append(row);
      });
      section.append(head, list);
      fragment.append(section);
      const navItem = element('li');
      const anchor = element('a', '', period.title);
      anchor.href = `#${period.id}`;
      navItem.append(anchor);
      navigation.append(navItem);
    });
    return { fragment, navigation };
  }

  async function refresh() {
    if (document.hidden || inFlight) return;
    if ((container.contains(document.activeElement) || toc.contains(document.activeElement)) && document.activeElement.matches(':focus-visible')) return;
    inFlight = true;
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), 10000);
    try {
      const response = await fetch('/api/timeline', { signal: controller.signal });
      if (!response.ok) return;
      const data = await response.json();
      if (data.version !== 1) return;
      const fingerprint = JSON.stringify(data.periods);
      if (fingerprint === previous) return;
      const { fragment, navigation } = build(data.periods);
      let hash;
      try { hash = decodeURIComponent(location.hash.slice(1)); } catch { hash = ''; }
      const hadHashTarget = hash && document.getElementById(hash);
      const headerBottom = document.querySelector('.site-header').getBoundingClientRect().bottom;
      const readingCard = [...container.querySelectorAll('.timeline-card')].find(card => {
        const bounds = card.getBoundingClientRect();
        return bounds.bottom > headerBottom && bounds.top < window.innerHeight;
      });
      const position = readingCard && {
        period: readingCard.closest('.period').id,
        title: readingCard.querySelector('h3').textContent,
        top: readingCard.getBoundingClientRect().top,
      };
      container.replaceChildren(fragment);
      toc.replaceChildren(navigation);
      previous = fingerprint;
      if (hash && !hadHashTarget && document.getElementById(hash)) {
        document.getElementById(hash).scrollIntoView();
      } else if (position) {
        const period = document.getElementById(position.period);
        const card = period && [...period.querySelectorAll('.timeline-card')].find(item => item.querySelector('h3').textContent === position.title);
        if (card) {
          const offset = card.getBoundingClientRect().top - position.top;
          const previousBehavior = document.documentElement.style.scrollBehavior;
          document.documentElement.style.scrollBehavior = 'auto';
          window.scrollBy(0, offset);
          document.documentElement.style.scrollBehavior = previousBehavior;
        }
      }
    } catch {
      // Keep the approved HTML or the last successfully loaded timeline.
    } finally {
      clearTimeout(timeout);
      inFlight = false;
    }
  }

  refresh();
  setInterval(refresh, 60 * 1000);
  document.addEventListener('visibilitychange', () => { if (!document.hidden) refresh(); });
})();
