(() => {
  'use strict';

  const $ = (selector, root = document) => root.querySelector(selector);
  const $$ = (selector, root = document) => Array.from(root.querySelectorAll(selector));
  document.documentElement.classList.add('js');

  const toast = $('#toast');
  let toastTimer;
  function announce(message) {
    toast.textContent = message;
    toast.classList.add('show');
    clearTimeout(toastTimer);
    toastTimer = setTimeout(() => toast.classList.remove('show'), 2600);
  }

  // Disclosure navigation: normal document order, Escape, and responsive state.
  const menuButton = $('.menu-toggle');
  const navigation = $('#gnb');
  const compact = matchMedia('(max-width: 1099px)');
  function setMenu(open, returnFocus = false) {
    navigation.hidden = compact.matches && !open;
    menuButton.setAttribute('aria-expanded', String(compact.matches && open));
    menuButton.textContent = open && compact.matches ? '메뉴 닫기' : '메뉴 열기';
    if (returnFocus) menuButton.focus();
  }
  menuButton.addEventListener('click', () => setMenu(navigation.hidden));
  compact.addEventListener('change', () => setMenu(false));
  document.addEventListener('keydown', event => {
    if (event.key === 'Escape' && menuButton.getAttribute('aria-expanded') === 'true') {
      setMenu(false, true);
    }
  });
  document.addEventListener('click', event => {
    if (!navigation.contains(event.target) && !menuButton.contains(event.target)) setMenu(false);
  });
  document.addEventListener('focusin', event => {
    if (!navigation.contains(event.target) && !menuButton.contains(event.target)) setMenu(false);
  });
  $$('a', navigation).forEach(link => link.addEventListener('click', () => setMenu(false)));
  setMenu(false);

  const sceneSelector = $('.scene-selector');
  if (sceneSelector) {
    const tabs = $$('[role="tab"]', sceneSelector);
    const panels = tabs.map(tab => document.getElementById(tab.getAttribute('aria-controls')));
    function selectScene(index, scroll = false) {
      tabs.forEach((tab, current) => {
        const selected = current === index;
        tab.setAttribute('aria-selected', String(selected));
        tab.tabIndex = selected ? 0 : -1;
        panels[current].hidden = !selected;
      });
      if (scroll) panels[index].scrollIntoView({ block: 'start' });
    }
    function sceneFromHash(scroll = false) {
      const index = panels.findIndex(panel => `#${panel.id}` === location.hash);
      if (index !== -1) {
        selectScene(index);
        if (scroll) requestAnimationFrame(() => panels[index].scrollIntoView({ block: 'start' }));
      }
      return index;
    }
    sceneSelector.hidden = false;
    panels.forEach((panel, index) => {
      panel.setAttribute('role', 'tabpanel');
      panel.setAttribute('aria-labelledby', tabs[index].id);
      panel.tabIndex = 0;
    });
    tabs.forEach((tab, index) => {
      tab.addEventListener('click', () => {
        selectScene(index, true);
        history.replaceState(null, '', `#${panels[index].id}`);
      });
      tab.addEventListener('keydown', event => {
        let next;
        if (event.key === 'ArrowRight') next = (index + 1) % tabs.length;
        if (event.key === 'ArrowLeft') next = (index - 1 + tabs.length) % tabs.length;
        if (event.key === 'Home') next = 0;
        if (event.key === 'End') next = tabs.length - 1;
        if (next === undefined) return;
        event.preventDefault();
        tabs[next].focus();
        tabs[next].click();
      });
    });
    if (sceneFromHash(true) === -1) selectScene(0);
    window.addEventListener('hashchange', () => sceneFromHash(true));
  }

  const sectionJump = $('.section-jump');
  if (sectionJump) {
    const sectionButton = $('.section-jump-toggle', sectionJump);
    const sectionList = $('#home-section-links');
    const sectionLinks = $$('a', sectionList);
    const sections = sectionLinks.map(link => document.getElementById(link.hash.slice(1)).closest('section'));
    const compactJump = matchMedia('(max-width: 1439px)');
    function setSectionMenu(open, returnFocus = false) {
      sectionList.hidden = !open;
      sectionButton.setAttribute('aria-expanded', String(open));
      if (returnFocus) sectionButton.focus();
    }
    sectionButton.hidden = false;
    sectionButton.addEventListener('click', () => setSectionMenu(sectionList.hidden));
    compactJump.addEventListener('change', () => setSectionMenu(!compactJump.matches));
    sectionLinks.forEach(link => link.addEventListener('click', () => {
      if (compactJump.matches) setSectionMenu(false, true);
    }));
    document.addEventListener('keydown', event => {
      if (event.key === 'Escape' && !sectionList.hidden) setSectionMenu(false, sectionJump.contains(document.activeElement));
    });
    document.addEventListener('click', event => {
      if (compactJump.matches && !sectionJump.contains(event.target)) setSectionMenu(false);
    });
    setSectionMenu(!compactJump.matches);

    // Follow section boundaries, including long sections and expanded answers.
    let scrollPending = false;
    function updateSection() {
      const threshold = document.querySelector('.site-header').getBoundingClientRect().bottom + 32;
      let active = -1;
      sections.forEach((section, index) => {
        const bounds = section.getBoundingClientRect();
        if (bounds.top <= threshold && bounds.bottom > threshold) active = index;
      });
      if (window.scrollY + window.innerHeight >= document.documentElement.scrollHeight - 2 && sections.at(-1).getBoundingClientRect().top < window.innerHeight) {
        active = sections.length - 1;
      }
      sectionLinks.forEach((link, index) => {
        if (index === active) link.setAttribute('aria-current', 'location');
        else link.removeAttribute('aria-current');
      });
      scrollPending = false;
    }
    function queueSectionUpdate() {
      if (scrollPending) return;
      scrollPending = true;
      requestAnimationFrame(updateSection);
    }
    window.addEventListener('scroll', queueSectionUpdate, { passive: true });
    window.addEventListener('resize', queueSectionUpdate);
    new ResizeObserver(queueSectionUpdate).observe($('#main'));
    updateSection();
  }

  $$('[data-share]').forEach(button => {
    button.hidden = false;
    button.addEventListener('click', async () => {
      const url = new URL('/', location.href).href;
      try {
        try {
          await navigator.clipboard.writeText(url);
        } catch {
          const field = document.createElement('textarea');
          field.value = url;
          field.readOnly = true;
          field.style.cssText = 'position:fixed;top:0;left:-9999px;';
          document.body.append(field);
          let copied;
          try {
            field.select();
            field.setSelectionRange(0, field.value.length);
            copied = document.execCommand('copy');
          } finally {
            field.remove();
            button.focus({ preventScroll: true });
          }
          if (!copied) throw new Error('Clipboard copy failed');
        }
        announce('링크가 복사되었습니다');
      } catch {
        announce('링크를 복사하지 못했습니다.');
      }
    });
  });

  const questions = $$('#faq-list .qa');
  const search = $('#faq-search');
  const expand = $('#faq-expand');
  function updateExpand() {
    const visible = questions.filter(question => !question.hidden);
    const allOpen = visible.length > 0 && visible.every(question => question.open);
    expand.setAttribute('aria-expanded', String(allOpen));
    expand.innerHTML = allOpen ? '모두 접기 <span aria-hidden="true">−</span>' : '모두 펼치기 <span aria-hidden="true">+</span>';
    expand.disabled = visible.length === 0;
  }
  function filterQuestions() {
    const term = search.value.toLocaleLowerCase('ko').trim();
    questions.forEach(question => {
      question.hidden = !question.textContent.toLocaleLowerCase('ko').includes(term);
    });
    const count = questions.filter(question => !question.hidden).length;
    $('#faq-count').textContent = term ? `검색 결과 ${count}개` : `질문 ${count}개`;
    $('#faq-empty').hidden = count !== 0;
    updateExpand();
  }
  if (questions.length) {
    $('.faq-toolbar').hidden = false;
    search.addEventListener('input', filterQuestions);
    expand.addEventListener('click', () => {
      const visible = questions.filter(question => !question.hidden);
      const shouldOpen = !visible.every(question => question.open);
      visible.forEach(question => { question.open = shouldOpen; });
      updateExpand();
    });
    questions.forEach(question => question.addEventListener('toggle', updateExpand));
    filterQuestions();
  }

  // Reveal a linked answer even when the current search hides it.
  function openFromHash() {
    let id;
    try { id = decodeURIComponent(location.hash.slice(1)); } catch { return; }
    const target = id && document.getElementById(id);
    if (!target) return;
    if (target.matches('details.qa')) {
      if (search) { search.value = ''; filterQuestions(); }
      target.open = true;
    }
    if (target.matches('details, .period')) target.scrollIntoView();
  }
  openFromHash();
  window.addEventListener('hashchange', openFromHash);
})();
