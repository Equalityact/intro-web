'use strict';
const { test }=require('node:test');const assert=require('node:assert/strict');const fs=require('node:fs');
const {parseManuscriptHtml,fetchDocumentHtml,documentUrl}=require('../lib/manuscript.cjs');
const {createHandler}=require('../api/manuscript');const known=require('../content/manuscript.json');
const html=fs.readFileSync(require('node:path').join(__dirname,'fixtures/manuscript.html'),'utf8');
const parse=text=>parseManuscriptHtml(text,known);
const source='https://docs.google.com/document/d/example/export?format=html';
function qnaEdited(text){return html.replace('<h1>5. 차별금지법 타임라인',text+'<h1>5. 차별금지법 타임라인');}
test('full manuscript has seven sections, nine questions, 23 scenes, 37 separate timeline links and eight resource URLs',()=>{
 const d=parse(html);assert.equal(Object.keys(d.pages).length,7);assert.equal(d.questions.length,9);assert.equal(d.periods.length,6);
 assert.equal(d.pages.scenes.blocks.flatMap(p=>p.children).length,23);
 assert.equal(d.periods.flatMap(p=>p.items.flatMap(i=>i.paragraph_links.flat())).length,37);assert.equal(d.resources.length,8);
 assert.deepEqual(d.resources.map(r=>r.url),known.resources.map(r=>r.url));
});
test('question additions, multiline answers, link labels, entity decoding, deletion and reordering follow document order',()=>{
 const edited=qnaEdited('<h2>새 질문 &amp; 확인?</h2><p>첫 답변 <a href="https://example.com/?a=1&amp;b=2">출처</a></p><p>둘째 답변</p>');
 const d=parse(edited);assert.equal(d.questions.length,10);const q=d.questions.at(-1);assert.equal(q.question,'새 질문 & 확인?');assert.equal(q.paragraphs.length,2);assert.equal(q.paragraphs[0].links[0].url,'https://example.com/?a=1&b=2');
 const moved=edited.replace('<h2>새 질문 &amp; 확인?</h2><p>첫 답변 <a href="https://example.com/?a=1&amp;b=2">출처</a></p><p>둘째 답변</p>','').replace('<h1>4. 차별금지법에 관한 질문들</h1>','<h1>4. 차별금지법에 관한 질문들</h1><h2>새 질문 &amp; 확인?</h2><p>답변 수정</p>');
 const next=parse(moved);assert.equal(next.questions[0].id,q.id);assert.equal(next.questions[0].paragraphs[0].text,'답변 수정');
 assert.equal(parse(html).questions.length,9);
});
test('case explanations and safe links attach to the correct case without inventing comparison text',()=>{
 const marker='<h3>이주노동자라는 이유로 임금 차별을 겪지 않는 일터</h3>';
 const d=parse(html.replace(marker,marker+'<p>사례 설명입니다.</p><p>변화 설명 <a href="https://example.com">원문</a></p>'));
 const item=d.pages.scenes.blocks[0].children[1];assert.equal(item.paragraphs.length,2);assert.equal(item.paragraphs[1].links[0].text,'원문');assert.ok(item.before);
 const n=parse(html.replace(marker,'<h3>새로운 장면</h3><p>새 설명</p>')).pages.scenes.blocks[0].children[1];assert.equal(n.before,undefined);
});
test('timeline document metadata controls pale background, marker, period years and category',()=>{
 const marker='<h3>현재 2개의 법안이 국회 계류 중</h3>';
 const d=parse(html.replace(marker,marker+'<p>[색상: 핑크]</p><p>[분류: 입법]</p>'));
 const item=d.periods.at(-1).items[0];assert.equal(item.color,'pink');assert.equal(item.meta.kind,'입법');assert.ok(!item.paragraphs.some(p=>p.startsWith('[색상:')));
 assert.ok(d.periods[0].years);
});
test('main page settings can be appended without renumbering existing pages',()=>{
 const d=parse(html.replace('</body>','<h1>0. 메인페이지</h1><h2>사이트 이름</h2><p>변경된 이름</p><h2>메인 슬로건</h2><p>첫 줄<br>둘째 줄</p></body>'));
 assert.equal(d.pages.home.blocks[0].paragraphs[0].text,'변경된 이름');assert.equal(d.pages.home.blocks[1].paragraphs[0].text,'첫 줄\n둘째 줄');
});
test('unsafe links, duplicate questions and missing heading structures do not publish a partial manuscript',()=>{
 assert.throws(()=>parse(html.replace('https://example.invalid','javascript:alert(1)').replace('https://www.humanrights.go.kr/site/program/board/basicboard/view?menuid=001004002001&amp;boardtypeid=24&amp;boardid=555110','javascript:alert(1)')));
 assert.throws(()=>parse(qnaEdited('<h2>새 질문</h2>')));assert.throws(()=>parse('<html><body><p>로그인하세요</p></body></html>'));
 assert.throws(()=>parse(qnaEdited('<h2>교회에서 ‘동성애는 죄’라고 말만 해도 처벌받나요?</h2><p>답변</p>')));
});
test('only public Google Docs export and trusted redirects may be fetched',async()=>{
 assert.equal(documentUrl(source).hostname,'docs.google.com');for(const bad of ['https://example.com/export?format=html','http://docs.google.com/document/d/x/export?format=html','https://docs.google.com/document/d/x/edit'])assert.throws(()=>documentUrl(bad));
 const got=await fetchDocumentHtml(source,async()=>new Response(html,{headers:{'content-type':'text/html'}}));assert.equal(got,html);
 await assert.rejects(fetchDocumentHtml(source,async()=>new Response('',{status:302,headers:{location:'http://127.0.0.1/'}})));
 await assert.rejects(fetchDocumentHtml(source,async()=>new Response('',{status:401})));
 await assert.rejects(fetchDocumentHtml(source,async()=>new Response('x',{headers:{'content-type':'text/html','content-length':String(3*1024*1024)}})));
});
function response(){return {headers:{},setHeader(k,v){this.headers[k]=v;},end(body){this.body=body;}};}
test('API supports cacheable valid snapshots, HEAD, and no-store failures; write requests are refused',async()=>{
 const handler=createHandler({source:()=>source,fetchHtml:async()=>html});const res=response();await handler({method:'GET'},res);assert.equal(res.statusCode,200);assert.equal(JSON.parse(res.body).questions.length,9);assert.match(res.headers['Cache-Control'],/s-maxage=60/);
 const head=response();await handler({method:'HEAD'},head);assert.equal(head.body,undefined);
 const fail=response();await createHandler({source:()=>source,fetchHtml:async()=>'<html>Sign in</html>'})({method:'GET'},fail);assert.equal(fail.statusCode,503);assert.equal(fail.headers['Cache-Control'],'no-store');
 const write=response();await handler({method:'POST'},write);assert.equal(write.statusCode,405);
});
test('bullets, ordered lists, nested items and their source links remain structured',()=>{
 const d=parse(qnaEdited('<h2>목록 답변?</h2><ul><li>첫 항목 <a href="https://example.com">원문</a><ul><li>하위 항목</li></ul></li><li>둘째 항목</li></ul><ol start="3"><li>셋째 순서</li></ol><p>마지막 문단</p>'));
 const p=d.questions.at(-1).paragraphs;
 assert.deepEqual(p.map(item=>item.text),['첫 항목 원문','하위 항목','둘째 항목','셋째 순서','마지막 문단']);
 assert.equal(p[0].list.kind,'ul');assert.equal(p[1].list.depth,1);assert.equal(p[2].list.depth,0);assert.equal(p[3].list.kind,'ol');assert.equal(p[3].list.start,3);assert.equal(p[0].links[0].text,'원문');assert.equal(p[4].list,undefined);
});
