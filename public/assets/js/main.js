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

  $$('[data-share]').forEach(button => {
    button.hidden = false;
    button.addEventListener('click', async () => {
      const url = new URL('/', location.href).href;
      try {
        if (navigator.share) {
          await navigator.share({ title: '차별금지법', text: '차별금지법, 모두를 위한 평등의 기준', url });
        } else {
          await navigator.clipboard.writeText(url);
          announce('사이트 링크를 복사했습니다.');
        }
      } catch (error) {
        if (error.name !== 'AbortError') announce('주소창의 링크를 복사해 공유해 주세요.');
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

  const sceneButtons = $$('[data-scene]');
  const scenePanels = $$('[data-scene-panel]');
  if (sceneButtons.length) {
    function showScene(selected) {
      sceneButtons.forEach(button => button.setAttribute('aria-pressed', String(button.dataset.scene === selected)));
      scenePanels.forEach(panel => { panel.hidden = panel.dataset.scenePanel !== selected; });
    }
    $('.scene-selector').hidden = false;
    showScene(sceneButtons[0].dataset.scene);
    sceneButtons.forEach(button => button.addEventListener('click', () => showScene(button.dataset.scene)));
  }

  const timelineButtons = $$('[data-timeline]');
  function filterTimeline(kind) {
    let count = 0;
    timelineButtons.forEach(button => button.setAttribute('aria-pressed', String(button.dataset.timeline === kind)));
    $$('.period').forEach(period => {
      const items = $$('.timeline-item', period);
      items.forEach(item => {
        item.hidden = kind !== 'all' && item.dataset.kind !== kind;
        if (!item.hidden) count++;
      });
      period.hidden = items.every(item => item.hidden);
    });
    $('#timeline-count').textContent = `사건 ${count}개`;
  }
  if (timelineButtons.length) {
    $('#timeline-filters').hidden = false;
    timelineButtons.forEach(button => button.addEventListener('click', () => filterTimeline(button.dataset.timeline)));
  }

  // A direct question/period link must remain reachable after a search or filter.
  function openFromHash() {
    let id;
    try { id = decodeURIComponent(location.hash.slice(1)); } catch { return; }
    const target = id && document.getElementById(id);
    if (!target) return;
    if (target.matches('#faq-list .qa')) {
      search.value = '';
      filterQuestions();
      target.open = true;
    }
    if (target.matches('.period') && target.hidden) filterTimeline('all');
    if (target.matches('details, .period')) target.scrollIntoView();
  }
  openFromHash();
  window.addEventListener('hashchange', openFromHash);
  $$('.page-toc a').forEach(link => link.addEventListener('click', () => {
    if (timelineButtons.length) filterTimeline('all');
  }));
})();
