(() => {
  'use strict';
  const $ = (s, root = document) => root.querySelector(s);
  const $$ = (s, root = document) => Array.from(root.querySelectorAll(s));

  // Toast
  const toast = $('#toast');
  let toastTimer;
  function announce(text) {
    if (!toast) return;
    toast.textContent = text;
    toast.classList.add('show');
    clearTimeout(toastTimer);
    toastTimer = setTimeout(() => toast.classList.remove('show'), 2600);
  }

  // Mobile menu
  const menuButton = $('.menu-toggle');
  const gnb = $('#gnb');
  if (menuButton && gnb) {
    const setOpen = open => {
      gnb.classList.toggle('open', open);
      menuButton.setAttribute('aria-expanded', String(open));
      menuButton.textContent = open ? '메뉴 닫기' : '메뉴 열기';
    };
    menuButton.addEventListener('click', () => setOpen(!gnb.classList.contains('open')));
    document.addEventListener('keydown', e => { if (e.key === 'Escape') setOpen(false); });
    $$('a', gnb).forEach(a => a.addEventListener('click', () => setOpen(false)));
  }

  // Share site link
  $$('[data-share]').forEach(button => button.addEventListener('click', async () => {
    const url = new URL('/', location.href).href;
    const data = { title: '차별금지법', text: '차별금지법, 모두를 위한 평등의 기준', url };
    try {
      if (navigator.share) { await navigator.share(data); return; }
      await navigator.clipboard.writeText(url);
      announce('사이트 링크를 복사했습니다.');
    } catch (err) {
      if (err && err.name === 'AbortError') return;
      announce('링크를 복사하지 못했습니다. 주소창의 링크를 복사해 주세요.');
    }
  }));

  // Newsletter form (스티비 연동 전 초안)
  const subscribe = $('#subscribe-form');
  if (subscribe) {
    subscribe.addEventListener('submit', e => {
      e.preventDefault();
      const email = $('#sub-email', subscribe);
      const error = $('#sub-email-error', subscribe);
      const valid = email.value.trim() !== '' && email.checkValidity();
      email.setAttribute('aria-invalid', String(!valid));
      error.hidden = valid;
      if (!valid) { email.focus(); return; }
      const required = $$('input[type=checkbox][required]', subscribe);
      if (required.some(c => !c.checked)) { announce('필수 동의 항목을 확인해 주세요.'); return; }
      announce('구독 폼 연동 전 초안입니다. 스티비 구독 페이지를 엽니다.');
      window.open(subscribe.action, '_blank', 'noopener');
    });
  }

  // FAQ: search, expand all, open from hash
  const questions = $$('#faq-list .qa');
  const search = $('#faq-search');
  const expand = $('#faq-expand');
  const count = $('#faq-count');
  const empty = $('#faq-empty');
  function updateExpand() {
    if (!expand) return;
    const visible = questions.filter(q => !q.hidden);
    const allOpen = visible.length > 0 && visible.every(q => q.open);
    expand.setAttribute('aria-expanded', String(allOpen));
    expand.innerHTML = allOpen ? '모두 접기 <span aria-hidden="true">−</span>' : '모두 펼치기 <span aria-hidden="true">+</span>';
    expand.disabled = visible.length === 0;
  }
  if (search) {
    search.addEventListener('input', () => {
      const term = search.value.toLocaleLowerCase().trim();
      let n = 0;
      questions.forEach(q => {
        q.hidden = !q.textContent.toLocaleLowerCase().includes(term);
        if (!q.hidden) n++;
      });
      count.textContent = term ? `검색 결과 ${n}개` : `질문 ${n}개`;
      empty.hidden = n !== 0;
      updateExpand();
    });
  }
  if (expand) {
    expand.addEventListener('click', () => {
      const visible = questions.filter(q => !q.hidden);
      const shouldOpen = !visible.every(q => q.open);
      visible.forEach(q => { q.open = shouldOpen; });
      updateExpand();
    });
    questions.forEach(q => q.addEventListener('toggle', updateExpand));
  }
  function openFromHash() {
    const target = location.hash && document.getElementById(location.hash.slice(1));
    if (target && target.tagName === 'DETAILS') { target.open = true; target.scrollIntoView(); }
  }
  openFromHash();
  window.addEventListener('hashchange', openFromHash);
})();
