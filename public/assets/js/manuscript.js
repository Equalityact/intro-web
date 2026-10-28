(() => {
  'use strict';
  const $ = (selector, root = document) => root.querySelector(selector);
  const $$ = (selector, root = document) => [...root.querySelectorAll(selector)];
  const page = (location.pathname.split('/').pop() || 'index').replace(/\.html$/, '');
  const reduced = matchMedia('(prefers-reduced-motion: reduce)');
  let inFlight = false, previous = '', decoration = [];
  const normal = text => text.replace(/\s+/g, '');
  const elem = (tag, cls, text) => {
    const node = document.createElement(tag);
    if (cls) node.className = cls;
    if (text !== undefined) node.textContent = text;
    return node;
  };
  function safeUrl(raw) {
    const url = new URL(raw);
    if (!['http:', 'https:', 'mailto:'].includes(url.protocol) || url.username || url.password) throw new Error('Invalid link');
    return url.href;
  }
  function link(url, label, cls = '') {
    const node = elem('a', cls, label); node.href = safeUrl(url);
    if (!url.startsWith('mailto:')) { node.target = '_blank'; node.rel = 'noopener noreferrer'; }
    return node;
  }
  function addRuns(node, text, links = []) {
    let cursor = 0;
    links.forEach(item => {
      if (!Number.isInteger(item.start) || !Number.isInteger(item.end) || item.start < cursor || item.end > text.length || item.end <= item.start || text.slice(item.start, item.end) !== item.text) throw new Error('Invalid link offsets');
      node.append(document.createTextNode(text.slice(cursor, item.start)), link(item.url, item.text)); cursor = item.end;
    });
    node.append(document.createTextNode(text.slice(cursor)));
    return node;
  }
  const paragraph = (item, cls = '') => addRuns(elem('p', cls), item.text, item.links);
  function paras(node, items) {
    const stack=[];
    items.forEach(item=>{
      if (!item.list) { stack.length=0;node.append(paragraph(item));return; }
      const {kind,group,start}=item.list;
      if (!['ul','ol'].includes(kind))throw new Error('Invalid list');
      const depth=Math.min(Math.max(0,item.list.depth || 0),stack.length);
      stack.length=Math.min(stack.length,depth+1);
      if (!stack[depth] || stack[depth].group!==group || stack[depth].node.tagName.toLowerCase()!==kind) {
        const list=elem(kind,'document-list');if(kind==='ol' && Number.isInteger(start))list.start=start;
        const parent=depth>0?stack[depth-1]?.last:node;(parent || node).append(list);stack[depth]={node:list,group,last:null};
      }
      const li=addRuns(elem('li'),item.text,item.links);stack[depth].node.append(li);stack[depth].last=li;
    });
    return node;
  }
  function svgPath(viewBox, path, cls = '') {
    const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
    svg.setAttribute('viewBox', viewBox); svg.setAttribute('preserveAspectRatio', 'none'); svg.setAttribute('aria-hidden', 'true'); svg.setAttribute('focusable', 'false');
    if (cls) svg.setAttribute('class', cls);
    const shape = document.createElementNS(svg.namespaceURI, 'path'); shape.setAttribute('d', path); shape.setAttribute('pathLength', '1'); svg.append(shape); return svg;
  }
  function decorate(node, tag, text) {
    if (tag === 'h1' && !node.dataset.underlineTone) {
      const existing = node.querySelector('.reading-highlight');
      const match = existing?.className.match(/reading-highlight--(pink-soft|purple-soft|yellow-soft|pink|purple|yellow)(?:\s|$)/);
      if (match) node.dataset.underlineTone = match[1];
    }
    node.textContent = text;
    const choice = decoration.find(item => item.tags.includes(tag) && text.includes(item.phrase)) || (tag === 'h1' && node.dataset.underlineTone ? { phrase: text, tone: node.dataset.underlineTone } : null);
    if (choice) {
      const at = text.indexOf(choice.phrase); const tone = ['yellow', 'purple', 'pink-soft', 'purple-soft', 'yellow-soft'].includes(choice.tone) ? choice.tone : 'pink';
      const mark = elem('span', `reading-highlight reading-highlight--${tone} reading-highlight--straight`, choice.phrase); mark.setAttribute('data-underline', '');
      node.replaceChildren(document.createTextNode(text.slice(0, at)), mark, document.createTextNode(text.slice(at + choice.phrase.length)));
    }
    if (/^h[123]$/.test(tag) && text.includes('사회적 합의') && text.includes('아직')) {
      const at = text.indexOf('아직'); const circle = elem('span', 'pen-circle', '아직'); circle.setAttribute('data-circle', '');
      circle.append(svgPath('0 0 120 64', 'M 103 13 C 76 -2 19 2 9 25 C -3 52 39 64 83 56 C 118 50 127 21 102 12 C 91 8 79 7 71 8'));
      node.replaceChildren(document.createTextNode(text.slice(0, at)), circle, document.createTextNode(text.slice(at + 2)));
    }
    return node;
  }
  function heading(tag, text, cls = '', id) { const node = decorate(elem(tag, cls, text), tag, text); if (id) node.id = id; return node; }
  function effects(root) {
    if (reduced.matches || !('IntersectionObserver' in window)) return;
    const observer = new IntersectionObserver(entries => entries.forEach(entry => {
      if (!entry.isIntersecting) return;
      const node = entry.target;
      node.classList.add(node.hasAttribute('data-circle') ? 'circle-visible' : 'underline-visible'); observer.unobserve(node);
    }), { threshold: .4 });
    $$('[data-underline], [data-circle]', root).forEach(node => {
      if (node.classList.contains('underline-ready') || node.classList.contains('circle-ready')) return;
      node.classList.add(node.hasAttribute('data-circle') ? 'circle-ready' : 'underline-ready'); observer.observe(node);
    });
  }
  function toc(items, host = $('.page-toc')) {
    if (!host || !items.length) return;
    const fragment = document.createDocumentFragment();
    items.forEach(item => { const li = elem('li'); const a = elem('a', '', item.title); a.href = `#${item.id}`; li.append(a); fragment.append(li); });
    host.replaceChildren(fragment);
  }
  function grounds(items) {
    const list = elem('ul', 'grounds');
    const tones = ['yellow-soft','pink','purple-soft','yellow','purple','pink-soft'];
    items.forEach((text,index) => {
      const shape = text.length <= 4 && index % 3 === 0 ? 'triangle' : text.length <= 8 && index % 2 ? 'circle' : 'square';
      const li = elem('li', `ground ground--${shape} ground--${tones[(index * 7 + Math.floor(index / 3)) % 6]}${text.length > 8 ? ' ground--long' : text.length > 4 ? ' ground--medium' : ''}`);
      li.append(elem('span', '', text)); list.append(li);
    });
    return list;
  }
  function about(data) {
    const host = $('[data-doc-about] .wrap'); if (!host) return;
    const fragment = document.createDocumentFragment();
    data.blocks.forEach((block,index) => {
      const article = elem('article', 'block'); article.id = block.id;
      const head = elem('div', 'block-head'); const num = elem('span', 'num', String(index+1).padStart(2,'0')); num.setAttribute('aria-hidden','true');
      head.append(num,heading('h2',block.title)); const body = elem('div','block-body');
      if (block.id === 'grounds' && block.paragraphs.length >= 3) {
        const listed = block.paragraphs.filter(item=>item.list);
        if (listed.length) {
          const first=block.paragraphs.indexOf(listed[0]),last=block.paragraphs.indexOf(listed.at(-1));
          paras(body,block.paragraphs.slice(0,first));body.append(grounds(listed.map(item=>item.text)));paras(body,block.paragraphs.slice(last+1));
        } else {
          body.append(paragraph(block.paragraphs[0]), grounds(block.paragraphs[1].text.split(/,\s*/).filter(Boolean)));
          paras(body,block.paragraphs.slice(2));
        }
      } else if(block.id === 'areas' && block.paragraphs.length > 1) {
        body.append(paragraph(block.paragraphs[0])); const list = elem('ul','area-list visual');
        block.paragraphs.slice(1).forEach(p => { const li = elem('li'); const match = p.text.match(/^(.+?)\s*:\s*(.+)\s+\(([^)]+)\)$/);
          if(match) li.append(elem('b','',match[1]),elem('span','area-description',match[2]),elem('span','tag',match[3])); else li.append(paragraph(p)); list.append(li); }); body.append(list);
      } else paras(body,block.paragraphs);
      article.append(head,body); fragment.append(article);
    }); host.replaceChildren(fragment); toc(data.blocks);
  }
  function scenes(data) {
    const host = $('[data-doc-scenes]'), selector = $('.scene-selector'); if(!host || !selector) return;
    const fragment = document.createDocumentFragment(), tabs = document.createDocumentFragment();
    const current = $('[aria-selected="true"]',selector)?.getAttribute('aria-controls');
    data.blocks.forEach((area,index) => {
      const tab = elem('button','',area.title);tab.type='button';tab.id=`tab-${area.id}`;tab.setAttribute('role','tab');tab.setAttribute('aria-controls',area.id);tab.setAttribute('aria-selected','false');tab.tabIndex=-1;tabs.append(tab);
      const panel = elem('section','scene-panel');panel.id=area.id;panel.setAttribute('aria-labelledby',`${area.id}-title`);panel.append(heading('h3',area.title,'scene-area-title',`${area.id}-title`));paras(panel,area.paragraphs);
      area.children.forEach((item,at) => {
        const article = elem('article','scene-comparison'); const id=`compare-${area.id}-${at+1}`;article.setAttribute('aria-labelledby',id);
        const grid=elem('div',`comparison-grid${item.before ? '' : ' comparison-grid--single'}`);
        if(item.before)grid.append(paras(elem('div','comparison-box'),[{text:item.before,links:[]}]),elem('span','comparison-arrow','→'));
        const after=elem('div','comparison-box after');const title=elem('p','',item.title);title.id=id;after.append(title);grid.append(after);article.append(grid);
        if(item.paragraphs.length)article.append(paras(elem('div','scene-case-copy reading'),item.paragraphs));panel.append(article);
      });fragment.append(panel);
    });host.replaceChildren(fragment);selector.replaceChildren(tabs);toc(data.blocks);
    document.dispatchEvent(new CustomEvent('manuscript:scenes',{detail:{selected:current}}));
  }
  function sliced(item, start, end) {
    return { text: item.text.slice(start, end).trim(), links: item.links.filter(link => link.start >= start && link.end <= end).map(link => {
      const leading = item.text.slice(start, end).length - item.text.slice(start, end).trimStart().length;
      return { ...link, start: link.start - start - leading, end: link.end - start - leading };
    }) };
  }
  function whyParagraphs(host, block) {
    let pending=[];
    const flush=()=>{if(pending.length){paras(host,pending);pending=[];}};
    block.paragraphs.forEach(item => {
      if(item.list){pending.push(item);return;}
      flush();
      if (block.id === 'global' && item.text.startsWith('여러분은 어떻게 생각하세요?')) {
        const callout = elem('div','callout section-content');
        const at = item.text.indexOf('시민들은');
        if (at > 0) { callout.append(heading('h3',item.text.slice(0,at).trim(),'callout-title'),paragraph(sliced(item,at,item.text.length))); }
        else callout.append(paragraph(item));
        host.append(callout); return;
      }
      const title = block.callout?.title, body = block.callout?.body;
      const start = title ? item.text.indexOf(title) : -1;
      const endStart = body ? item.text.indexOf(body,Math.max(0,start)) : -1;
      if (start >= 0 && endStart >= 0) {
        if (start) host.append(paragraph(sliced(item,0,start)));
        const callout=elem('div','callout purple visual');callout.append(elem('strong','',title),paragraph(sliced(item,endStart,endStart+body.length)));host.append(callout);
        if (endStart+body.length<item.text.length)host.append(paragraph(sliced(item,endStart+body.length,item.text.length)));
      } else host.append(paragraph(item));
    });
    flush();
  }
  function why(data) {
    const oldSections=$$('#main > section.section'); if(!oldSections.length)return;
    const surveys=$('.stat-hero .survey')?.cloneNode(true), recommendations=$('.recommendations')?.cloneNode(true);
    const fragment=document.createDocumentFragment();
    data.blocks.forEach((block,index)=>{
      const section=elem('section',`section${index===1?' soft':''}`);section.id=block.id;const id=`${block.id}-title`;section.setAttribute('aria-labelledby',id);
      const global = block.id === 'global';
      const wrap=elem('div','wrap'), grid=elem('div',global?'stat-hero editorial-columns':index===0?'stat-hero':'block'), left=elem('div',global?'editorial-title':index===0?'':'block-head'), right=elem('div',global||index===0?'reading':'block-body reading');
      const eyebrow=elem('p','eyebrow');eyebrow.append(elem('b','',String(index+1).padStart(2,'0')));if(block.label)eyebrow.append(document.createTextNode(block.label));
      const title=heading('h2',block.title,'section-title',id);
      if(global){
        // Keep the count card inside the left content cell, never as an auto-placed grid item.
        const content=elem('div','editorial-content');content.append(title);if(recommendations)content.append(recommendations);
        left.append(eyebrow,content);whyParagraphs(right,block);grid.append(left,right);
      } else if(index===0){left.append(eyebrow,title);paras(left,block.paragraphs);grid.append(left,surveys || right);}
      else {left.append(eyebrow,title);whyParagraphs(right,block);grid.append(left,right);}
      wrap.append(grid);section.append(wrap);fragment.append(section);
    });
    oldSections[0].before(fragment);oldSections.forEach(section=>section.remove());toc(data.blocks);
  }
  function questions(items, home = false) {
    const host=home?$('.qa-list-simple'):$('#faq-list');if(!host)return;
    const opened=new Set($$('details[open]',host).map(node=>node.dataset.question || $('.q-title',node)?.textContent));
    const fragment=document.createDocumentFragment();
    (home?items.slice(0,4):items).forEach((item,index)=>{
      const detail=elem('details','qa');detail.id=item.id;detail.dataset.question=item.question;detail.open=opened.has(item.question);
      const summary=elem('summary');const copy=elem('span','q-copy');copy.append(elem('span','q-title',item.question));
      if(!home){const first=item.paragraphs[0].text;const end=first.search(/[.!?。]\s/);copy.append(elem('span','q-preview',end>=0?first.slice(0,end+1):first));}
      const num=elem('span','q-number',`Q${index+1}`),toggle=elem('span','q-toggle');num.setAttribute('aria-hidden','true');toggle.setAttribute('aria-hidden','true');summary.append(num,copy,toggle);
      const answer=elem('div','q-detail');answer.append(elem('p','detail-label','자세한 답변'));paras(answer,item.paragraphs);detail.append(summary,answer);fragment.append(detail);
    });host.replaceChildren(fragment);document.dispatchEvent(new Event('manuscript:questions'));
  }
  function timeline(periods) {
    const host=$('[data-timeline]');if(!host)return;
    const fragment=document.createDocumentFragment();
    periods.forEach((period,index)=>{
      const section=elem('section','period');section.id=period.id;section.setAttribute('aria-labelledby',`${period.id}-title`);const head=elem('div','period-head');
      head.append(elem('span','period-number',String(index+1).padStart(2,'0')),heading('h2',period.title,'',`${period.id}-title`));if(period.years)head.append(elem('span','years',period.years));
      const list=elem('ol','timeline');period.items.forEach(item=>{
        const row=elem('li',`timeline-item${item.color?' timeline-color-'+item.color:''}`),card=elem('article','timeline-card'),meta=elem('div','timeline-meta');
        for(const key of ['date','actor','kind'])if(item.meta?.[key])meta.append(elem('span',`timeline-${key}`,item.meta[key]));
        const prefix=item.meta?.actor&&item.meta?.date?`${item.meta.actor}(${item.meta.date}) - `:'';
        card.append(meta,heading('h3',prefix&&item.title.startsWith(prefix)?item.title.slice(prefix.length):item.title));
        paras(card,item.paragraphs.map((text,i)=>({text,links:item.paragraph_links[i],list:item.paragraph_lists?.[i]})));row.append(card);list.append(row);
      });section.append(head,list);fragment.append(section);
    });host.replaceChildren(fragment);toc(periods);
  }
  function resources(items) {
    const host=$('[data-doc-resources]');if(!host)return;const fragment=document.createDocumentFragment();
    items.forEach(item=>{const li=elem('li','resource');li.append(heading('h2',item.title),elem('p','by',item.by));paras(li,item.paragraphs);const button=link(item.url,'자료 보기 ','btn purple small');button.append(elem('span','arrow','↗'));li.append(button);fragment.append(li);});host.replaceChildren(fragment);
  }
  function information(items) {
    const body=$('.info-table tbody');if(body){const fragment=document.createDocumentFragment();items.forEach(item=>{const row=elem('tr'),label=elem('th','',item.label),cell=elem('td');label.scope='row';
      if(!item.paragraph.links.length && item.label==='이메일' && /^[^\s@]+@[^\s@]+$/.test(item.paragraph.text))cell.append(link(`mailto:${item.paragraph.text}`,item.paragraph.text,'info-link'));
      else {addRuns(cell,item.paragraph.text,item.paragraph.links);$$('a',cell).forEach(a=>a.className='info-link');}row.append(label,cell);fragment.append(row);});body.replaceChildren(fragment);}
    const footer=$('.footer-info');if(footer){const fragment=document.createDocumentFragment();items.filter(item=>['제작','홈페이지','SNS','이메일','후원 계좌'].includes(item.label)).forEach(item=>{const dt=elem('dt','',item.label),dd=elem('dd');addRuns(dd,item.paragraph.text,item.paragraph.links);if(item.label==='이메일'&&!item.paragraph.links.length){dd.replaceChildren(link(`mailto:${item.paragraph.text}`,item.paragraph.text));}fragment.append(dt,dd);});footer.replaceChildren(fragment);}
    const rows=new Map(items.map(item=>[item.label,item.paragraph]));
    for(const [selector,label] of [['[data-share] + a','후원 계좌'],['.join-path:nth-child(2) a','뉴스레터 구독하기'],['.join-path:nth-child(3) a','후원 계좌']]) {
      // The leaflet form is a separate main-page setting, never the donation URL.
      if(selector.startsWith('[data-share]'))continue;
      const url=rows.get(label)?.links[0]?.url;if(url) $$(selector).forEach(a=>a.href=safeUrl(url));
    }
  }
  const HOME_FIELDS={
    '사이트 이름':'name','메인 슬로건':'slogan','메인 소개':'description','요약 섹션 제목':'summary_title','법안 이름 안내':'summary_note','히어로 카드 문구':'grounds_title',
    '통계 제목':'stats_title','찬성 비율':'support_value','찬성 설명 제목':'support_title','찬성 설명':'support_caption','정책 과제 제목':'policy_title','정책 과제 설명':'policy_caption',
    '국제사회 권고 횟수':'recommendation_value','국제사회 권고 제목':'recommendation_title','국제사회 권고 설명':'recommendation_caption','질문 섹션 제목':'questions_title',
    '함께하기 제목':'join_title','공유 안내':'share','리플렛 버튼':'leaflet','뉴스레터 안내':'newsletter_question','뉴스레터 설명':'newsletter','뉴스레터 버튼':'newsletter_button','후원 안내':'donate','출처 표시':'source_label'
  };
  function mainPage(data) {
    if(!data)return;
    const fields={};data.blocks.forEach(block=>{if(HOME_FIELDS[block.title])fields[HOME_FIELDS[block.title]]=block.paragraphs.map(p=>p.text).join('\n');});
    for(const [key,text] of Object.entries(fields)) {
      $$(`[data-home-field="${key}"]`).forEach(node=>{
        node.dataset.manuscriptText=text;
        if (node.dataset.heroCaptionManaged === 'true') {
          node.dispatchEvent(new CustomEvent('hero:caption', { detail: { text } }));
          return;
        }
        if(key==='recommendation_value'){const match=text.match(/^(\d+)(.*)$/);if(match){node.replaceChildren(document.createTextNode(match[1]),elem('small','',match[2]));return;}}
        decorate(node,node.tagName.toLowerCase(),text);
      });
    }
    if(fields.name){$$('.wordmark > span,.footer-name').forEach(node=>node.textContent=fields.name);const title=$('.page-hero h1')?.textContent;document.title=page==='index'?fields.name:`${title} · ${fields.name}`;}
    if(fields.slogan && $('#hero-title')) {
      const lines=fields.slogan.split('\n').filter(Boolean);const node=$('#hero-title'),fragment=document.createDocumentFragment();
      lines.forEach((line,index)=>{const span=elem('span','hero-title-line');if(index===lines.length-1){const mark=elem('mark','reading-highlight reading-highlight--pink',line);mark.setAttribute('data-underline','');mark.append(svgPath('0 0 300 14','M 2 8 C 22 -1 38 17 57 8 S 91 -1 111 8 S 145 17 166 8 S 201 -1 222 8 S 262 17 298 5'));span.append(mark);}else span.textContent=line;fragment.append(span,document.createTextNode(' '));});node.replaceChildren(fragment);
    }
    const pillars=data.blocks.find(block=>block.title==='메인 카드');
    if(pillars && $('.pillars')){const fragment=document.createDocumentFragment();pillars.children.forEach((item,index)=>{const article=elem('article','pillar');article.append(elem('div','role',String(index+1).padStart(2,'0')),heading('h3',item.title));paras(article,item.paragraphs);fragment.append(article);});$('.pillars').replaceChildren(fragment);}
    const surveys=data.blocks.find(block=>block.title==='여론조사');
    if(surveys && $('.home-survey')) {
      const host=$('.home-survey'),fragment=document.createDocumentFragment();fragment.append(heading('h3',fields.source_label||'출처'));
      surveys.children.forEach(item=>{const row=elem('div','rate-row'),source=item.paragraphs.find(p=>p.links.length),date=item.paragraphs.find(p=>!p.links.length&&!/^(찬성한다|잘 모르겠다|반대한다)\s+\d/.test(p.text));
        const values=['찬성한다','잘 모르겠다','반대한다'].map(label=>{const p=item.paragraphs.find(p=>p.text.startsWith(label+' '));const value=Number(p?.text.match(/(\d+(?:\.\d+)?)%/)?.[1]);if(!Number.isFinite(value)||value<0||value>100)throw new Error('Invalid survey value');return value;});if(values.reduce((a,b)=>a+b,0)>100.5)throw new Error('Invalid survey total');
        const label=elem('div','rate-label');label.append(source?link(source.links[0].url,item.title):elem('span','',item.title));row.append(label);if(date)row.append(paragraph(date,'rate-source'));
        const track=elem('div','survey-track'),legend=elem('ul','survey-legend');track.setAttribute('aria-hidden','true');values.forEach((value,index)=>{const seg=elem('span',`survey-segment response-${index}`);seg.style.width=`${value}%`;track.append(seg);const li=elem('li'),key=elem('span',`survey-key response-${index}`);key.setAttribute('aria-hidden','true');li.append(key,document.createTextNode(['찬성한다','잘 모르겠다','반대한다'][index]+' '),elem('strong','',`${value}%`));legend.append(li);});row.append(track,legend);fragment.append(row);
      });host.replaceChildren(fragment);
    }
    const leaflet=data.blocks.find(block=>block.title==='리플렛 신청 링크')?.paragraphs.find(p=>p.links.length)?.links[0]?.url;
    if(leaflet){const a=$('.join-path:first-child a');if(a)a.href=safeUrl(leaflet);}
    if(fields.recommendation_value){const count=Number(fields.recommendation_value.match(/^\d+/)?.[0]);if(Number.isInteger(count)&&count>=0&&count<=100)$$('.dots').forEach(host=>{const f=document.createDocumentFragment();for(let i=0;i<count;i++)f.append(elem('span'));host.replaceChildren(f);});}
  }
  function validate(data) {
    if(data.version!==1 || !data.pages || !Array.isArray(data.questions) || !data.questions.length || !Array.isArray(data.periods) || !Array.isArray(data.resources) || !Array.isArray(data.info))throw new Error('Invalid manuscript');
    let count=0;
    function walk(value) {
      if(++count>40000)throw new Error('Excessive data');
      if(typeof value==='string' && value.length>100000)throw new Error('Excessive text');
      if(value&&typeof value==='object'){
        if(value.url)safeUrl(value.url);
        if(value.id && !/^[a-z][a-z0-9-]*$/.test(value.id))throw new Error('Invalid ID');
        if(value.links){const probe=elem('p');addRuns(probe,value.text,value.links);}
        Object.values(value).forEach(walk);
      }
    }walk(data);
    for(const key of ['about','scenes','why','qna','timeline','resources','info'])if(!data.pages[key])throw new Error('Missing page');
  }
  function apply(data) {
    validate(data);decoration=data.emphasis||[];
    const current=data.pages[page];
    if(current){const title=$('.page-hero h1');if(title)decorate(title,'h1',current.title);if(current.intro.length && page!=='info'){const lead=$('.page-hero .lead');if(lead){lead.replaceChildren();current.intro.forEach((item,index)=>{if(index)lead.append(document.createElement('br'));addRuns(lead,item.text,item.links);});}}}
    if(page==='about')about(current);else if(page==='scenes')scenes(current);else if(page==='why')why(current);else if(page==='qna')questions(data.questions);else if(page==='timeline')timeline(data.periods);else if(page==='resources')resources(data.resources);
    if(page==='index') {
      questions(data.questions,true);
      const host=$('.scene-grid');if(host){const fragment=document.createDocumentFragment();data.pages.scenes.blocks.forEach((item,index)=>{const a=elem('a','scene-card');a.href=`scenes.html#${item.id}`;const top=elem('div','scene-top');top.append(elem('span','scene-index',String(index+1).padStart(2,'0')),elem('span','scene-glyph',['[ ]','?','↔','='][index%4]));a.append(top,heading('h3',item.title),elem('span','scene-link','더 알아보기 →'));fragment.append(a);});host.replaceChildren(fragment);const title=$('#scenes-title');if(title)decorate(title,'h2',data.pages.scenes.title);}
    }
    information(data.info);mainPage(data.pages.home);effects(document);
  }
  async function refresh() {
    if(inFlight||document.hidden)return;
    // Never replace an answer, selected text, or focused control while someone reads it.
    if(previous && (window.getSelection()?.toString() || document.activeElement?.closest('#main,.site-footer') || $('#faq-list details[open],.qa-list-simple details[open]')))return;
    inFlight=true;const controller=new AbortController(),timeout=setTimeout(()=>controller.abort(),15000);
    try{const response=await fetch('/api/manuscript',{signal:controller.signal});if(!response.ok)return;const data=await response.json();const fingerprint=JSON.stringify(data);if(fingerprint===previous)return;
      // Validate the full snapshot before changing the currently displayed manuscript.
      validate(data);
      const oldY=window.scrollY;const activeId=document.activeElement?.id;let hash='';try{hash=decodeURIComponent(location.hash.slice(1));}catch{}
      apply(data);previous=fingerprint;
      if(hash){const target=document.getElementById(hash);if(target){if(target.matches('details'))target.open=true;target.scrollIntoView();}}
      else {const behavior=document.documentElement.style.scrollBehavior;document.documentElement.style.scrollBehavior='auto';window.scrollTo(0,oldY);document.documentElement.style.scrollBehavior=behavior;}
      if(activeId)document.getElementById(activeId)?.focus({preventScroll:true});
    }catch{/* Keep the generated manuscript or last good snapshot if the document is unavailable. */}
    finally{clearTimeout(timeout);inFlight=false;}
  }
  refresh();setInterval(refresh,60000);document.addEventListener('visibilitychange',refresh);
})();
